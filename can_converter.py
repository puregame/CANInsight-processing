import os
import logging
import time
from datetime import timedelta
from dateutil import parser
from pathlib import Path

from helpers import read_log_to_df, get_dbc_file_list, tail, df_to_mf4

logging.basicConfig(filename='./data/can_processing.log', level=logging.DEBUG, #, encoding='utf-8'
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

input_files = Path("./data/in_logs/")
output_files = Path("./data/out/")
dbc_folder = Path('./data/dbc/')

def read_files_recursive(files_to_process):
    this_file = files_to_process.pop(0)
    df, meta, continues = read_log_to_df(input_files / this_file)
    
    #todo: following three lines should be function
    unit_output_folder = output_files/meta['unit_type']/meta['unit_number']
    unit_output_folder.mkdir(parents=True, exist_ok=True)
    (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)
    
    new_file_name = "{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"))
    os.rename(input_files/this_file, unit_output_folder/"in_logs_processed"/"{}.log".format(new_file_name))
    meta['file_name'] = this_file

    if continues:
        logging.info("Log file: {} continues to next file".format(this_file))
        start_time = parser.parse(meta['log_start_time'])
        first_log_len_seconds = df.iloc[-1,0]
        next_df, next_meta = read_files_recursive(files_to_process)
        next_start_time = parser.parse(next_meta['log_start_time'])

        # if second log starts more than 10 seconds after first log, thorw a warning
        if (start_time + timedelta(seconds=(first_log_len_seconds + 10))) < next_start_time:
            logging.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 10 seconds before first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))
        # if second log starts before end of first log, thorw a warning
        if (start_time + timedelta(seconds=(first_log_len_seconds))) > next_start_time:
            logging.warning("Warning: continued logs for type {unit_type} unit {unit_number}, last entry of {log_start_time} \
                            is more than 1 seconds after first entry of {second_time}"\
                            .format(second_time=next_meta['log_start_time'], **meta))

        next_df['timestamp'] = next_df.timestamp + first_log_len_seconds
        df = df.append(next_df)
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
        new_file_name = "{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"))
        unit_output_folder = output_files/meta['unit_type']/meta['unit_number']
        unit_output_folder.mkdir(parents=True, exist_ok=True)
        (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)

        mf4.save(unit_output_folder / "raw-{}.mf4".format(new_file_name))
        unit_type_dbc_files = list(get_dbc_file_list(dbc_folder/meta['unit_type']))

        mf4_extract = mf4.extract_bus_logging({"CAN": unit_type_dbc_files+global_dbc_files})
        mf4_extract.save(unit_output_folder / "extracted-{}.mf4".format(new_file_name))
    logging.debug("*EXPORT COMPELTE*")

while(True):
    process_new_files()
    time.sleep(10)