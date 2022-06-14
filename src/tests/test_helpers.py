from unittest import TestCase
from pathlib import Path
from datetime import datetime

from pandas import Series, Float64Dtype
from numpy import float64

from helpers import read_log_to_df

from database import db_session, ENGINE
from database.models import LogFile, Vehicle

class LogConverterTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass
    
    def test_read_log_with_continuation(self):
        pass

    def test_read_log_with_bad_timestamp(self):
        """ test reading basic CSV with bad timestamp, lines should be ignored"""
        df, meta, continues = read_log_to_df("tests/test_data/test_data_bad_timestamp.log")
        self.assertEqual(len(df), 4)

    def test_read_csv_with_type(self):
        """ test reading basic CSV style log file with log type in meta """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_with_csv_logtype.log")
        self.assertEqual(continues, False)
        self.assertEqual(len(df), 6)
        self.assertIn("log_type", meta)
        self.assertEqual(meta['log_type'], "CSV0.1")

    def test_read_log_to_df_good_csv(self):
        """ test reading basic CSV style log file with no log type in meta """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_all_good_lines.log")
        self.assertEqual(continues, False)
        self.assertEqual(meta['unit_type'], "MM430")
        self.assertEqual(meta['unit_number'], "E00123")
        self.assertEqual(meta['can_1']['bus_name'], "Main")
        self.assertEqual(len(df), 6)
        self.assertTrue(df.iloc[0].equals(Series(data={"timestamp": 1.127, 
                                                        "CAN_BUS": 2, 
                                                        "CAN_EXT": 1, 
                                                        "CAN_ID": 0xCF62602, 
                                                        "CAN_LEN": 5, 
                                                        "Data0": 1, 
                                                        "Data1": 0x12, 
                                                        "Data2": 0, 
                                                        "Data3": 0, 
                                                        "Data4": 0, 
                                                        "Data5":0,
                                                        "Data6":0,
                                                        "Data7":0}, dtype=float64)))
        self.assertTrue(df.iloc[5].equals(Series(data={"timestamp": 0.268, 
                                                        "CAN_BUS": 1, 
                                                        "CAN_EXT": 0, 
                                                        "CAN_ID": 913, 
                                                        "CAN_LEN": 8, 
                                                        "Data0": 21, 
                                                        "Data1": 129, 
                                                        "Data2": 39, 
                                                        "Data3": 0, 
                                                        "Data4": 25, 
                                                        "Data5": 129,
                                                        "Data6": 38,
                                                        "Data7": 22}, dtype=float64)))

    def test_read_log_to_df_bad_lines(self):
        """ test reading a log file into a dataframe"""
        df, meta, continues = read_log_to_df("tests/test_data/test_data_bad_lines.log")
        self.assertEqual(continues, False)
        self.assertEqual(meta['unit_type'], "Test")
        self.assertEqual(meta['unit_number'], "Test")
        self.assertEqual(len(df), 9)
        self.assertTrue(df.iloc[0].equals(Series(data={"timestamp": 0.007, 
                                                        "CAN_BUS": 1, 
                                                        "CAN_EXT": 0, 
                                                        "CAN_ID": 785, 
                                                        "CAN_LEN": 8, 
                                                        "Data0": 1, 
                                                        "Data1": 0, 
                                                        "Data2": 0, 
                                                        "Data3": 0, 
                                                        "Data4": 0, 
                                                        "Data5":0,
                                                        "Data6":0,
                                                        "Data7":0}, dtype=float64)))
        self.assertTrue(df.iloc[8].equals(Series(data={"timestamp": 0.268, 
                                                        "CAN_BUS": 1, 
                                                        "CAN_EXT": 0, 
                                                        "CAN_ID": 913, 
                                                        "CAN_LEN": 8, 
                                                        "Data0": 21, 
                                                        "Data1": 129, 
                                                        "Data2": 39, 
                                                        "Data3": 0, 
                                                        "Data4": 25, 
                                                        "Data5": 129,
                                                        "Data6": 38,
                                                        "Data7": 22}, dtype=float64)))

    def test_Read_log_to_df_dat(self):
        """ test reading basic DAT file """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_dat.log")
        self.assertEqual(continues, False)
        self.assertEqual(meta['unit_type'], "test")
        self.assertEqual(meta['unit_number'], "test")
        self.assertEqual(meta['log_start_time'], "2022-05-23T17:12:22.597Z")
        self.assertEqual(meta['log_type'], "DAT0.1")
        self.assertEqual(len(df), 10)
        self.assertTrue(df.iloc[0].equals(Series(data={"timestamp": 8.543,
                                                        "CAN_BUS": 1, 
                                                        "CAN_EXT": 1,
                                                        "CAN_ID": 0x10B5B63F, 
                                                        "CAN_LEN": 6, 
                                                        "Data0": 0x54, 
                                                        "Data1": 0x8B, 
                                                        "Data2": 0xA7, 
                                                        "Data3": 0x15, 
                                                        "Data4": 0xD3, 
                                                        "Data5": 0x34,
                                                        "Data6": 0,
                                                        "Data7": 0}, dtype=float64)))
        self.assertTrue(df.iloc[9].equals(Series(data={"timestamp": 8.548,
                                                        "CAN_BUS": 1,
                                                        "CAN_EXT": 1, 
                                                        "CAN_ID": 0x72C0BCE, 
                                                        "CAN_LEN": 8, 
                                                        "Data0": 0xD2,
                                                        "Data1": 0x3A, 
                                                        "Data2": 0x26, 
                                                        "Data3": 0x61,
                                                        "Data4": 0x61,
                                                        "Data5": 0,
                                                        "Data6": 0,
                                                        "Data7": 0}, dtype=float64)))
        
    def tearDown(self):
        """ Remove all testing airports from the db. """
        connection = ENGINE.connect()
        # Must clear the test patient from the test database after the test
        connection.execute("DELETE FROM log_file;")
        connection.execute("DELETE FROM vehicle;")
        connection.close()