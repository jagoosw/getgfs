"""gfspy - A library that extracts information from the NOAA GFS forecast without using .grb2 files

TODO
----
- Could add historic fetching from https://www.ncei.noaa.gov/thredds/dodsC/model-gfs-004-files-old/202003/20200328/gfs_4_20200328_1800_384.grb2.das
    - Possibly beneficial for historical analysis since it should mean you don't have to download the whole shibang
- Add export to .nc file with netcdf4 (maybe an optional dependancy)
- Add shortcuts like wind, alts="all" would also include the surface wind component (since min alt wind is ~40m)
- Add purge missing/unreliable
"""
import requests, json, os, re, dateutil.parser, sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
from decode import *

try:
    from fuzzywuzzy import fuzz
except:
    pass

__copyright__ = """
    gfspy - A library that extracts information from the NOAA GFS forecast without using .grb2 files
    Copyright (C) 2021 Jago Strong-Wright

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>."""

route = os.path.abspath(os.path.dirname(__file__))

url = "https://nomads.ncep.noaa.gov/dods/gfs_{res}{step}/gfs{date}/gfs_{res}{step}_{hour:02d}z.{info}"
config_file = "%s/config.json" % route
attribute_file = "%s/atts/{res}{step}.json" % route

if not os.path.isdir("%s/atts" % route):
    os.makedirs("%s/atts" % route)
if not os.path.isfile(config_file):
    with open(config_file, "w+") as f:
        json.dump({"saved_atts": ["Na"]}, f)


class Forcast:
    def __init__(self, resolution="0p25", timestep=""):
        if timestep != "":
            timestep = "_" + timestep
        self.resolution = resolution
        self.timestep = timestep
        self.times, self.coords, self.variables = get_attributes(resolution, timestep)

    def get(self, variables, date_time, lat, lon):
        """Returns the latest forcast available for the requested date and time

        Note:
        ----
        - "raw" since you have to put indexes in rather than coordinates and it returns a file object rather than a processed file
        - If a variable has level dependance, you get all the levels - it seems extremely hard to impliment otherwise

        Args:
            variables (list): list of required variables by short name
            date_time (string): datetime requested
            lat (string or number): latitude in the format "[min:max]" or a single value
            lon (string or number): longitude in the format "[min:max]" or a single value
        """

        # Get forcast date run, date, time
        forcast_date,forcast_time,query_time=self.datetime_to_forcast(date_time)

        # Get latitude
        lat=self.value_input_to_index("lat",lat)

        # Get longitude
        lon=self.value_input_to_index("lon",lon)

        # Get lev
        lev = "[0:%s]" % int(
            (self.coords["lev"]["minimum"] - self.coords["lev"]["maximum"])
            / self.coords["lev"]["resolution"]
        )

        # Make query
        query = ""
        for variable in variables:
            if variable not in self.variables.keys():
                raise ValueError(
                    "The variable {name} is not a valid choice for this weather model".format(
                        name=variable
                    )
                )
            if self.variables[variable]["level_dependent"] == True and lev == []:
                raise ValueError(
                    "The variable {name} requires the altitude/level to be defined".format(
                        name=variable
                    )
                )
            elif self.variables[variable]["level_dependent"] == True:
                query += "," + variable + query_time + lev + lat + lon
            else:
                query += "," + variable + query_time + lat + lon

        query = query[1:]

        r = requests.get(
            url.format(
                res=self.resolution,
                step=self.timestep,
                date=forcast_date,
                hour=int(forcast_time),
                info="ascii?{query}".format(query=query),
            )
        )
        if r.status_code != 200:
            raise Exception(
                """The altitude pressure forcast information could not be downloaded. 
        This error should never occure but it may be helpful to know the requested information was:
        - Forcast date: {f_date}
        - Forcast time: {f_time}
        - Query time: {q_time}
        - Latitude: {lat}
        - Longitude: {lon}""".format(
                    f_date=forcast_date,
                    f_time=forcast_time,
                    q_time=query_time,
                    lat=lat,
                    lon=lon,
                )
            )

        return File(r.text)

    def datetime_to_forcast(self,date_time):
        earliest_available = hour_round(datetime.utcnow() - timedelta(days=7))
        latest_available = hour_round(
            datetime.utcnow()
            - timedelta(
                hours=datetime.utcnow().hour
                - 6 * (datetime.utcnow().hour // 6)
                - int(self.times["grads_size"]) * int(self.times["grads_step"][0]),
                minutes=datetime.utcnow().minute,
                seconds=datetime.utcnow().second,
                microseconds=datetime.utcnow().microsecond,
            )
        )
        desired_date = dateutil.parser.parse(date_time)
        latest_forcast = latest_available - timedelta(
            hours=int(self.times["grads_size"]) * int(self.times["grads_step"][0])
        )
        if earliest_available < desired_date < latest_available:
            query_forcast = latest_forcast
            while desired_date < query_forcast:
                query_forcast -= timedelta(hours=6)

            forcast_date = query_forcast.strftime("%Y%m%d")
            forcast_time = query_forcast.strftime("%H")

            query_time = "[{t_ind}]".format(
                t_ind=round(
                    (desired_date - query_forcast).seconds
                    / (int(self.times["grads_step"][0]) * 60 * 60)
                )
            )

        else:
            raise ValueError(
                "Datetime requested ({dt}) is not available the moment, usually only the last weeks worth of forcasts are available and this model only extends {hours} hours forward.\nThis error may be caused by an uninterpretable datetime format.".format(
                    hours=int(self.times["grads_size"])
                    * int(self.times["grads_step"][0]),
                    dt=dateutil.parser.parse(date_time),
                )
            )
        
        return forcast_date,forcast_time,query_time

    def value_input_to_index(self,coord,inpt):
        if isinstance(inpt, str):
            if inpt[0] == "[" and inpt[-1] == "]" and ":" in inpt:
                val_1 = float(re.findall(r"\[(.*?):", inpt))
                val_2 = float(re.findall(r"\:(.*?)]", inpt))
                val_min = self.value_to_index(coord, min(val_1, val_2))
                val_max = self.value_to_index(coord, max(val_1, val_2))
                ind = "[%s:%s]" % (val_min, val_max)
            else:
                try:
                    inpt=float(inpt)#isnumeric apparently doesn't work for floats
                except:
                    raise ValueError(
                        "The format of the %s variable was incorrect, it must either be a single number or a range in the format [min:max]. You entered '%s'"
                        % (coord, inpt)
                    )
                ind = "[%s]" % self.value_to_index(coord, inpt)
        else:
            ind = "[%s]" % self.value_to_index(coord, inpt)
        
        return ind


    def value_to_index(self, coord, value):
        possibles = [
            float(self.coords[coord]["resolution"]) * n
            + float(self.coords[coord]["minimum"])
            for n in range(0, int(self.coords[coord]["grads_size"]))
        ]
        closest=min(possibles, key=lambda x:abs(x-value))
        return possibles.index(closest)

    def search_names(self,variable,sensetivity=80):
        if 'fuzzywuzzy.fuzz' not in sys.modules:
            raise RuntimeError("You can not use search_name without fuzzywuzzy installed, please `pip install fuzzywuzzy`. Other functionality is still available")

        possibles=[]
        for var in self.variables.keys():
            if "long_name" in self.variables[var].keys():
                ln=fuzz.partial_ratio(self.variables[var]["long_name"],variable)
                sn=fuzz.partial_ratio(var,variable)
                if ln>sensetivity or sn>sensetivity:
                    possibles.append((var,self.variables[var]["long_name"],ln+sn))

        possibles=sorted(possibles, key=lambda tup: tup[2])
        return possibles

    def get_windprofile(self, date_time, lat, lon):
        info=self.get(["ugrdprs","vgrdprs","ugrd2pv","vgrd2pv","hgtsfc","hgtprs"],date_time,lat,lon)
        

        u_wind=list(info.variables["ugrdprs"].data.flatten())+list(info.variables["ugrd2pv"].data.flatten())
        v_wind=list(info.variables["vgrdprs"].data.flatten())+list(info.variables["vgrd2pv"].data.flatten())

        #at the altitudes we are concerned with the geopotential height and altitude are within 0.5km of eachother
        alts=list(info.variables["hgtprs"].data.flatten())+list(info.variables["hgtsfc"].data.flatten())

        return interp1d(alts,u_wind),interp1d(alts,v_wind)

def get_attributes(res, step):
    with open(config_file) as f:
        config = json.load(f)
    if "{res}{step}".format(res=res, step=step) not in config["saved_atts"]:
        if datetime.utcnow().hour < 6:
            date = datetime.utcnow() - timedelta(day=1)
        else:
            date = datetime.utcnow()
        r = requests.get(
            url.format(
                res=res,
                step=step,
                date=date.strftime("%Y%m%d"),
                hour=0,
                info="das",
            )
        )
        if r.status_code != 200:
            raise Exception("The forcast resolution and timestep was not found")
        search_text = re.sub("\s{2,}", "", r.text[12:-2])
        raws = re.findall(r"(.*?) \{(.*?)\}", search_text)
        variables = {}
        coords = {}
        for var in raws:
            attributes = {}
            atts = var[1].split(";")
            # Extraction from a line could be simplified to a function
            if var[0] not in ["time", "lat", "lon", "lev"]:
                for att in atts:
                    iden, val = extract_line(
                        ["_FillValue", "missing_value", "long_name"], att
                    )
                    if iden != None:
                        attributes[iden] = val
                variables[var[0]] = attributes
            elif var[0] == "time":
                for att in atts:
                    iden, val = extract_line(["grads_size", "grads_step"], att)
                    if iden != None:
                        attributes[iden] = val
                time = attributes
            else:
                for att in atts:
                    iden, val = extract_line(
                        ["grads_dim", "grads_size", "minimum", "maximum", "resolution"],
                        att,
                    )
                    if iden != None:
                        attributes[iden] = val
                coords[var[0]] = attributes

        r = requests.get(
            url.format(
                res=res,
                step=step,
                date=date.today().strftime("%Y%m%d"),
                hour=0,
                info="dds",
            )
        )
        if r.status_code != 200:
            raise RuntimeError("The forcast resolution and timestep was not found")
        arrays = re.findall(r"ARRAY:\n(.*?)\n", r.text)
        for array in arrays:
            var = re.findall(r"(.*?)\[", array)[0].split()[1]
            if var in variables.keys():
                lev_dep = False
                for dim in re.findall(r"(.*?)\[", array):
                    if dim.split()[0] == "lev":
                        lev_dep = True
                variables[var]["level_dependent"] = lev_dep

        save = {"time": time, "coords": coords, "variables": variables}
        with open(attribute_file.format(res=res, step=step), "w+") as f:
            json.dump(save, f)
        config["saved_atts"].append("{res}{step}".format(res=res, step=step))
        with open(config_file, "w+") as f:
            json.dump(config, f)
        return time, coords, variables
    else:
        with open(attribute_file.format(res=res, step=step)) as f:
            data = json.load(f)
        return data["time"], data["coords"], data["variables"]


def extract_line(possibles, line):
    found = -1
    ind = -1
    while found == -1 and ind < len(possibles) - 1:
        ind += 1
        found = line.find(possibles[ind])

    if found != -1:
        if line[0:3] == "Str":
            return possibles[ind], line[found + len(possibles[ind]) + 2 : -1]
        elif line[0:3] == "Flo":
            return possibles[ind], float(line[found + len(possibles[ind]) + 1 :])
    return None, None


def hour_round(t):
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + timedelta(
        hours=t.minute // 30
    )


if __name__ == "__main__":
    test = False

    f = Forcast("0p25", "1hr")
    #print(f.search_names("geopotential"))
    u,v=f.get_windprofile("20210226 17:00", "12.5", "6.3")
    print(u(1000))
    # print(f.value_to_index("lat", 0))
    if test == True:
        os.remove(config_file)
        import shutil

        shutil.rmtree("%s/atts" % route)
