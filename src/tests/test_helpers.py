from unittest import TestCase
from pathlib import Path, PosixPath
from datetime import datetime

from pandas import Series
import numpy as np

from helpers import dat_line_to_data, df_to_mf4, read_log_to_df, is_val_float, is_val_hex, get_dbc_file_list


class LogHelperTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        pass
    
    def test_read_log_with_continuation(self):
        df, meta, continues = read_log_to_df("tests/test_data/test_data_dat_continues.log")
        self.assertTrue(continues)
        df, meta, continues = read_log_to_df("tests/test_data/test_data_continues.log")
        self.assertTrue(continues)

    def test_log_multiple_continues(self):
        pass # todo: test multiple continues, this is not implemented yet

    def test_read_log_with_bad_timestamp(self):
        """ test reading basic CSV with bad timestamp, lines should be ignored"""
        df, meta, continues = read_log_to_df("tests/test_data/test_data_bad_timestamp.log")
        self.assertFalse(continues)
        self.assertEqual(len(df), 4)

    def test_read_csv_with_type(self):
        """ test reading basic CSV style log file with log type in meta """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_with_csv_logtype.log")
        self.assertFalse(continues)
        self.assertEqual(len(df), 6)
        self.assertIn("log_type", meta)
        self.assertEqual(meta['log_type'], "CSV0.1")

    def test_read_csv_no_type(self):
        pass
        # this test case is in other tests, test_data_all_good_lines, test_data_bad_lines
        #  both have no type in metadata 

    def test_read_log_to_df_good_csv(self):
        """ test reading basic CSV style log file with no log type in meta """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_all_good_lines.log")
        self.assertFalse(continues)
        self.assertEqual(meta['unit_type'], "test")
        self.assertEqual(meta['unit_number'], "test")
        self.assertEqual(meta['can_1']['bus_name'], "Main")
        self.assertEqual(len(df), 6)
        self.assertTrue(df.iloc[0].equals(Series(data={"timestamp": 0.000, 
                                                        "CAN_BUS": 1, 
                                                        "CAN_EXT": 1, 
                                                        "CAN_ID": 0x18FFDD46, 
                                                        "CAN_LEN": 8, 
                                                        "Data0": 0x11, 
                                                        "Data1": 0x81, 
                                                        "Data2": 0x21, 
                                                        "Data3": 0x00, 
                                                        "Data4": 0x19, 
                                                        "Data5": 0x81,
                                                        "Data6": 0x23,
                                                        "Data7": 0x09}, dtype=np.float64)))
        self.assertTrue(df.iloc[5].equals(Series(data={"timestamp": 5.000, 
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
                                                        "Data7":0}, dtype=np.float64)))
        self.assertTrue(df.iloc[4].equals(Series(data={"timestamp": 4.000, 
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
                                                        "Data7": 22}, dtype=np.float64)))

    def test_read_log_to_df_bad_lines(self):
        """ test reading a log file into a dataframe"""
        df, meta, continues = read_log_to_df("tests/test_data/test_data_bad_lines.log")
        self.assertFalse(continues)
        self.assertEqual(meta['unit_type'], "test")
        self.assertEqual(meta['unit_number'], "test")
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
                                                        "Data7":0}, dtype=np.float64)))
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
                                                        "Data7": 22}, dtype=np.float64)))

    def test_Read_log_to_df_dat(self):
        """ test reading basic DAT file """
        df, meta, continues = read_log_to_df("tests/test_data/test_data_dat.log")
        self.assertFalse(continues)
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
        self.assertRaises(FileNotFoundError, get_dbc_file_list, Path("some_folder_that_does_not_exist"))
        self.assertListEqual(list(get_dbc_file_list(Path("tests/"))), []) # look in folder with not files
        self.assertListEqual(list(get_dbc_file_list(Path("tests/test_data"))), [PosixPath('tests/test_data/test.dbc')]) # look in folder with files and a dbc

    def test_df_to_mf4(self):
        # test by creating an MF4 from a DF and check its attributes
        df, meta, continues = read_log_to_df("tests/test_data/test_data_bad_lines.log")

        mf4 = df_to_mf4(df)
        self.assertEqual(mf4.version, "4.11")
        self.assertRaises(KeyError, mf4.get_group, 1) # should be only group 0
        can_group = mf4.get_group(0)
        self.assertListEqual(list(mf4.get_group(0).columns), ['CAN_DataFrame.CAN_DataFrame.BusChannel', 'CAN_DataFrame.CAN_DataFrame.ID', 'CAN_DataFrame.CAN_DataFrame.IDE', 'CAN_DataFrame.CAN_DataFrame.DLC', 'CAN_DataFrame.CAN_DataFrame.DataLength', 'CAN_DataFrame.CAN_DataFrame.DataBytes', 'CAN_DataFrame.CAN_DataFrame.Dir', 'CAN_DataFrame.CAN_DataFrame.EDL', 'CAN_DataFrame.CAN_DataFrame.BRS'])
        self.assertListEqual(list(mf4.get_group(0).index), [0.0, 0.06899999999999999, 0.09999999999999999, 0.103, 0.22899999999999998, 0.261])
        first_item =  list(can_group.iloc[0])
        self.assertListEqual(first_item[:5], [1, 913, 0, 8, 8])
        for a,b in zip(first_item[5], [ 20, 129,  70,   0,  25, 129,  71,  85]):
            self.assertEqual(a,b)
        self.assertListEqual(first_item[6:], [0,0,0])

    def tearDown(self):
        """ Remove all testing airports from the db. """
        pass