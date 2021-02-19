import requests, json, os, re, dateutil.parser
from datetime import datetime, timedelta
import pandas as pd

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

    def get(self, variables, date_time, lat, lon, z=[]):
        """Returns the latest forcast available for the requested date and time

        Args:
            variables ([type]): [description]
            date ([type]): [description]
            time ([type]): [descriptionzw]
            lat ([type]): [description]
            lon ([type]): [description]
            z (list, optional): [description]. Defaults to [].
        """
        earliest_available = datetime.utcnow() - timedelta(days=7)
        latest_available = datetime.utcnow() - timedelta(
            hours=datetime.utcnow().hour
            - 6 * (datetime.utcnow().hour // 6 - 1)
            - int(self.times["grads_size"]) * int(self.times["grads_step"][0]),
            minutes=datetime.utcnow().minute,
            seconds=datetime.utcnow().second,
            microseconds=datetime.utcnow().microsecond,
        )
        if earliest_available < dateutil.parser.parse(date_time) < latest_available:
            pass
        else:
            raise ValueError(
                "Datetime requested ({dt}) is not available the moment, usually only the last weeks worth of forcasts are available and this model only extends {hours} hours forward.\nThis error may be caused by an uninterpretable datetime format.".format(
                    hours=int(self.times["grads_size"])
                    * int(self.times["grads_step"][0]),
                    dt=dateutil.parser.parse(date_time),
                )
            )


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
            raise Exception("The forcast resolution and timestep was not found")
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


if __name__ == "__main__":
    test = False
    f = Forcast("0p25")
    print(f.times)
    f.get(1, "20210218 12:00", 1, 1)
    if test == True:
        os.remove(config_file)
        import shutil

        shutil.rmtree("%s/atts" % route)
