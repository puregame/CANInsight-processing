from unittest import TestCase
from pathlib import Path

from database import db_session, ENGINE
from database.models import LogFile, Vehicle

from log_converter import get_new_log_filename

from datetime import datetime

class CRUDTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass

    def test_new_vehicle(self):
        raise NotImplementedError

    def test_get_vehicle_by_unit_number(self):
        raise NotImplementedError

    def test_new_log_file(self):
        raise NotImplementedError

    def test_update_log_status(self):
        raise NotImplementedError

    def test_updat_log_file_len(self):
        raise NotImplementedError

    def test_get_log_file(self):
        raise NotImplementedError

    def test_delete_log_file(self):
        raise NotImplementedError

    def create_log_in_db_if_not_exists(self):
        raise NotImplementedError

    def test_get_log_status(self):
        raise NotImplementedError

    def test_is_log_status(self):
        raise NotImplementedError

    def tearDown(self):
        """ Remove all testing airports from the db. """
        connection = ENGINE.connect()
        # Must clear the test patient from the test database after the test
        connection.execute("DELETE FROM log_file;")
        connection.execute("DELETE FROM vehicle;")
        connection.close()