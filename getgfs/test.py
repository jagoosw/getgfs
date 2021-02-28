import unittest
from .getgfs import *
from .decode import *

# Seems like these aren't actually working

__copyright__ = """
    getgfs - A library that extracts information from the NOAA GFS forecast without using .grb2 files
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

example_file = """hgtprs, [5][4][2][4]
[0][0][0], 143.26001, 143.26001, 143.26001, 143.26001
[0][0][1], 142.28401, 142.268, 142.25201, 142.25201

[0][1][0], 329.76636, 329.76636, 329.76636, 329.76636
[0][1][1], 328.71036, 328.71036, 328.69437, 328.67834

[0][2][0], 520.16754, 520.16754, 520.16754, 520.16754
[0][2][1], 519.04755, 519.0315, 519.0155, 518.9995

[0][3][0], 714.6294, 714.6294, 714.6294, 714.6294
[0][3][1], 713.4134, 713.3974, 713.3974, 713.3814


[1][0][0], 141.57744, 141.57744, 141.57744, 141.57744
[1][0][1], 142.63344, 142.60144, 142.56944, 142.53745

[1][1][0], 328.0829, 328.0829, 328.0829, 328.0829
[1][1][1], 328.93088, 328.9149, 328.8829, 328.8509

[1][2][0], 518.4631, 518.4631, 518.4631, 518.4631
[1][2][1], 519.1191, 519.08704, 519.07104, 519.03906

[1][3][0], 712.9098, 712.9098, 712.9098, 712.9098
[1][3][1], 713.3578, 713.3418, 713.3258, 713.29376


[2][0][0], 132.99606, 132.99606, 132.99606, 132.99606
[2][0][1], 133.52406, 133.50807, 133.49207, 133.46007

[2][1][0], 319.4645, 319.4645, 319.4645, 319.4645
[2][1][1], 319.8485, 319.83252, 319.81653, 319.78452

[2][2][0], 509.819, 509.819, 509.819, 509.819
[2][2][1], 510.059, 510.043, 510.027, 510.011

[2][3][0], 704.22687, 704.22687, 704.22687, 704.22687
[2][3][1], 704.3229, 704.3068, 704.29083, 704.29083


[3][0][0], 129.57916, 129.57916, 129.57916, 129.57916
[3][0][1], 129.99516, 129.97916, 129.94716, 129.93117

[3][1][0], 315.9453, 315.9453, 315.9453, 315.9453
[3][1][1], 316.21732, 316.18533, 316.16934, 316.15332

[3][2][0], 506.1779, 506.1779, 506.1779, 506.1779
[3][2][1], 506.3059, 506.2899, 506.2739, 506.2579

[3][3][0], 700.4825, 700.4825, 700.4825, 700.4825
[3][3][1], 700.4665, 700.4505, 700.41846, 700.40247


[4][0][0], 124.38838, 124.38838, 124.38838, 124.38838
[4][0][1], 125.04438, 125.02838, 125.01238, 125.01238

[4][1][0], 310.62332, 310.62332, 310.62332, 310.62332
[4][1][1], 311.1353, 311.11932, 311.11932, 311.08734

[4][2][0], 500.7546, 500.7546, 500.7546, 500.7546
[4][2][1], 501.10663, 501.0906, 501.0906, 501.07462

[4][3][0], 694.9354, 694.9354, 694.9354, 694.9354
[4][3][1], 695.1274, 695.1274, 695.1114, 695.1114



time, [5]
737842.0, 737842.125, 737842.25, 737842.375, 737842.5
lev, [4]
1000.0, 975.0, 950.0, 925.0
lat, [2]
-90.0, -89.75
lon, [4]
0.0, 0.25, 0.5, 0.75
hgtmwl, [1][1][1]
[0][0], 9504.847


time, [1]
737842.0
lat, [1]
-90.0
lon, [1]
0.0"""

example = File(example_file)


class TestBasics(unittest.TestCase):
    def test_attribute(self):
        self.assertEqual(
            Forecast("0p25").times, {"grads_size": "81", "grads_step": "3hr"}
        )

    def test_folders(self):
        if not os.path.isdir("%s/atts" % route) and not os.path.isfile(config_file):
            result = "Required files and folders are not being created"
        else:
            result = "Ok"
        self.assertEqual(result, "Ok")


class Decode(unittest.TestCase):
    def test_variables(self):
        self.assertEqual(
            example.variables["hgtprs"].coords["time"].values,
            [737842.0, 737842.125, 737842.25, 737842.375, 737842.0],
        )

    def test_data(self):
        self.assertEqual(example.variables["hgtmwl"].data, [[[9504.847]]])


if __name__ == "__main__":
    unittest.main()
