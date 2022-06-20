from unittest import TestCase
from pathlib import Path
from datetime import datetime

from pandas import Series, Float64Dtype
from numpy import float64

from helpers import dat_line_to_data, read_log_to_df, is_val_float, is_val_hex

from database import db_session, ENGINE
from database.models import LogFile, Vehicle

class LogConverterTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass
    
    def test_read_log_with_continuation(self):
        raise NotImplementedError

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

    def test_read_csv_no_type(self):
        raise NotImplementedError

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
                                                        "Data7": 0})))
        self.assertTrue(df.iloc[9].equals(Series(data={"timestamp": 8.548,
                                                        "CAN_BUS": 1,
                                                        "CAN_EXT": 1, 
                                                        "CAN_ID": 0x72C0BCE, 
                                                        "CAN_LEN": 5, 
                                                        "Data0": 0xD2,
                                                        "Data1": 0x3A, 
                                                        "Data2": 0x26, 
                                                        "Data3": 0x61,
                                                        "Data4": 0x61,
                                                        "Data5": 0,
                                                        "Data6": 0,
                                                        "Data7": 0})))

    def test_dat_line_to_data(self):
        line1 = "1234-1-100#12345678"
        line1_data = {"timestamp": 1234.0, "CAN_BUS": 1.0 ,"CAN_ID": "100", "CAN_EXT": 0.0, "CAN_LEN": 4,
                      "Data0": "12", "Data1": "34", "Data2": "56", "Data3": "78", "Data4": "00", "Data5": "00", "Data6": "00", "Data7": "00"}
        self.assertDictEqual(line1_data, dat_line_to_data(line1))

        
        line2 = "778933.456-3-FFF#1234567890AABBCC"
        line2_data = {"timestamp": 778933.456, "CAN_BUS": 3.0 ,"CAN_ID": "FFF", "CAN_EXT": 0.0, "CAN_LEN": 8,
                      "Data0": "12", "Data1": "34", "Data2": "56", "Data3": "78", "Data4": "90", "Data5": "AA", "Data6": "BB", "Data7": "CC"}
        self.assertDictEqual(line2_data, dat_line_to_data(line2))

        line3 = "778933.456-2-FFEC23#AC"
        line3_data = {"timestamp": 778933.456, "CAN_BUS": 2.0 ,"CAN_ID": "FFEC23", "CAN_EXT": 1.0, "CAN_LEN": 1,
                      "Data0": "AC", "Data1": "00", "Data2": "00", "Data3": "00", "Data4": "00", "Data5": "00", "Data6": "00", "Data7": "00"}
        self.assertDictEqual(line3_data, dat_line_to_data(line3))        
        
        line4 = "123.0-2-FFEC23#"
        line4_data = {"timestamp": 123.0, "CAN_BUS": 2.0 ,"CAN_ID": "FFEC23", "CAN_EXT": 1.0, "CAN_LEN": 0,
                      "Data0": "00", "Data1": "00", "Data2": "00", "Data3": "00", "Data4": "00", "Data5": "00", "Data6": "00", "Data7": "00"}
        self.assertDictEqual(line4_data, dat_line_to_data(line4))
        
        self.assertRaises(Exception, dat_line_to_data, "ac")# test random string should fail
        self.assertRaises(Exception, dat_line_to_data, "ac-1-123#1234") # test not number in timestamp
        self.assertRaises(Exception, dat_line_to_data, "123-A-100#00") # test no number in can bus number

    def test_is_val_hex(self):
        self.assertTrue(is_val_hex("AC"))
        self.assertTrue(is_val_hex("ac"))
        self.assertTrue(is_val_hex("12"))
        self.assertTrue(is_val_hex("00"))
        self.assertTrue(is_val_hex("99"))
        self.assertTrue(is_val_hex("1234"))
        self.assertTrue(is_val_hex("1234567890F"))
        self.assertTrue(is_val_hex("ABCDEF"))
        self.assertTrue(is_val_hex("FF"))
        self.assertTrue(is_val_hex("00FF"))
        self.assertTrue(is_val_hex("DEADBEEF"))
        self.assertTrue(is_val_hex("0 "))
        self.assertFalse(is_val_hex("Hey now brown cow"))
        self.assertFalse(is_val_hex("YOU"))
        self.assertFalse(is_val_hex("99  8"))
        self.assertFalse(is_val_hex("ACT"))

    def test_is_val_float(self):
        self.assertTrue(is_val_float("123"))
        self.assertTrue(is_val_float(" 123"))
        self.assertTrue(is_val_float("123 "))
        self.assertTrue(is_val_float("123.123212321"))
        self.assertFalse(is_val_float("  123  .  45"))
        self.assertTrue(is_val_float("4566"))
        self.assertTrue(is_val_float("0"))
        self.assertTrue(is_val_float("0100"))
        self.assertTrue(is_val_float("9990011"))
        self.assertFalse(is_val_float("ac"))
        self.assertFalse(is_val_float("123.56t"))
        self.assertFalse(is_val_float("123.56-"))
        self.assertFalse(is_val_float("!"))
        self.assertFalse(is_val_float("TD"))
        self.assertFalse(is_val_float("DEADBEEF"))

    def test_get_dbc_file_list(self):
        raise NotImplementedError

    def test_df_to_mf4(self):
        # likely can't test because don't want to construct an entirely new MF4
        # test by creating an MF4 from a DF and check its attributes
        raise NotImplementedError

    def tearDown(self):
        """ Remove all testing airports from the db. """
        connection = ENGINE.connect()
        # Must clear the test patient from the test database after the test
        connection.execute("DELETE FROM log_file;")
        connection.execute("DELETE FROM vehicle;")
        connection.close()