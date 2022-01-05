from database import *

import os
import logging
import time
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from pathlib import Path
import json
from itertools import repeat

from helpers import read_log_to_df, get_dbc_file_list, tail, df_to_mf4

home_folder = Path("/data")

logging.basicConfig(filename=home_folder/'can_processing.log', level=logging.DEBUG, #, encoding='utf-8'
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


input_files = home_folder / "in_logs/"
output_files = home_folder / "out/"
dbc_folder = home_folder / 'dbc/'

def read_files_recursive(files_to_process):
    this_file = files_to_process.pop(0)
    df, meta, continues = read_log_to_df(input_files / this_file)
    meta['file_name'] = this_file

    if len(df) == 0:
        # nothing else to do
        meta['log_end_time'] = meta['log_start_time']
        return df, meta

    start_time = parser.parse(meta['log_start_time'])
    log_len_seconds = df.iloc[-1,0]
    end_time = start_time + timedelta(seconds=log_len_seconds)
    meta['log_end_time'] = end_time
    
    #todo: following three lines should be function
    unit_output_folder = output_files/meta['unit_type']/meta['unit_number']
    unit_output_folder.mkdir(parents=True, exist_ok=True)
    (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)
    
    # todo: make log file nameing a function
    if parser.parse(meta['log_start_time']) < datetime(year=2020, month=2, day=1, hour=1, tzinfo=pytz.UTC):
        # if the start time is before 2020 then we know the time for this file is not correct!
        new_file_name = meta['file_name']
        logging.warning("CAN log {} does not have a proper start timestamp, using log file name for output file".format(new_file_name))
    else:
        new_file_name = "{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"))
    logging.info("Renaminf file from {} to {}".format(input_files/this_file, unit_output_folder/"in_logs_processed"/"{}.log".format(new_file_name)))
    os.rename(input_files/this_file, unit_output_folder/"in_logs_processed"/"{}.log".format(new_file_name))

    if continues:
        logging.info("Log file: {} continues to next file".format(this_file))
       
        next_df, next_meta = read_files_recursive(files_to_process)
        next_start_time = parser.parse(next_meta['log_start_time'])

        # if second log starts more than 10 seconds after first log, thorw a warning
        if (start_time + timedelta(seconds=(log_len_seconds + 10))) < next_start_time:
            logging.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 10 seconds before first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))
        # if second log starts before end of first log, thorw a warning
        if end_time > next_start_time:
            logging.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 1 seconds after first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))

        next_df['timestamp'] = next_df.timestamp + log_len_seconds
        df = df.append(next_df)
        meta['log_end_time'] = next_meta['log_end_time'] # new end time is end time of next log
    return df, meta


def process_new_files():
    logging.debug("Looking for new CAN Log files to process")
    files_to_process = [k for k in os.listdir(input_files) if ('.log' in k) or ('.LOG' in k)]
    logging.debug("input data files: {}".format(files_to_process))

    global_dbc_files = list(get_dbc_file_list(dbc_folder))
    while len(files_to_process) > 0:
        df, meta = read_files_recursive(files_to_process)
        # todo: store meta data in mf4 file!
        mf4 = df_to_mf4(df)
        # mf4.attach(str(meta).encode('utf-8'))

        if parser.parse(meta['log_start_time']) < datetime(year=2020, month=2, day=1, hour=1, tzinfo=pytz.UTC):
            # if the start time is before 2020 then we know the time for this file is not correct!
            new_file_name = meta['file_name']
        else:
            new_file_name = "{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"))

        unit_output_folder = output_files/meta['unit_type']/meta['unit_number']
        unit_output_folder.mkdir(parents=True, exist_ok=True)
        (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)

        mf4.save(unit_output_folder / "raw-{}.mf4".format(new_file_name))
        unit_type_dbc_files = list(get_dbc_file_list(dbc_folder/meta['unit_type']))
        all_dbc_files = unit_type_dbc_files+global_dbc_files
        all_dbc_files = list(zip(all_dbc_files, repeat(0)))

        mf4_extract = mf4.extract_bus_logging({"CAN": all_dbc_files})
        mf4_extract.save(unit_output_folder / "extracted-{}.mf4".format(new_file_name))
    logging.debug("*EXPORT COMPELTE*")

while(True):
    process_new_files()
    time.sleep(10)