"""gfspy - A library that extracts information from the NOAA GFS forecast without using .grb2 files

TODO
----
- Could add historic fetching from https://www.ncei.noaa.gov/thredds/dodsC/model-gfs-004-files-old/202003/20200328/gfs_4_20200328_1800_384.grb2.das
    - Possibly beneficial for historical analysis since it should mean you don't have to download the whole shibang
- Add export to .nc file with netcdf4 (maybe an optional dependancy)
"""
import requests, json, os, re, dateutil.parser
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

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
    def __init__(self, resolution, timestep=""):
        if timestep != "":
            timestep = "_" + timestep
        self.resolution = resolution
        self.timestep = timestep
        self.times, self.coords, self.variables = get_attributes(resolution, timestep)

    def get(self, variables, date_time, lat, lon, lev=[]):
        """Returns the latest forcast available for the requested date and time

        Args:
            variables (list): list of required variables by short name
            date_time (string): datetime requested
            lat (string): latitude in the format "[min_index:max_index]"
            lon ([type]): longitude in the format "[min_index:max_index]"
            z (list, optional): z level in the format "[min_index:max_index]". Defaults to [] meaning there is no level dependance.
        """

        if isinstance(lat,str):
            if lat[0]=="[" and lat[-1]=="]" and ":" in lat:
                #Extract 2 values
                #see which is bigger and smaller
                #convert to [:] format
            elif lat.isnumeric():
                lat="[%s]"%self.value_to_index("lat",float(lat))
            else:
                raise ValueError("The format of the latitude variable was incorrect, it must either be a single number or a range in the format [min:max]. You entered '%s'"%lat)


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
            forcast_time = query_forcast.strftime("_%Hz")

            query_time = "[{t_ind}]".format(
                t_ind=round(
                    (desired_date - query_forcast).seconds
                    / (int(self.times["grads_step"][0]) * 60 * 60)
                )
            )
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
            print(query)

        else:
            raise ValueError(
                "Datetime requested ({dt}) is not available the moment, usually only the last weeks worth of forcasts are available and this model only extends {hours} hours forward.\nThis error may be caused by an uninterpretable datetime format.".format(
                    hours=int(self.times["grads_size"])
                    * int(self.times["grads_step"][0]),
                    dt=dateutil.parser.parse(date_time),
                )
            )

    def value_to_index(self, coord, value):
        possibles = [
            float(self.coords[coord]["resolution"]) * n
            + float(self.coords[coord]["minimum"])
            for n in range(0, int(self.coords[coord]["grads_size"]))
        ]
        return possibles.index(value)


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
    print(f.times)
    f.get(["dzdtprs"], "20210220 17:00", "0", "[1]", lev="[1]")
    print(f.value_to_index("lat", 0))
    if test == True:
        os.remove(config_file)
        import shutil

        shutil.rmtree("%s/atts" % route)
