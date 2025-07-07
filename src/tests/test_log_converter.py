from curses import meta
import os
import shutil
from unittest import TestCase
from unittest.mock import patch, MagicMock
from pathlib import Path
from sqlalchemy import inspect

from asammdf import MDF

import pandas as pd

from database.crud import *
from database import ENGINE

from config import DATA_FOLDER
        
from helpers import read_log_to_df, get_dbc_file_list, df_to_mf4
from log_converter import get_files_to_process, create_unit_folders, archive_log, merge_continued_logs, setup_environment, save_mf4_files, process_log_file


class LogConverterTestCase(TestCase):
    """ Test importing data. """

    def setUp(self):
        """ Instantiate the test. """
        DATA_FOLDER = Path("tests/tmp")
        DATA_FOLDER.mkdir(parents=True, exist_ok=True)
        self.unit_output_folder = DATA_FOLDER / "unit_test_output"
        
        folders = ["in_logs", "in_logs/uploading", "out", "dbc"]
        self.subfolders = [DATA_FOLDER / x for x in folders]

        
        # Create target folders
        setup_environment(self.subfolders)
        create_unit_folders(self.unit_output_folder)

        # Copy the test dbc files to the dbc folder
        for dbc_file in get_dbc_file_list(Path("tests/test_data/dbc")):
            shutil.copy(dbc_file, DATA_FOLDER / "dbc" / dbc_file.name)
        

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
        self.assertListEqual(get_files_to_process(Path("tests/test_data")), ['test_data_all_good_lines.log','test_data_bad_lines.log','test_data_bad_timestamp.log','test_data_continues.log','test_data_dat.log','test_data_dat_continues.log','test_data_with_csv_logtype.log'])


    def test_merge_continued_logs(self):
        """ Test the merging of continued logs. """
        # This is a placeholder for the actual test implementation
        # You would need to create mock data and call merge_continued_logs
        pass


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

        # Process a log file
        file_name = "test_data_all_good_lines.log"
        shutil.copy(Path("tests/test_data") / file_name, self.subfolders[0] / file_name)

        global_dbc_files = [(f, 0) for f in get_dbc_file_list(DATA_FOLDER / "dbc")]
        
        result = process_log_file(file_name, global_dbc_files)

        # Check if the log file was processed correctly
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "processed")

        # check that the input file was moved to the processed folder
        processed_folder = self.subfolders[2] / "MM430/E00123"
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
        self.assertEqual(log.unit_number, "E00123")
        self.assertEqual(log.processing_status, "Processing Complete")
        self.assertEqual(log.original_file_name, file_name)
        self.assertEqual(log.length_sec, 1.127)
        self.assertEqual(log.samples, 6)
        self.assertEqual(log.log_start_time, parser.parse("2021-01-10T13:53:33.993Z").replace(tzinfo=None))

    def tearDown(self):
        """ Remove all testing airports from the db. """
        with ENGINE.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
        for folder in self.subfolders:
            shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(self.unit_output_folder, ignore_errors=True)
