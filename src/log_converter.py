from database import *

import os
import time
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from pathlib import Path
import json
from itertools import repeat

from helpers import read_log_to_df, get_dbc_file_list, tail, df_to_mf4

from config import DATA_FOLDER
from database.crud import *

from log_logger import logger

input_files = DATA_FOLDER / "in_logs/"
input_files.mkdir(exist_ok=True)
output_files = DATA_FOLDER / "out/"
output_files.mkdir(exist_ok=True)
dbc_folder = DATA_FOLDER / 'dbc/'
dbc_folder.mkdir(exist_ok=True)

def create_unit_folders(unit_output_folder):
    unit_output_folder.mkdir(parents=True, exist_ok=True)
    (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)

def get_new_log_filename(log_start_time, file_name):
    # get new file name for this log
    if parser.parse(log_start_time) < datetime(year=2020, month=2, day=1, hour=1, tzinfo=pytz.UTC):
        # if the start time is before 2020 then we know the time for this file is not correct!
        new_file_name = file_name
        logger.warning("CAN log {} does not have a proper start timestamp, using log file name for output file".format(new_file_name))
    else:
        new_file_name = "{}".format(log_start_time.replace(":", "-").replace(".","-"))
    return new_file_name

def read_files_recursive(files_to_process):
    this_file = files_to_process.pop(0)
    logger.info("Starting processing for file name: {}".format(this_file))
    df, meta, continues = read_log_to_df(input_files / this_file)
    meta['unit_output_folder'] = output_files/meta['unit_type']/meta['unit_number']
    create_unit_folders(meta['unit_output_folder'])
    meta['file_name'] = this_file
    meta['len'] = len(df)

    new_file_name = get_new_log_filename(meta['log_start_time'], meta['file_name'])

    create_log_in_database_if_not_exists(meta['log_start_time'], meta['unit_number'], meta['unit_type'])
    # Move input log file to storage folder
    update_log_file_status(meta['log_start_time'], meta['unit_number'], "LOG file Moved")
    logger.info("Renaming file from {} to {}".format(input_files/this_file, meta['unit_output_folder']/"in_logs_processed"/"{}.log".format(new_file_name)))
    os.rename(input_files/this_file, meta['unit_output_folder']/"in_logs_processed"/"{}.log".format(new_file_name))

    # if there is no log data then skip remaining processing
    if meta['len'] == 0:  
        meta['log_end_time'] = meta['log_start_time']
        return df, meta

    start_time = parser.parse(meta['log_start_time'])
    log_len_seconds = df.iloc[-1,0]
    meta['log_len_seconds'] = log_len_seconds
    end_time = start_time + timedelta(seconds=log_len_seconds)
    meta['log_end_time'] = end_time

    if continues:
        logger.info("Log file: {} continues to next file".format(this_file))
        next_df, next_meta = read_files_recursive(files_to_process)
        next_start_time = parser.parse(next_meta['log_start_time'])

        # if second log starts more than 10 seconds after first log, thorw a warning
        if (start_time + timedelta(seconds=(log_len_seconds + 10))) < next_start_time:
            logger.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 10 seconds before first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))

        # if second log starts before end of first log, thorw a warning
        if end_time > next_start_time:
            logger.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 1 seconds after first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))

        next_df['timestamp'] = next_df.timestamp + log_len_seconds
        df = df.append(next_df)
        meta['len'] = meta['len'] + next_meta['len']
        update_log_file_status(next_meta['log_start_time'], next_meta['unit_number'], "Combined With Earlier LOG") # for each continues file remove the latest file from the DB
        meta['log_end_time'] = next_meta['log_end_time'] # new end time is end time of next log
    return df, meta

def process_new_files():
    logger.debug("Looking for new CAN Log files to process")
    files_to_process = [k for k in os.listdir(input_files) if ('.log' in k) or ('.LOG' in k)]
    files_to_process.sort()
    logger.debug("Data files: {}".format(files_to_process))

    global_dbc_files = list(get_dbc_file_list(dbc_folder))
    while len(files_to_process) > 0:
        df, meta = read_files_recursive(files_to_process)
        if is_log_status(meta['log_start_time'], meta['unit_number'], "Uploading"):
            # do nothing, log is still uploading and should not be processed
            continue
        if meta['len'] == 0:
            update_log_file_len(meta['log_start_time'], meta['unit_number'], 0, 0)
            update_log_file_status(meta['log_start_time'], meta['unit_number'], "Zero Data") 
            continue # do not process logs that have zero length
        
        update_log_file_len(meta['log_start_time'], meta['unit_number'], meta['log_len_seconds'], len(df))
        
        # todo: store meta data in mf4 file!
        mf4 = df_to_mf4(df)
        # mf4.attach(str(meta).encode('utf-8'))

        new_file_name = get_new_log_filename(meta['log_start_time'], meta['file_name'])
        mf4.save(meta['unit_output_folder'] / "raw-{}.mf4".format(new_file_name))
        update_log_file_status(meta['log_start_time'], meta['unit_number'], "Saved Raw MF4")
        unit_type_dbc_files = list(get_dbc_file_list(dbc_folder/meta['unit_type']))
        all_dbc_files = unit_type_dbc_files+global_dbc_files
        all_dbc_files = list(zip(all_dbc_files, repeat(0)))

        mf4_extract = mf4.extract_bus_logging({"CAN": all_dbc_files})
        mf4_extract.save(meta['unit_output_folder'] / "extracted-{}.mf4".format(new_file_name))
        update_log_file_status(meta['log_start_time'], meta['unit_number'], "Saved extracted MF4")
    logger.info("*EXPORT COMPELTE*")

if __name__ == "__main__":
    while(True):
        print("Processing new files")
        process_new_files()
        time.sleep(120)