# gfspy
gfspy will be a Python library that extracts information from the NOAA GFS forecast without using `.grb2` files as the cross platform compatibility of the ECMWF `ecCodes` dependency required to read them if [poor](https://github.com/ecmwf/eccodes-python#system-dependencies) and the library needed to read them often more bloated than required. To get around this the [OpenDAP](https://nomads.ncep.noaa.gov/) version of the forecast.

Previous Python projects that attempted this do not fulfil all the requirements, mainly being an importable library. Acknowledgment must be made to [albertotb](https://github.com/albertotb)'s project [get-gfs](https://github.com/albertotb/get-gfs) for providing the first foothold along the way.

## Current status
Weather forecast variables can now easily be found but with limited output niceness
