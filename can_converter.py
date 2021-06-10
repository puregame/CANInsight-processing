import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
from helpers import read_log_to_mf4, get_dbc_file_list
from pathlib import Path
import logging
import os
import time

logging.basicConfig(filename='/data/can_processing.log', encoding='utf-8', level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

input_files = Path("/data/in_logs/")
output_files = Path("/data/out/")
dbc_folder = Path('/data/dbc/')

def process_new_files():
    logging.debug("Looking for new CAN Log files to process")
    files_to_process = os.listdir(input_files)
    logging.debug("input data files: {}".format(files_to_process))

    global_dbc_files = list(get_dbc_file_list(dbc_folder))

    for file in files_to_process:
        file_name = file.replace(".log", "")
        logging.debug("Processing file: {}".format(file_name))

        mf4, meta = read_log_to_mf4(input_files / file)
        new_file_name = "{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"))
        unit_output_folder = output_files/meta['unit_type']/meta['unit_number']
        unit_output_folder.mkdir(parents=True, exist_ok=True)
        (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)

        mf4.save(unit_output_folder / "raw-{}.mf4".format(new_file_name))
        unit_type_dbc_files = list(get_dbc_file_list(dbc_folder/meta['unit_type']))

        mf4_extract = mf4.extract_bus_logging({"CAN": unit_type_dbc_files+global_dbc_files})
        mf4_extract.save(unit_output_folder / "extracted-{}.mf4".format(new_file_name))
        os.rename(input_files/file, unit_output_folder/"in_logs_processed"/"{}.log".format(new_file_name))
    logging.debug("*EXPORT COMPELTE*")

while(True):
    process_new_files()
    time.sleep(10)