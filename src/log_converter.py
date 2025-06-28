import os
import time
from datetime import datetime, timedelta
from dateutil import parser
import pytz
from pathlib import Path
import json
from itertools import repeat

from log_converter_logger import logger

from database import *
from database.upgrade import init_and_upgrade_db

from helpers import read_log_to_df, get_dbc_file_list, tail, df_to_mf4

from config import DATA_FOLDER
from database.crud import *

INPUT_FILES = DATA_FOLDER / "in_logs/"
INPUT_FILES_UPLOAD = DATA_FOLDER / "in_logs/uploading"
OUTPUT_FILES = DATA_FOLDER / "out/"
DBC_FOLDER = DATA_FOLDER / 'dbc/'

SUBFOLDERS = [INPUT_FILES, INPUT_FILES_UPLOAD, OUTPUT_FILES, DBC_FOLDER]

def setup_environment():
    for folder in SUBFOLDERS:
        folder.mkdir(parents=True, exist_ok=True)
    init_and_upgrade_db()


def create_unit_folders(unit_output_folder: Path):
    (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)
    (unit_output_folder/"raw_logs/").mkdir(parents=True, exist_ok=True)

def get_new_log_filename(log_start_time: str, file_name: str) -> str:
    try:
        ts = parser.parse(log_start_time)
        if ts < datetime(2020, 2, 1, tzinfo=pytz.UTC):
            # if the start time is before 2020 then we know the time for this file is not correct!
            raise ValueError("Timestamp too early")
        # return ts.strftime("%Y-%m-%dT%H-%M-%S")
        return "{}".format(log_start_time.replace(":", "-").replace(".","-"))
    except ValueError:
        logger.warning("Invalid log timestamp for file %s, using original file name", file_name)
        return file_name

def get_files_to_process(folder: Path) -> list[str]:
    return sorted([f for f in os.listdir(folder) if f.lower().endswith('.log')])


def process_log_file(file_name: str, global_dbc_files: list[tuple[Path, int]]) -> None:
    logger.info("Starting processing for file: %s", file_name)
    df, meta, continues = read_log_to_df(INPUT_FILES / file_name)

    meta['unit_output_folder'] = OUTPUT_FILES / meta['unit_type'] / meta['unit_number']
    create_unit_folders(meta['unit_output_folder'])
    meta['file_name'] = file_name
    meta['len'] = len(df)

    new_file_name = get_new_log_filename(meta['log_start_time'], meta['file_name'])

    if does_log_exist(meta['log_start_time'], meta['unit_number']):
        # the log already exiss

    create_log_in_database_if_not_exists(meta['log_start_time'], meta['unit_number'], meta['unit_type'], original_file_name=file_name)
    update_log_file_status(meta['log_start_time'], meta['unit_number'], "LOG file Moved")

    original_path = INPUT_FILES / file_name
    archived_path = meta['unit_output_folder'] / "in_logs_processed" / f"{new_file_name}.log"
    original_path.rename(archived_path)

    if meta['len'] == 0:
        meta['log_end_time'] = meta['log_start_time']
        update_log_file_len(meta['log_start_time'], meta['unit_number'], 0, 0)
        update_log_file_status(meta['log_start_time'], meta['unit_number'], "Zero Data")
        return

    start_time = parser.parse(meta['log_start_time'])
    log_len_seconds = df.iloc[-1, 0]
    meta['log_len_seconds'] = log_len_seconds
    meta['log_end_time'] = start_time + timedelta(seconds=log_len_seconds)

    while continues:
        files_remaining = get_files_to_process(INPUT_FILES)
        try:
            next_idx = files_remaining.index(file_name) + 1
            next_file = files_remaining[next_idx]
        except (ValueError, IndexError):
            logger.warning("Could not find next continued file after %s", file_name)
            break

        next_df, next_meta, continues = read_log_to_df(INPUT_FILES / next_file)
        next_start_time = parser.parse(next_meta['log_start_time'])

        if meta['log_end_time'] + timedelta(seconds=10) < next_start_time:
            logger.warning("Gap between logs too large for unit %s", meta['unit_number'])
        if meta['log_end_time'] > next_start_time:
            logger.warning("Overlap between logs for unit %s", meta['unit_number'])

        # Offset and combine
        next_df['timestamp'] += meta['log_len_seconds']
        df = df.append(next_df, ignore_index=True)

        # Update cumulative meta
        meta['log_len_seconds'] += next_meta['log_len_seconds']
        meta['len'] += next_meta['len']
        meta['log_end_time'] = parser.parse(next_meta['log_end_time'])

        update_log_file_status(next_meta['log_start_time'], next_meta['unit_number'], "Combined With Earlier LOG")

        # Archive the continued file
        new_continued_name = get_new_log_filename(next_meta['log_start_time'], next_meta['file_name'])
        archived_path = meta['unit_output_folder'] / "in_logs_processed" / f"{new_continued_name}.log"
        (INPUT_FILES / next_file).rename(archived_path)

    update_log_file_len(meta['log_start_time'], meta['unit_number'], meta['log_len_seconds'], len(df))

    mf4 = df_to_mf4(df)
    del df
    mf4_file = meta['unit_output_folder'] / f"raw_logs/raw-{new_file_name}.mf4"
    mf4.save(mf4_file)
    update_log_file_status(meta['log_start_time'], meta['unit_number'], "Saved Raw MF4")

    try:
        unit_dbc_files = list(get_dbc_file_list(DBC_FOLDER / meta['unit_type']))
    except FileNotFoundError:
        logger.warning("No DBC files found for unit type: %s", meta['unit_type'])
        unit_dbc_files = []

    all_dbc_files = [(f, 0) for f in unit_dbc_files + [f for f, _ in global_dbc_files]]
    mf4_extract = mf4.extract_bus_logging({"CAN": all_dbc_files})
    mf4_extract.save(meta['unit_output_folder'] / f"extracted-{new_file_name}.mf4")
    update_log_file_status(meta['log_start_time'], meta['unit_number'], "Saved extracted MF4")

def process_new_files():
    logger.debug("Looking for new CAN Log files to process")
    files_to_process = get_files_to_process(INPUT_FILES)
    logger.debug("Found files: %s", files_to_process)

    global_dbc_files = [(f, 0) for f in get_dbc_file_list(DBC_FOLDER)]

    for file_name in files_to_process:
        if is_log_status(parser.parse("2000-01-01"), "unknown", "Uploading"):
            continue
        process_log_file(file_name, global_dbc_files)

    logger.info("*EXPORT COMPLETE*")

if __name__ == "__main__":
    setup_environment()
    try:
        while True:
            logger.info("Processing new files")
            process_new_files()
            time.sleep(120)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
