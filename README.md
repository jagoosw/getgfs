# getgfs
getgfs extracts weather forecast variables from the NOAA GFS forecast in a pure python, no obscure dependencies way. Currently you can:
- "Connect" to a forecast
- Search the variables 
- Download variables for any time range, longitude, latitude and altitude
- Download "wind profiles" where you get an interpolation object for the u and v wind components by altitude

For full documentation please see the [docs]()

# Installing
Installation is simple with PyPi:

`pip install getgfs`

## Requirements
The required libraries (installed by PyPi) are:

```scipy, requests, fuzzywuzzy, numpy, python_dateutil, regex```

I have tried to ensure that these are well maintained and work across platforms (as this was the motive for writing this library).

# About

The incentive to write this library was that the current method to get any variable was to download and extract information from a grib file. This requires you to use the ECMWF's `ecCodes` which [doesn't work on Windows](https://github.com/ecmwf/eccodes-python#system-dependencies). To get around this the [OpenDAP](https://nomads.ncep.noaa.gov/) version of the forecast is used and a custom decoder reads the downloaded files.

Previous Python projects that attempted this do not fulfil all the requirements, mainly being an importable library. Acknowledgment must be made to [albertotb](https://github.com/albertotb)'s project [get-gfs](https://github.com/albertotb/get-gfs) for providing the first foothold along the way.

# Usage
The library is straight forward to use. To get started create a Forecast object by:

```
>>>import getgfs
>>>f=getgfs.Forecast("0p25")
```

You can choose the resolution to be `0p25`, `0p50` or `1p00` and for the `0p25` forecast you can optional specify a shorter time step by adding `1hr` after.

First to find what variable you are looking for use the search function, for example if I want the wind speed I could search for "wind":

```
>>>f.search("wind")
[('gustsfc', '** surface wind speed (gust) [m/s] ', 100), ('ugrdprs', '** (1000 975 950 925 900.. 7 5 3 2 1) u-component of wind [m/s] ', 125), ('ugrd_1829m', '** 1829 m above mean sea level u-component of wind [m/s] ', 125), ...
```

So now I can see I might want "gustsfc". Now if I want the wind speed at N70.1 W94.7 at 5:30 on the 27th of February (only forecasts going back around a week are available and future times available depend on the forecast - look for f.times) I could do:

```
>>>res=f.get(["gustsfc"],"20210227 5:30", 70.1,-94.7)
>>>res.variables["gustsfc"].data
array([[[18.808477]]])
```

You can get more information (e.g. what is the units of this) by exploring the variables information

```>>>f.variables["gustsfc"]
{'_FillValue': 9.999e+20, 'missing_value': 9.999e+20, 'long_name': '** surface wind speed (gust) [m/s] ', 'level_dependent': False}
```

You can also get multiple variables by including more names in the list or a range of positions by using "'[min_lat:max_lat]'" type strings in place of the position parameters.


## Contributing
Please see [contributing](CONTRIBUTING.md) for more information.

# Todo
- Add historical forecasts from https://www.ncei.noaa.gov/thredds/dodsC/model-gfs-004-files-old/202003/20200328/gfs_4_20200328_1800_384.grb2.das
- Add export to .nc file with netcdf4 (maybe an optional dependency)
- Add purge missing/unreliable (missing/unreliable fill values are provided but have to iterate through data to check probably)