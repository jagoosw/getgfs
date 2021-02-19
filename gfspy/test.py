import unittest
from gfspy import *

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


class TestBasics(unittest.TestCase):
    def test_attribute(self):
        self.assertEqual(
            Forcast("0p25").times, {"grads_size": "81", "grads_step": "3hr"}
        )

    def check_folders(self):
        if not os.path.isdir("%s/atts" % gfspy.route) and not os.path.isfile(
            gfspy.config_file
        ):
            result = "Required files and folders are not being created"
        else:
            result = "Ok"
        self.assertEqual(result, "Ok")


if __name__ == "__main__":
    unittest.main()
