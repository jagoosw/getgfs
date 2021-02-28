.. getgfs documentation master file, created by
   sphinx-quickstart on Sun Feb 28 19:01:16 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to getgfs
================

getgfs extracts weather forecast variables from the NOAA GFS forecast in a pure python, no obscure dependencies way. Currently you can:

- "Connect" to a forecast
- Search the variables 
- Download variables for any time range, longitude, latitude and altitude
- Download "wind profiles" where you get an interpolation object for the u and v wind components by altitude

Installing
==========
Installation is simple with PyPi:

```pip install getgfs```

Usage
=====
The library is straight forward to use. To get started create a Forecast object by:

.. code-block:: python
   :linenos:

   >>>import getgfs
   >>>f=getgfs.Forecast("0p25")

You can chose the resolution to be `0p25`, `0p50` or `1p00` and for the `0p25` forecast you can optional specify a shorter timestep by adding `1hr` after.

First to find what variable you are looking for use the search function, for example if I want the wind speed I could search for "wind":

.. code-block:: python
   :linenos:
   
   >>>f.search("wind")
   [('gustsfc', '** surface wind speed (gust) [m/s] ', 100), ('ugrdprs', '** (1000 975 950 925 900.. 7 5 3 2 1) u-component of wind [m/s] ', 125), ('ugrd_1829m', '** 1829 m above mean sea level u-component of wind [m/s] ', 125), ('ugrd_2743m', '** 2743 m above mean sea level u-component of wind [m/s] ', 125), ('ugrd_3658m', '** 3658 m above mean sea level u-component of wind [m/s] ', 125), ('ugrd10m', '** 10 m above ground u-component of wind [m/s] ', 125), ('ugrd20m', '** 20 m above ground u-component of wind [m/s] ', 125), ('ugrd30m', '** 30 m above ground u-component of wind [m/s] ', 125), ('ugrd40m', '** 40 m above ground u-component of wind [m/s] ', 125), ('ugrd50m', '** 50 m above ground u-component of wind [m/s] ', 125), ('ugrd80m', '** 80 m above ground u-component of wind [m/s] ', 125), ('ugrd100m', '** 100 m above ground u-component of wind [m/s] ', 125), ('ugrdsig995', '** 0.995 sigma level u-component of wind [m/s] ', 125), ('ugrd30_0mb', '** 30-0 mb above ground u-component of wind [m/s] ', 125), ('ugrd2pv', '** pv=2e-06 (km^2/kg/s) surface u-component of wind [m/s] ', 125), ('ugrdneg2pv', '** pv=-2e-06 (km^2/kg/s) surface u-component of wind [m/s] ', 125), ('ugrdpbl', '** planetary boundary layer u-component of wind [m/s] ', 125), ('ugrdtrop', '** tropopause u-component of wind [m/s] ', 125), ('vgrdprs', '** (1000 975 950 925 900.. 7 5 3 2 1) v-component of wind [m/s] ', 125), ('vgrd_1829m', '** 1829 m above mean sea level v-component of wind [m/s] ', 125), ('vgrd_2743m', '** 2743 m above mean sea level v-component of wind [m/s] ', 125), ('vgrd_3658m', '** 3658 m above mean sea level v-component of wind [m/s] ', 125), ('vgrd10m', '** 10 m above ground v-component of wind [m/s] ', 125), ('vgrd20m', '** 20 m above ground v-component of wind [m/s] ', 125), ('vgrd30m', '** 30 m above ground v-component of wind [m/s] ', 125), ('vgrd40m', '** 40 m above ground v-component of wind [m/s] ', 125), ('vgrd50m', '** 50 m above ground v-component of wind [m/s] ', 125), ('vgrd80m', '** 80 m above ground v-component of wind [m/s] ', 125), ('vgrd100m', '** 100 m above ground v-component of wind [m/s] ', 125), ('vgrdsig995', '** 0.995 sigma level v-component of wind [m/s] ', 125), ('vgrd30_0mb', '** 30-0 mb above ground v-component of wind [m/s] ', 125), ('vgrd2pv', '** pv=2e-06 (km^2/kg/s) surface v-component of wind [m/s] ', 125), ('vgrdneg2pv', '** pv=-2e-06 (km^2/kg/s) surface v-component of wind [m/s] ', 125), ('vgrdpbl', '** planetary boundary layer v-component of wind [m/s] ', 125), ('vgrdtrop', '** tropopause v-component of wind [m/s] ', 125), ('hgtmwl', '** max wind geopotential height [gpm] ', 133), ('icahtmwl', '** max wind icao standard atmosphere reference height [m] ', 133), ('presmwl', '** max wind pressure [pa] ', 133), ('tmpmwl', '** max wind temperature [k] ', 133), ('ugrdmwl', '** max wind u-component of wind [m/s] ', 133), ('vgrdmwl', '** max wind v-component of wind [m/s] ', 133)]

So now I can see I might want "gustsfc". Now if I want the wind speed at N70.1 W94.7 at 5:30 on the 27th of Febuary (only forecasts going back around a week are available and furutre times available depend on the forecast - look for f.times) I could do:

.. code-block:: python
   :linenos:

   >>>res=f.get(["gustsfc"],"20210227 5:30", 70.1,-94.7)
   >>>res.variables["gustsfc"].data
   array([[[18.808477]]])

You can get more information (e.g. what is the units of this) by exploring the variables information

.. code-block:: python
   :linenos:

   >>>f.variables["gustsfc"]
   {'_FillValue': 9.999e+20, 'missing_value': 9.999e+20, 'long_name': '** surface wind speed (gust) [m/s] ', 'level_dependent': False}

You can also get multiple variables by including more names in the list or a range of positions by using "'[min_lat:max_lat]'" type strings in place of the position parameters.

About
=====

The incentive to write this library was that the current method to get any variable was to download and extract information from a grib file. This requires you to use the ECMWF's `ecCodes` which `doesn't work on Windows <https://github.com/ecmwf/eccodes-python#system-dependencies>`_. To get around this the `OpenDAP <https://nomads.ncep.noaa.gov/>`_ version of the forecast is used and a custom decoder reads the downloaded files.

Previous Python projects that attempted this do not fulfil all the requirements, mainly being an importable library. Acknowledgment must be made to `albertotb <https://github.com/albertotb>`_'s project `get-gfs <https://github.com/albertotb/get-gfs>`_ for providing the first foothold along the way.


Requirements
------------
The required libraries (installed by PyPi) are:

```scipy, requests, fuzzywuzzy, numpy, python_dateutil, regex```

I have tried to ensure that these are well maintained and work across platforms (as this was the motive for writing this library).

Contributing
============
Please see `contributing <https://github.com/jagoosw/getgfs/blob/main/CONTRIBUTING.md>`_ for more information.

Todo
----
- Add historical forecasts from `<https://www.ncei.noaa.gov/thredds/dodsC/model-gfs-004-files-old/202003/20200328/gfs_4_20200328_1800_384.grb2.das>`_
- Add export to .nc file with netcdf4 (maybe an optional dependency)
- Add purge missing/unreliable (missing/unreliable fill values are provided but have to iterate through data to check probably)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getgfs.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
