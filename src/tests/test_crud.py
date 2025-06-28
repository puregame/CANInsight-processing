from distutils.command.upload import upload
from unittest import TestCase
from pathlib import Path

from psycopg2 import IntegrityError

from database import db_session, ENGINE
from database.models import LogFile, Vehicle
from database.crud import *
from sqlalchemy.exc import IntegrityError

from log_converter import get_new_log_filename

from datetime import datetime

class CRUDTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass

    def test_new_vehicle(self):
        # get a vehicle that does not exist
        self.assertEqual(get_vehicle_by_unit_number("notexists"), None)
        
        # insert a vehicle and get its information
        new_vehicle("test_unit_number", "test_vehicle_type", "SN123456")
        vehicle_dict = get_vehicle_by_unit_number("test_unit_number").__dict__
        vehicle_dict.pop("_sa_instance_state")
        self.assertEqual(vehicle_dict, {"unit_number": "test_unit_number",
                                         "vehicle_type": "test_vehicle_type",
                                         "serial_number": "SN123456",
                                         "status": None})

        # check that we can't insert a vehicle that already exists
        self.assertRaises(IntegrityError, new_vehicle, "test_unit_number", "test_vehicle_type", "SN123456")

        new_vehicle("test_unit_number1", "test_vehicle_type1", "SN56789", "In Service")
        vehicle_dict = get_vehicle_by_unit_number("test_unit_number1").__dict__
        vehicle_dict.pop("_sa_instance_state")
        self.assertEqual(vehicle_dict, {"unit_number": "test_unit_number1",
                                         "vehicle_type": "test_vehicle_type1",
                                         "serial_number": "SN56789",
                                         "status": "In Service"})

    def test_get_vehicle_by_unit_number(self):
        # tested in new vehicle tests
        pass

    def test_new_log_file(self):
        self.test_new_vehicle() # create some test vehicles
        self.start_time1 = datetime.fromisoformat('2021-01-10T10:10:10.000Z'.replace("Z", "+00:00"))
        upload_time = datetime.now()
        new_log_file_id = new_log_file(self.start_time1, "test_unit_number")
        # test new log file with all defaults
        self.assertIsInstance(new_log_file_id, int)
        log_file_db = get_log_file(self.start_time1, "test_unit_number")
        self.assertEqual(self.start_time1.replace(tzinfo=None), log_file_db.start_time.replace(tzinfo=None)) # remove timezone info for SQLite
        self.assertEqual(log_file_db.processing_status, "Uploaded")
        self.assertIsNone(log_file_db.length)
        self.assertIsNone(log_file_db.samples)
        self.assertEqual(upload_time.replace(microsecond=0), log_file_db.upload_time.replace(microsecond=0))

        # test conflicting
        self.assertRaises(IntegrityError, new_log_file, self.start_time1, "test_unit_number")

        # test inserting with none as default
        self.start_time2 = datetime.fromisoformat('2021-01-10T11:10:10.000Z'.replace("Z", "+00:00"))
        upload_time = datetime.now()
        # test new log file with all defaults
        new_log_file_id = new_log_file(self.start_time2, "test_unit_number", status="Complete", 
                                       upload_time=upload_time, length=1234.7, samples=40000)
        self.assertIsInstance(new_log_file_id, int)
        log_file_db = get_log_file(self.start_time2, "test_unit_number")
        self.assertEqual(self.start_time2.replace(tzinfo=None), log_file_db.start_time.replace(tzinfo=None)) # remove timezone info for SQLite
        self.assertEqual(log_file_db.processing_status, "Complete")
        self.assertEqual(log_file_db.length, 1234.7)
        self.assertEqual(log_file_db.samples, 40000)
        self.assertEqual(upload_time, log_file_db.upload_time)

    def test_update_log_status(self):
        self.test_new_log_file()
        self.assertEqual(get_log_status(self.start_time1, "test_unit_number"), "Uploaded")
        self.assertEqual(get_log_status(self.start_time2, "test_unit_number"), "Complete")

        update_log_file_status(self.start_time1, "test_unit_number", "Combined With Earlier LOG")
        self.assertEqual(get_log_status(self.start_time1, "test_unit_number"), "Combined With Earlier LOG")
        update_log_file_status(self.start_time2, "test_unit_number", 1)
        self.assertEqual(get_log_status(self.start_time2, "test_unit_number"), "1")

    def test_update_log_file_len(self):
        self.test_new_log_file()
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").length, None)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").samples, None)
        update_log_file_len(self.start_time1, "test_unit_number", 10, 100)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").length, 10)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").samples, 100)
        update_log_file_len(self.start_time1, "test_unit_number", 999000, 999000)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").length, 999000)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").samples, 999000)
        update_log_file_len(self.start_time1, "test_unit_number", 0, 0)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").length, 0)
        self.assertEqual(get_log_file(self.start_time1, "test_unit_number").samples, 0)

    def test_get_log_file(self):
        # tested in adding log file
        pass

    def test_delete_log_file(self):
        self.test_new_log_file()
        self.assertIsNotNone(get_log_file(self.start_time1, "test_unit_number"))
        delete_log_file(self.start_time1, "test_unit_number")
        self.assertIsNone(get_log_file(self.start_time1, "test_unit_number"))

        self.assertIsNotNone(get_log_file(self.start_time2, "test_unit_number"))
        delete_log_file(self.start_time2, "test_unit_number")
        self.assertIsNone(get_log_file(self.start_time2, "test_unit_number"))

    def test_create_log_in_db_if_not_exists(self):
        self.test_new_log_file()

        # test adding new log that already exists
        self.assertIs(create_log_in_database_if_not_exists(self.start_time1, "test_unit_number"), LogFile)
        self.assertIs(create_log_in_database_if_not_exists(self.start_time2, "test_unit_number"), LogFile)

        # test adding a new log to an old unit
        start = datetime.fromisoformat('2021-01-10T10:10:10.000Z'.replace("Z", "+00:00"))
        self.assertIsInstance(create_log_in_database_if_not_exists(start, "test_unit_number"), int)
        log = get_log_file(start, "test_unit_number")
        self.assertEqual(log.unit_number, "test_unit_number")
        self.assertEqual(log.length, None)
        self.assertEqual(log.samples, None)

        # test adding a new log to a new unit
        start = datetime.fromisoformat('2021-01-10T13:10:10.000Z'.replace("Z", "+00:00"))
        self.assertIsInstance(create_log_in_database_if_not_exists(start, "test_unit_number2", "test2_unit_type"), int)
        log = get_log_file(start, "test_unit_number2")
        self.assertEqual(log.unit_number, "test_unit_number2")
        self.assertEqual(log.length, None)
        self.assertEqual(log.samples, None)
        unit = get_vehicle_by_unit_number("test_unit_number2")
        self.assertEqual(unit.vehicle_type, "test2_unit_type")

    def test_get_log_status(self):
        # tested in test_update_log_status
        pass

    def test_is_log_status(self):
        self.test_new_log_file()
        self.assertTrue(is_log_status(self.start_time1, "test_unit_number", "Uploaded"))
        self.assertTrue(is_log_status(self.start_time2, "test_unit_number", "Complete"))

        update_log_file_status(self.start_time1, "test_unit_number", "Combined With Earlier LOG")
        self.assertTrue(is_log_status(self.start_time1, "test_unit_number", "Combined With Earlier LOG"))

    def tearDown(self):
        """Remove all test data from the database after each test."""
        with ENGINE.begin() as connection:
            connection.execute(LogFile.__table__.delete())
            connection.execute(Vehicle.__table__.delete())
            connection.close()