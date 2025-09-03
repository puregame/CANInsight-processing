from curses import meta
import os
import shutil
from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path
from sqlalchemy import inspect

from dateutil import parser

from asammdf import MDF

import pandas as pd

from database.crud import *
from database import ENGINE

from config import DATA_FOLDER

from helpers import read_log_to_df, get_dbc_file_list, df_to_mf4
from log_converter import get_files_to_process, create_unit_folders, archive_log, merge_continued_logs, setup_environment, save_mf4_files, process_log_file, process_new_files


class LogConverterTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        DATA_FOLDER = Path("tests/tmp")
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        self.unit_output_folder = DATA_FOLDER / "out/test/test"
        
        folders = ["in_logs", "in_logs/uploading", "out", "dbc"]
        self.subfolders = [DATA_FOLDER / x for x in folders]

        self.test_data_files = ['test_data_all_good_lines.log','test_data_bad_lines.log','test_data_bad_timestamp.log','test_data_continues.log','test_data_continues1.log','test_data_continues1_different_unit_num.log','test_data_dat.log','test_data_dat_continues.log','test_data_dat_continues1.log','test_data_with_csv_logtype.log']
        
        # Create target folders
        setup_environment(self.subfolders)
        create_unit_folders(self.unit_output_folder)

        # Copy the test dbc files to the dbc folder
        for dbc_file in get_dbc_file_list(Path("tests/test_data/dbc")):
            shutil.copy(dbc_file, DATA_FOLDER / "dbc" / dbc_file.name)

        self.global_dbc_files = [(f, 0) for f in get_dbc_file_list(DATA_FOLDER / "dbc")]
        
    def test_create_unit_folders(self):
        """ Test the creation of unit folders. """
        # create unit folders called in setup, # but we can call it again to test
        create_unit_folders(self.unit_output_folder)

        self.assertTrue((self.unit_output_folder / "in_logs_processed").exists())
        self.assertTrue((self.unit_output_folder / "raw_logs").exists())

    def test_archive_log(self):
        """ Test the archiving of logs. """
        self.test_create_unit_folders() # create the necessary folders first
        
        #create a test log file
        test_log_file = self.unit_output_folder / "test_log.log"
        test_log_file.write_text("This is a test log file.")
        archive_log_file = self.unit_output_folder / "in_logs_processed/test_log.log"

        archive_log(test_log_file, archive_log_file)

        self.assertFalse(test_log_file.exists())
        self.assertTrue((archive_log_file).exists())
    
    def test_setup_environment(self):
        """ Test the setup of the environment. """
        #setup environment called in setUp, but we can call it again to test
        setup_environment(self.subfolders)

        # Check if the temp folder exists
        self.assertTrue(DATA_FOLDER.exists())
        for folder in self.subfolders:
            # Check if each subfolder was created
            self.assertTrue(folder.exists(), f"Folder {folder} was not created.")

        # Check that DB was initialized
        inspector = inspect(ENGINE)
        tables = inspector.get_table_names()
        self.assertIn('log_file', tables)  # replace with actual table name(s)
        self.assertIn('vehicle', tables)  # replace with actual table name(s)
        self.assertIn('log_comment', tables)  # replace with actual table name(s)

    def test_checksum(self):
        """ Test the checksum function on local files. """
        pass

    def test_get_files_to_process(self):
        self.assertListEqual(get_files_to_process(Path("tests/")), [])
        self.assertListEqual(get_files_to_process(Path("tests/test_data")), self.test_data_files)

    def test_merge_continued_logs_csv(self):
        """ Test the merging of continued logs. """
        
        # copy test log file to input folder
        file_names = ["test_data_continues.log", "test_data_continues1.log"]
        for file_name in file_names:
            shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name) 

        # Start the process, see if both show up in the output
        result = process_log_file(file_names[0], self.global_dbc_files)

        # Check that input files no longer exist in the input folder
        for file_name in file_names:
            self.assertFalse((self.subfolders[0] / file_name).exists(), f"Input file {file_name} still exists after processing.")

        log_db_entry = get_log_file(result['uuid'])
        print(log_db_entry)

        self.assertEqual(log_db_entry.unit_number, "test")
        self.assertEqual(log_db_entry.log_number, 1)
        self.assertEqual(log_db_entry.processing_status, "Processing Complete")
        self.assertEqual(log_db_entry.log_start_time, datetime(2021, 1, 10, 13, 53, 33, 993000))
        self.assertEqual(log_db_entry.log_end_time, datetime(2021, 1, 10, 13, 54, 36, 193000))
        self.assertEqual(log_db_entry.length_sec, 3.2)
        self.assertEqual(log_db_entry.samples, 6)

        # assert status in result is "processed"
        self.assertEqual(result['status'], "processed")
        self.assertEqual(result['multi_input_files'], True)
        #assert final log length is 6
        self.assertEqual(result['log_len'], 6)
        # assert output file name
        self.assertEqual(result['output_file_name'], f"test_00001")

        # assert that processed logs exist
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{result['output_file_name']}.log").exists())
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{result['output_file_name']}_cont01.log").exists())
        # assert that output logs exist
        self.assertTrue((self.unit_output_folder / f"{result['output_file_name']}.mf4").exists())
        # assert that raw logs exist
        self.assertTrue((self.unit_output_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4").exists())

        # open raw mf4 and check that there are 6 data frames
        raw_mf4 = MDF(self.unit_output_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4")
        self.assertGreater(len(list(raw_mf4.channels_db)), 0, "Raw MF4 file has no signals.")
        df = raw_mf4.to_dataframe()

        expected_ids = [0xCF62602, 0x18FFDD46, 0x3E1, 0xCF62602, 0x18FFDD46, 0x3E1]
        expected_data = [ [0x01,0x12,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x11,0x81,0x21,0x00,0x19,0x81,0x23,0x09],
            [0x81,0x28,0x81,0x56,0x81,0x1F,0x29,0x54],
            [0x01,0x12,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x11,0x81,0x21,0x00,0x19,0x81,0x23,0x09],
            [0x81,0x28,0x81,0x56,0x81,0x1F,0x29,0x54]]

        expected_dlcs = [5, 8, 8, 5, 8, 8]
        
        self.assertEqual(list(df["CAN_DataFrame.CAN_DataFrame.ID"]), expected_ids)
        for i, (expected_bytes, expected_dlc) in enumerate(zip(expected_data, expected_dlcs)):
            self.assertEqual(list(df["CAN_DataFrame.CAN_DataFrame.DataBytes"].iloc[i]), expected_bytes)
            self.assertEqual(df["CAN_DataFrame.CAN_DataFrame.DLC"].iloc[i], expected_dlc)

        # open output MF4 and check the data matches
        processed_mf4 = MDF(self.unit_output_folder / f"{result['output_file_name']}.mf4")
        self.assertEqual(len(list(processed_mf4.channels_db)), 0, "Processed MF4 file has more than zero signals.")
        
        # Clean up
        raw_mf4.close()
        processed_mf4.close()

    def test_merge_continued_logs_fails_unit_number(self):
        """ Test the merging of continued logs. """
        
        # copy test log file to input folder
        file_names = ["test_data_continues.log", "test_data_continues1_different_unit_num.log"]
        for file_name in file_names:
            shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name) 

        # Start the process, see if both show up in the output
        result = process_log_file(file_names[0], self.global_dbc_files)

        # Check that first input file does not exist, second one does
        self.assertFalse((self.subfolders[0] / file_names[0]).exists(), f"Input file {file_names[0]} still exists after processing.")
        self.assertTrue((self.subfolders[0] / file_names[1]).exists(), f"Input file {file_names[1]} does not exist after processing.")

        # assert status in result is "processed"
        self.assertEqual(result['status'], "processed")
        self.assertTrue(result['multi_input_files'])
        #assert final log length is 6
        self.assertEqual(result['log_len'], 3)
        # assert output file name
        self.assertEqual(result['output_file_name'], f"test_00001")

        # assert that processed logs exist
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{result['output_file_name']}.log").exists())
        # assert that output logs exist
        self.assertTrue((self.unit_output_folder / f"{result['output_file_name']}.mf4").exists())
        # assert that raw logs exist
        self.assertTrue((self.unit_output_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4").exists())

    def test_merge_continued_logs_dat(self):
        """ Test the merging of continued logs AND test processing of MF4 to physical values """
        
        # copy test log file to input folder
        file_names = ["test_data_dat_continues.log", "test_data_dat_continues1.log"]
        for file_name in file_names:
            shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name) 

        # Start the process, see if both show up in the output
        result = process_log_file(file_names[0], self.global_dbc_files)

        # Check that input files no longer exist in the input folder
        for file_name in file_names:
            self.assertFalse((self.subfolders[0] / file_name).exists(), f"Input file {file_name} still exists after processing.")

        # assert status in result is "processed"
        self.assertEqual(result['status'], "processed")
        #assert final log length is 6
        self.assertEqual(result['log_len'], 12)
        # assert output file name
        self.assertEqual(result['output_file_name'], f"test_00001")

        # assert that processed logs exist
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{result['output_file_name']}.log").exists())
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{result['output_file_name']}_cont01.log").exists())
        # assert that output logs exist
        self.assertTrue((self.unit_output_folder / f"{result['output_file_name']}.mf4").exists())
        # assert that raw logs exist
        self.assertTrue((self.unit_output_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4").exists())

        # open raw mf4 and check that there are 12 data frames
        raw_mf4 = MDF(self.unit_output_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4")
        self.assertGreater(len(list(raw_mf4.channels_db)), 0, "Raw MF4 file has no signals.")
        df = raw_mf4.to_dataframe()

        expected_ids = [0x3A] * 12
        expected_data = [
            [0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00],
            [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00]]

        expected_dlcs = [8] * 12
        self.assertEqual(len(df), 12)
        self.assertEqual(list(df["CAN_DataFrame.CAN_DataFrame.ID"]), expected_ids)
        for i, (expected_bytes, expected_dlc) in enumerate(zip(expected_data, expected_dlcs)):
            self.assertEqual(list(df["CAN_DataFrame.CAN_DataFrame.DataBytes"].iloc[i]), expected_bytes)
            self.assertEqual(df["CAN_DataFrame.CAN_DataFrame.DLC"].iloc[i], expected_dlc)

        # open output MF4 and check the data matches
        processed_mf4 = MDF(self.unit_output_folder / f"{result['output_file_name']}.mf4")
        self.assertGreater(len(list(processed_mf4.channels_db)), 0, "Processed MF4 file has zero signals.")
        df = processed_mf4.to_dataframe()
        expected_charge_relay = [1,0]*3 + [0]*6
        expected_discharge_relay = [1,0]*6
        expected_time = [0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0]
        self.assertEqual(len(df), 12)
        self.assertEqual(list(df.index), expected_time)
        self.assertEqual(list(df["ChargeRelay"]), expected_charge_relay)
        self.assertEqual(list(df["DischargeRelay"]), expected_discharge_relay)
        
        # Clean up
        raw_mf4.close()
        processed_mf4.close()

    def test_process_same_file_twice(self):
        """ Process one file twice, the second time it should do nothing and delete the input file."""

        file_name = "test_data_all_good_lines.log"
        shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name)

        # run the processing
        process_status = process_log_file(file_name, self.global_dbc_files)

        # copy again since input file got deleted
        file_name = "test_data_all_good_lines.log"
        shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name)

        # run the processing again
        process_status = process_log_file(file_name, self.global_dbc_files)
        self.assertEqual(process_status['status'], "duplicate")

        # Check that input files no longer exist in the input folder
        self.assertFalse((self.subfolders[0] / file_name).exists(), f"Input file {file_name} still exists after processing.")

        # check that the duplicate output exists in the archive folder
        self.assertEqual((self.unit_output_folder / "in_logs_processed/test_00001_duplicate.log").exists(), True)

    def test_process_new_files(self):
        """ Test full processing function """
        # copy test log file to input folder
        file_name = "test_data_all_good_lines.log"
        input_file = self.subfolders[0] / file_name
        shutil.copy(Path("tests/test_data") / file_name, input_file)

        # run the processing
        n_processed = process_new_files()
        self.assertEqual(n_processed, 1)

        # check that the input file was removed from the input folder
        self.assertFalse(input_file.exists(), "Input log file still exists in the input folder after processing.")

        # check that the line exists in the DB
        db_logs = get_all_logs_for_unit("test")
        print(db_logs)
        self.assertEqual(len(db_logs), 1)
        self.assertEqual(db_logs[0].unit_number, "test")
        self.assertEqual(db_logs[0].length_sec, 5.0)
        self.assertEqual(db_logs[0].log_start_time, parser.isoparse("2021-01-10T12:01:01.000"))
        self.assertEqual(db_logs[0].samples, 6)
        self.assertEqual(db_logs[0].log_end_time, parser.isoparse("2021-01-10T12:01:06.000"))

        # check that the files exist in the output folder

        # assert that processed logs exist
        self.assertTrue((self.unit_output_folder / "in_logs_processed" / f"{db_logs[0].file_stem}.log").exists())
        # assert that output logs exist
        self.assertTrue((self.unit_output_folder / f"{db_logs[0].file_stem}.mf4").exists())
        # assert that raw logs exist
        self.assertTrue((self.unit_output_folder / "raw_logs" / f"raw-{db_logs[0].file_stem}.mf4").exists())

    def test_save_mf4_files(self):
        """ Test saving data to MF4 format with mocks. """
        # get some data
        df, meta, continues = read_log_to_df(Path("tests/test_data/test_data_all_good_lines.log"))
        
        meta.update({"unit_output_folder": self.unit_output_folder, "log_num": 1, "file_stem": f"{meta['unit_number']}_{1:05d}"})


        # save the dataframe to MF4
        test_global_dbc_flles = [(f, 0) for f in get_dbc_file_list(DATA_FOLDER / "dbc")]
        save_mf4_files(df, meta, test_global_dbc_flles)

        # check that all MF4s saved to the correct folder
        raw_output_file = self.unit_output_folder / f"raw_logs/raw-{meta['file_stem']}.mf4"
        processed_output_file = self.unit_output_folder / f"{meta['file_stem']}.mf4"

        self.assertTrue(raw_output_file.exists())
        self.assertTrue(processed_output_file.exists())

        # open the mf4 files and check that they have the correct data
        
        # Open and validate MF4 content
        raw_mf4 = MDF(raw_output_file)

        self.assertGreater(len(list(raw_mf4.channels_db)), 0, "Raw MF4 file has no signals.")

        #check that the raw MF4 contains the expected signals
        raw_signals = [sig for sig in raw_mf4.channels_db]        
        self.assertTrue(any("CAN" in s for s in raw_signals), "No CAN signals in raw MF4.")
        self.assertIn("Timestamp", raw_signals, "Timestamp signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame", raw_signals, "CAN_DataFrame signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame.ID", raw_signals, "CAN_DataFrame.ID signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame.IDE", raw_signals, "CAN_DataFrame.IDE signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame.DLC", raw_signals, "CAN_DataFrame.DLC signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame.DataLength", raw_signals, "CAN_DataFrame.DataLength signal not found in raw MF4.")
        self.assertIn("CAN_DataFrame.DataBytes", raw_signals, "CAN_DataFrame.DataBytes signal not found in raw MF4.")
        df = raw_mf4.to_dataframe()
        self.assertEqual(len(df), 6, "Raw MF4 file does not contain the expected number of rows.")


        # Check processed MF4 content
        processed_mf4 = MDF(processed_output_file)
        self.assertGreater(len(list(processed_mf4.channels_db)), 0, "Processed MF4 file has no signals.")
        processed_signals = [sig for sig in processed_mf4.channels_db]
        self.assertTrue(any("CAN" in s for s in processed_signals), "No CAN signals in processed MF4.")
        self.assertIn("CAN1.BMS1.ChargeRelay", processed_signals, "Processed MF4 does not contain 'CAN1.BMS1.ChargeRelay' signal.")
        self.assertIn("CAN1.BMS1.DischargeRelay", processed_signals, "Processed MF4 does not contain 'CAN1.BMS1.DischargeRelay' signal.")
        self.assertIn("CAN1.BMS1.ChargeRelay", processed_signals, "Processed MF4 does not contain 'CAN1.BMS1.ChargeRelay' signal.")
        self.assertIn("time", processed_signals, "Processed MF4 does not contain 'time' signal.")
        
        df = processed_mf4.to_dataframe()
        self.assertEqual(len(df), 3, "Processed MF4 file does not contain the expected number of rows.")

        # Clean up
        raw_mf4.close()
        processed_mf4.close()

    def test_process_log_file_good(self):
        """ Test processing a log file. """

        file_name = "test_data_all_good_lines.log"
        shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name) # copy test log file to input folder
        
        result = process_log_file(file_name, self.global_dbc_files)

        # Check if the log file was processed correctly
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "processed")

        # check that the input file was moved to the processed folder
        processed_folder = self.subfolders[2] / "test/test"
        self.assertTrue(processed_folder.exists(), "Processed folder does not exist.")
        processed_file = processed_folder / f"{result['output_file_name']}.mf4"
        self.assertTrue(processed_file.exists(), "Processed log file does not exist.")

        # check that the input file was removed from the input folder
        input_file = self.subfolders[0] / file_name
        self.assertFalse(input_file.exists(), "Input log file still exists in the input folder.")

        # check if raw file exists in the output folder
        raw_output_file = processed_folder / "raw_logs" / f"raw-{result['output_file_name']}.mf4"
        self.assertTrue(raw_output_file.exists(), "Raw output file does not exist.")

        # check if the in log was moved to the processed folder
        in_log_processed_folder = processed_folder / "in_logs_processed"
        self.assertTrue(in_log_processed_folder.exists(), "In logs processed folder does not exist.")
        in_log_processed_file = in_log_processed_folder / f"{result['output_file_name']}.log"
        self.assertTrue(in_log_processed_file.exists(), "In log processed file does not exist.")

        # check if log exists in the database
        log = get_log_file(result["uuid"])
        self.assertEqual(log.unit_number, "test")
        self.assertEqual(log.processing_status, "Processing Complete")
        self.assertEqual(log.original_file_name, file_name)
        self.assertEqual(log.length_sec, 5)
        self.assertEqual(log.samples, 6)
        self.assertEqual(log.log_start_time, parser.parse("2021-01-10T12:01:01.0000Z").replace(tzinfo=None))

    def tearDown(self):
        """ Remove all testing data from the db. """
        with ENGINE.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
        for folder in self.subfolders:
            shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(self.unit_output_folder, ignore_errors=True)
