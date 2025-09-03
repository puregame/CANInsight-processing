from unittest import TestCase

from database import ENGINE
from database import Session
from database.crud import get_vehicle_by_unit_number, new_vehicle, new_log_file, get_log_file, update_log_file_status, get_log_status, is_log_status, does_log_exist, delete_log_file, update_log_file_len, 
from database.models import Base
from database.upgrade import init_and_upgrade_db
from sqlalchemy.exc import IntegrityError

from datetime import datetime

class CRUDTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        init_and_upgrade_db()
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
        log = new_log_file(self.start_time1, "test_unit_number")
        self.new_log_file_id = log.id

        # test new log file with all defaults
        self.assertIsInstance(self.new_log_file_id, str)
        log_file_db = get_log_file(self.new_log_file_id)  # ensure log file exists
        self.assertEqual(self.start_time1.replace(tzinfo=None), log_file_db.log_start_time.replace(tzinfo=None)) # remove timezone info for SQLite
        self.assertEqual(log_file_db.processing_status, "Uploaded")
        self.assertIsNone(log_file_db.length_sec)
        self.assertIsNone(log_file_db.samples)
        self.assertEqual(upload_time.replace(microsecond=0), log_file_db.upload_time.replace(microsecond=0))

        # test new log file with No defaults
        self.start_time2 = datetime.fromisoformat('2021-01-10T11:10:10.000Z'.replace("Z", "+00:00"))
        upload_time = datetime.now()
        # test new log file with all defaults
        log2 = new_log_file(self.start_time2, "test_unit_number", status="Complete",
                                       upload_time=upload_time, length_sec=1234.7, samples=40000, hash=b"testhash")
        self.new_log_file_id2 = log2.id
        self.assertIsInstance(self.new_log_file_id2, str)
        log_file_db = get_log_file(self.new_log_file_id2)
        self.assertEqual(self.start_time2.replace(tzinfo=None), log_file_db.log_start_time.replace(tzinfo=None)) # remove timezone info for SQLite
        self.assertEqual(log_file_db.processing_status, "Complete")
        self.assertEqual(log_file_db.length_sec, 1234.7)
        self.assertEqual(log_file_db.samples, 40000)
        self.assertEqual(log_file_db.hash, b"testhash")
        self.assertEqual(upload_time, log_file_db.upload_time)

    def test_update_log_status(self):
        self.test_new_log_file()
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        uuid1 = log.id
        log = get_log_file(self.new_log_file_id2)  # ensure log file exists
        uuid2 = log.id
        self.assertEqual(get_log_status(uuid1), "Uploaded")
        self.assertEqual(get_log_status(uuid2), "Complete")

        update_log_file_status(uuid1, "Combined With Earlier LOG")
        self.assertEqual(get_log_status(uuid1), "Combined With Earlier LOG")
        update_log_file_status(uuid2, 1)
        self.assertEqual(get_log_status(uuid2), "1")

    def test_update_log_file_len(self):
        self.test_new_log_file()
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        self.assertEqual(log.length_sec, None)
        self.assertEqual(log.samples, None)


        update_log_file_len(log.id, 10, 100)
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        self.assertEqual(log.length_sec, 10)
        self.assertEqual(log.samples, 100)

        update_log_file_len(log.id, 999000, 999000)
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        self.assertEqual(log.length_sec, 999000)
        self.assertEqual(log.samples, 999000)

        update_log_file_len(log.id, 0, 0)
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        self.assertEqual(log.length_sec, 0)
        self.assertEqual(log.samples, 0)

    def test_get_log_file(self):
        # tested in adding log file
        pass

    def test_delete_log_file(self):
        self.test_new_log_file()
        log = get_log_file(self.new_log_file_id)  # ensure log file exists
        self.assertIsNotNone(log)
        delete_log_file(log.id)
        self.assertIsNone(get_log_file(self.new_log_file_id))  # ensure log file exists

        log2 = get_log_file(self.new_log_file_id2)
        self.assertIsNotNone(log2)
        delete_log_file(log2.id)
        self.assertIsNone(get_log_file(self.new_log_file_id2))

    def test_check_hash(self):
        self.test_new_log_file()

        # test adding new log with a hash that already exists
        self.assertTrue(does_log_exist(b'testhash', 'test_unit_number'))
        self.assertFalse(does_log_exist(b'testhash1', 'test_unit_number'))
        self.assertFalse(does_log_exist(b'testhash', 'test_unit_number2'))

    def test_get_log_status(self):
        # tested in test_update_log_status
        pass

    def test_is_log_status(self):
        self.test_new_log_file()
        
        log = get_log_file(self.new_log_file_id)  # ensure log file exists  # ensure log file exists
        log2 = get_log_file(self.new_log_file_id2)  # ensure log file exists
        
        self.assertTrue(is_log_status(log.id, "Uploaded"))
        self.assertFalse(is_log_status(log2.id, "Completed"))
        self.assertTrue(is_log_status(log2.id, "Complete"))
        self.assertFalse(is_log_status(log2.id, "Completed"))

        update_log_file_status(log.id, "Combined With Earlier LOG")
        self.assertTrue(is_log_status(log.id, "Combined With Earlier LOG"))
        self.assertFalse(is_log_status(log.id, "derp status"))


    def test_new_vehicle_invalid(self):
        # Test missing required fields
        with self.assertRaises(TypeError):
            new_vehicle()  # Missing all args

        with self.assertRaises(TypeError):
            new_vehicle("unitonly")  # Missing other args

    def test_new_log_file_missing_vehicle(self):
        # Should raise or handle vehicle not existing
        start_time = datetime.fromisoformat('2021-01-11T10:10:10.000+00:00')
        with Session(ENGINE) as session:
            from sqlalchemy import text
            fk_status = session.execute(text("PRAGMA foreign_keys;")).scalar()
            print("Foreign keys enabled:", fk_status)
        with self.assertRaises(IntegrityError):
            new_log_file(start_time, "no_such_vehicle")

    def test_update_log_file_status_invalid(self):
        self.test_new_log_file()
        log = get_log_file(self.new_log_file_id)  # ensure log file exists
        
        # Update with empty string
        update_log_file_status(log.id, "")
        self.assertTrue(is_log_status(log.id, ""))

    def test_update_log_file_len_negative(self):
        self.test_new_log_file()
        log = get_log_file(self.new_log_file_id)  # ensure log file exists

        # Test negative length and samples
        update_log_file_len(log.id, -1, -100)
        log = get_log_file(self.new_log_file_id)  # ensure log file exists
        self.assertEqual(log.length_sec, -1)
        self.assertEqual(log.samples, -100)  # Depends if validation is enforced

    def test_hash_collision(self):
        self.test_new_log_file()

        # Insert second log with same hash but different timestamp
        ts = datetime.fromisoformat('2021-01-10T12:10:10.000+00:00')
        new_log_file(ts, "test_unit_number", hash=b"testhash")
        self.assertTrue(does_log_exist(b"testhash", "test_unit_number"))


    def tearDown(self):
        """Remove all test data from the database after each test."""
        with ENGINE.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())