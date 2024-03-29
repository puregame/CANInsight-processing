from unittest import TestCase
from pathlib import Path

from database import db_session, ENGINE
from database.models import LogFile, Vehicle

from log_converter import get_files_to_process, get_new_log_filename

from datetime import datetime

class LogConverterTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass

    def test_get_new_log_filename(self):
        self.assertEqual(get_new_log_filename("2021-01-01T00:00:01.990Z", "CAN_001.LOG"), "2021-01-01T00-00-01-990Z")
        self.assertEqual(get_new_log_filename("2022-12-20T17:30:02.110Z", "CAN_001.LOG"), "2022-12-20T17-30-02-110Z")

    def test_checksum(self):
        """ Test the checksum function on local files. """
        pass

    def test_get_files_to_process(self):
        self.assertListEqual(get_files_to_process(Path("tests/")), [])
        self.assertListEqual(get_files_to_process(Path("tests/test_data")), ['test_data_all_good_lines.log','test_data_bad_lines.log','test_data_bad_timestamp.log','test_data_continues.log','test_data_dat.log','test_data_dat_continues.log','test_data_with_csv_logtype.log'])

    def tearDown(self):
        """ Remove all testing airports from the db. """
        connection = ENGINE.connect()
        # Must clear the test patient from the test database after the test
        connection.execute("DELETE FROM log_file;")
        connection.execute("DELETE FROM vehicle;")
        connection.close()