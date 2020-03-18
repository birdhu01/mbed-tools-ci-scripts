from mbed_tools_ci_scripts.license_files import _to_copyright_date_string
import unittest
from datetime import datetime


class TestPythonHelpers(unittest.TestCase):
    def test_copyright_dates(self):
        self.assertEqual("2020", _to_copyright_date_string(2020, 2020))
        self.assertEqual("2020-2021", _to_copyright_date_string(2020, 2021))
        this_year = datetime.now().year
        self.assertEqual(str(this_year), _to_copyright_date_string(this_year, this_year))
