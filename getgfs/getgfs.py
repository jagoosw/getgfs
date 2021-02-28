"""getgfs - a library for extracting weather forecast variables from the NOAA GFS forecast in a pure python, no obscure dependencies way
"""
import requests, json, os, re, dateutil.parser, sys
from datetime import datetime, timedelta
import numpy as np
from scipy.interpolate import interp1d
from .decode import *

try:
    from fuzzywuzzy import fuzz
except:
    pass

__copyright__ = """
    getgfs - a library for extracting weather forecast variables from the NOAA GFS 
    forecast in a pure python, no obscure dependencies way
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


class Forecast:
    """Object that can be manipulated to get forecast information"""

    def __init__(self, resolution="0p25", timestep=""):
        """Setting up the forecast object by specifying the forecast type

        Args:
            resolution (str, optional): The forecast resulution, choices are 1p00, 0p50 and 0p25. Defaults to "0p25".
            timestep (str, optional): The timestep of the forecast to use, most do not have a choice but 0p25 can be 3hr (default) or 1hr. Defaults to "".
        """
        if timestep != "":
            timestep = "_" + timestep

        if resolution not in ["1p00", "0p50", "0p25"]:
            raise ValueError(
                "You have entered an invalid forecast resulution, the choices are 1p00, 0p50 and 0p25. You entered %s"
                % resolution
            )
        if (timestep != "" and resolution != "0p25") or (
            timestep not in ["_1hr", ""] and resolution == "0p25"
        ):
            raise ValueError(
                "You have entered an invalid forecast timestep, the only choice is 1hr for 0p25 forecasts or the default. You entered %s"
                % timestep
            )
        self.resolution = resolution
        self.timestep = timestep
        self.times, self.coords, self.variables = get_attributes(resolution, timestep)

    def get(self, variables, date_time, lat, lon):
        """Returns the latest forecast available for the requested date and time

        Note
        ----
        - "raw" since you have to put indexes in rather than coordinates and it returns a file object rather than a processed file
        - If a variable has level dependance, you get all the levels - it seems extremely hard to impliment otherwise

        Args:
            variables (list): list of required variables by short name
            date_time (string): datetime requested (parser used so any format fine)
            lat (string or number): latitude in the format "[min:max]" or a single value
            lon (string or number): longitude in the format "[min:max]" or a single value

        Raises:
            ValueError: Invalid variable choice
            ValueError: Level dependance needs to be specified for chosen variable
            Exception: Unknown failure to download the file

        Returns:
            File Object: File object with the downloaded variable data (see File documentation)
        """

        # Get forecast date run, date, time
        forecast_date, forecast_time, query_time = self.datetime_to_forecast(date_time)

        # Get latitude
        lat = self.value_input_to_index("lat", lat)

        # Get longitude
        lon = self.value_input_to_index("lon", lon)

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
                date=forecast_date,
                hour=int(forecast_time),
                info="ascii?{query}".format(query=query),
            )
        )
        if r.status_code != 200:
            raise Exception(
                """The altitude pressure forecast information could not be downloaded. 
        This error should never occure but it may be helpful to know the requested information was:
        - Forecast date: {f_date}
        - Forecast time: {f_time}
        - Query time: {q_time}
        - Latitude: {lat}
        - Longitude: {lon}""".format(
                    f_date=forecast_date,
                    f_time=forecast_time,
                    q_time=query_time,
                    lat=lat,
                    lon=lon,
                )
            )

        return File(r.text)

    def datetime_to_forecast(self, date_time):
        """Works out which forecast date/run/time is required for the latest values for a chosen time

        Args:
            date_time (string): The date and time of the desired forecast, parser is used so any format is valid e.g. 20210205 11pm

        Raises:
            ValueError: The date time requested is not available from the NOAA at this time

        Returns:
            string: forecast date
            string: forecast run
            string: forecast query time (the appropriate timestep within the forecast)
        """
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
        latest_forecast = latest_available - timedelta(
            hours=int(self.times["grads_size"]) * int(self.times["grads_step"][0])
        )
        if earliest_available < desired_date < latest_available:
            query_forecast = latest_forecast
            while desired_date < query_forecast:
                query_forecast -= timedelta(hours=6)

            forecast_date = query_forecast.strftime("%Y%m%d")
            forecast_time = query_forecast.strftime("%H")

            query_time = "[{t_ind}]".format(
                t_ind=round(
                    (desired_date - query_forecast).seconds
                    / (int(self.times["grads_step"][0]) * 60 * 60)
                )
            )

        else:
            raise ValueError(
                "Datetime requested ({dt}) is not available the moment, usually only the last weeks worth of forecasts are available and this model only extends {hours} hours forward.\nThis error may be caused by an uninterpretable datetime format.".format(
                    hours=int(self.times["grads_size"])
                    * int(self.times["grads_step"][0]),
                    dt=dateutil.parser.parse(date_time),
                )
            )

        return forecast_date, forecast_time, query_time

    def value_input_to_index(self, coord, inpt):
        """Turns a chosen value of a coordinate/coordinate range to the index in the forecast array

        Args:
            coord (string): The short name of the coordinate to convert
            inpt (float/str): The value or range requested, for a range a string in the format [min_val:max_val] is required

        Raises:
            ValueError: Incorrect inpt format

        Returns:
            str: Index of coordinate value(s) as the forecast requires it (i.e. within [])
        """
        if isinstance(inpt, str):
            if inpt[0] == "[" and inpt[-1] == "]" and ":" in inpt:
                val_1 = float(re.findall(r"\[(.*?):", inpt))
                val_2 = float(re.findall(r"\:(.*?)]", inpt))
                val_min = self.value_to_index(coord, min(val_1, val_2))
                val_max = self.value_to_index(coord, max(val_1, val_2))
                ind = "[%s:%s]" % (val_min, val_max)
            else:
                try:
                    inpt = float(inpt)  # isnumeric apparently doesn't work for floats
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
        """Turns a coordinate value into the index in the forecast array

        Args:
            coord (string): The short name of the coordinate to convert
            inpt (float/str): The value requested

        Returns:
            int: Index in array
        """
        possibles = [
            float(self.coords[coord]["resolution"]) * n
            + float(self.coords[coord]["minimum"])
            for n in range(0, int(self.coords[coord]["grads_size"]))
        ]
        closest = min(possibles, key=lambda x: abs(x - value))
        return possibles.index(closest)

    def search(self, variable, sensetivity=80):
        """The short names of the forecast variables are nonsence so this can be used to find
        the short name (used for the rest of the forecast) that you are looking for

        Note
        ----
        Will not work if fuzzywuzzy is not installed

        Args:
            variable (string): Search terms for the variable (e.g. U-Component wind)
            sensetivity (int, optional): The search sensitivity, for common words a higher sensitivity may be required. Defaults to 80.

        Raises:
            RuntimeError: Fuzzywuzzy not installed

        Returns:
            list: List of possible matches sorted by ratio, short name (what you need) and long name also given
        """
        if "fuzzywuzzy.fuzz" not in sys.modules:
            raise RuntimeError(
                "You can not use search_name without fuzzywuzzy installed, please `pip install fuzzywuzzy`. Other functionality is still available"
            )

        possibles = []
        for var in self.variables.keys():
            if "long_name" in self.variables[var].keys():
                ln = fuzz.partial_ratio(self.variables[var]["long_name"], variable)
                sn = fuzz.partial_ratio(var, variable)
                if ln > sensetivity or sn > sensetivity:
                    possibles.append((var, self.variables[var]["long_name"], ln + sn))

        possibles = sorted(possibles, key=lambda tup: tup[2])
        return possibles

    def get_windprofile(self, date_time, lat, lon):
        """Finds the verticle wind profile for a location. I wrote this since it is what
        I require in another program. The U/V compoents of wind with sigma do not go down to
        the surface so the surface components are also included as well as a pressure altitude
        change of x- variable.

        Args:
            date_time (string): datetime requested (parser used so any format fine)
            lat (string or number): Latitude for data
            lon (string or number): Longitude for data

        Returns:
            interpolation object: U component of wind interpolater by altitude
            interpolation object: V component of wind interpolater by altitude
        """
        info = self.get(
            ["ugrdprs", "vgrdprs", "ugrd2pv", "vgrd2pv", "hgtsfc", "hgtprs"],
            date_time,
            lat,
            lon,
        )

        u_wind = list(info.variables["ugrdprs"].data.flatten()) + list(
            info.variables["ugrd2pv"].data.flatten()
        )
        v_wind = list(info.variables["vgrdprs"].data.flatten()) + list(
            info.variables["vgrd2pv"].data.flatten()
        )

        # at the altitudes we are concerned with the geopotential height and altitude are within 0.5km of eachother
        alts = list(info.variables["hgtprs"].data.flatten()) + list(
            info.variables["hgtsfc"].data.flatten()
        )

        return interp1d(alts, u_wind), interp1d(alts, v_wind)

    def __str__(self):
        print(type(self))
        return "GFS forecast with resolution %s" % self.resolution


def get_attributes(res, step):
    """Finds the available variables and coordinates for a given forecast

    Args:
        res (str, optional): The forecast resulution, choices are 1p00, 0p50 and 0p25. Defaults to "0p25".
        step (str, optional): The timestep of the forecast to use, most do not have a choice but 0p25 can be 3hr (default) or 1hr. Defaults to "".

    Raises:
        Exception: Failed to download the requested resolution and forecast
        RuntimeError: Failed to download the other attributes

    Returns:
        dict: Time attributes (the number of timesteps and the size of the timesteps)
        dict: Coordinates for the forecast with their short name, number of steps, min, max, resolution
        dict: Variables with all the information about them
    """
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
            raise Exception("The forecast resolution and timestep was not found")
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
            raise RuntimeError("The forecast resolution and timestep was not found")
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
    """Works out what is being refered to by a line in the das and dds pages for the forecast

    Args:
        possibles (list): Possible titles
        line (string): Line to search

    Returns:
        int: Index of the attribute
    """
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
    """Rounds to the nearest hour for a datetime object

    Args:
        t (datetime): Datetime to round

    Returns:
        datetime: Rounded datetime
    """
    return t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + timedelta(
        hours=t.minute // 30
    )
