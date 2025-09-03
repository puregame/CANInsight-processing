import os
import time
from datetime import timedelta
from dateutil import parser
from pathlib import Path
import hashlib
import pandas as pd

from log_converter_logger import logger

from database import *
from database.upgrade import init_and_upgrade_db

from helpers import read_log_to_df, get_dbc_file_list, df_to_mf4

from config import DATA_FOLDER, SLEEP_TIME_BETWEEN_PROCESSINGS
from database.crud import *

INPUT_FILES = DATA_FOLDER / "in_logs/"
INPUT_FILES_UPLOAD = DATA_FOLDER / "in_logs/uploading"
OUTPUT_FILES = DATA_FOLDER / "out/"
DBC_FOLDER = DATA_FOLDER / "dbc/"

SUBFOLDERS = [INPUT_FILES, INPUT_FILES_UPLOAD, OUTPUT_FILES, DBC_FOLDER]

def setup_environment(subfolders: list[Path] = SUBFOLDERS):
    for folder in subfolders:
        folder.mkdir(parents=True, exist_ok=True)
    init_and_upgrade_db()


def create_unit_folders(unit_output_folder: Path):
    (unit_output_folder/"in_logs_processed/").mkdir(parents=True, exist_ok=True)
    (unit_output_folder/"raw_logs/").mkdir(parents=True, exist_ok=True)


def get_files_to_process(folder: Path) -> list[str]:
    return sorted([f for f in os.listdir(folder) if f.lower().endswith('.log')])


def archive_log(original_path: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.rename(target_path)


def merge_continued_logs(initial_df: pd.DataFrame, initial_meta: dict, initial_continues: bool, file_name: str, global_dbc_files: list[tuple[Path, int]]) -> tuple:
    df = initial_df
    meta = initial_meta
    continues = initial_continues
    n_continuation = 0

    while continues:
        n_continuation += 1
        # get all files that are left to process, file that we want is alwasys the first one
        files_remaining = get_files_to_process(INPUT_FILES)
        logger.info("Merging continued log %s into %s", files_remaining[0], file_name)

        next_df, next_meta, continues = read_log_to_df(INPUT_FILES / files_remaining[0])

        # compare unit types and unit numbers, if they are different do not process the next file
        if (meta['unit_number'] != next_meta['unit_number']) or (meta['unit_type'] != next_meta['unit_type']):
            logger.warning("Continuation Error: Unit number or type mismatch for next log after %s", meta['uuid'])
            continues = False
            return df, meta

        next_meta['log_len_seconds'] = next_df.iloc[-1, 0]
        logger.info("Extending original log length seconds from %d by %d", meta['log_len_seconds'], next_meta['log_len_seconds'])
        start_time = parser.parse(next_meta['log_start_time'])
        next_meta['log_end_time'] = start_time + timedelta(seconds=next_meta['log_len_seconds'] )
        next_meta['len'] = len(next_df)

        next_start_time = parser.parse(next_meta['log_start_time'])

        if meta['log_end_time'] + timedelta(seconds=10) < next_start_time:
            logger.warning("Gap between logs is large for unit %s", meta['unit_number'])
        if meta['log_end_time'] > next_start_time:
            logger.warning("Overlap between logs for unit %s", meta['unit_number'])

        next_df['timestamp'] += meta['log_len_seconds']
        df = pd.concat([df, next_df], ignore_index=True)

        meta['log_len_seconds'] += next_meta['log_len_seconds']
        meta['len'] += next_meta['len']
        meta['log_end_time'] = next_meta['log_end_time']

        update_log_file_status(meta['uuid'], "Combined With Later LOG")

        meta.setdefault('file_continuations', []).append({
            "file_name": files_remaining[0],
            "log_start_time": next_meta['log_start_time'],
            "log_end_time": next_meta['log_end_time'],
            "log_len_seconds": next_meta['log_len_seconds'],
            "len": next_meta['len']
        })
        new_continued_name = f"{meta['unit_number']}_{meta['log_num']:05d}_cont{n_continuation:02d}"
        archive_log(INPUT_FILES / files_remaining[0], meta['unit_output_folder'] / "in_logs_processed" / f"{new_continued_name}.log")

    return df, meta


def save_mf4_files(df:pd.DataFrame, meta:dict, global_dbc_files: list[Path]) -> None:
    mf4 = df_to_mf4(df)
    raw_path = meta['unit_output_folder'] / f"raw_logs/raw-{meta['file_stem']}.mf4"
    mf4.save(raw_path)

    try:
        unit_dbc_files = list(get_dbc_file_list(DBC_FOLDER / meta['unit_type']))
    except FileNotFoundError:
        logger.warning("No DBC files found for unit type: %s", meta['unit_type'])
        unit_dbc_files = []

    all_dbc_files = [(f, 0) for f in unit_dbc_files + [f for f, _ in global_dbc_files]]
    mf4_extract = mf4.extract_bus_logging({"CAN": all_dbc_files})
    mf4_extract.save(meta['unit_output_folder'] / f"{meta['file_stem']}.mf4")


def process_log_file(file_name: str, global_dbc_files: list[tuple[Path, int]]) -> None:
    logger.info("Starting processing for file: %s", file_name)
    log_path = INPUT_FILES / file_name

    # Read the dataframe and metadata from the log file
    df, meta, continues = read_log_to_df(log_path) 
    df_hash = hashlib.sha256(pd.util.hash_pandas_object(df).values).digest()
    
    # check if vehicle type is the same as database, if not move old vehicle files to new folder
    vehicle = get_vehicle_by_unit_number(unit_number=meta['unit_number'])
    if meta['unit_type'] != vehicle.vehicle_type:
        logger.warning(f"Vehicle type mismatch for unit {meta['unit_number']}: {vehicle.vehicle_type} != {meta['unit_type']}, Moving files to new vehicle folder")
        move_vehicle_files(old_vehicle_type=vehicle.vehicle_type, 
                            new_vehicle_type=meta['unit_type'], 
                            unit_number=meta['unit_number'])
        update_vehicle(unit_number=meta['unit_number'], vehicle_type=meta['unit_type'])

    # Create the folder structure for the file
    meta['unit_output_folder'] = OUTPUT_FILES / meta['unit_type'] / meta['unit_number']
    create_unit_folders(meta['unit_output_folder'])
    meta['file_name'] = file_name
    meta['len'] = len(df)

    # Check if the log file has already been processed
    if does_log_exist(df_hash, meta['unit_number']):
        logger.warning("Log for %s already exists, skipping file %s", meta['unit_number'], file_name)
        # move the log file to archive with duplicate tag
        log_db_entry = get_log_with_hash(df_hash, meta['unit_number'])
        archive_log(log_path, meta['unit_output_folder'] / "in_logs_processed" / f"{log_db_entry.file_stem}_duplicate.log")
        return {"status": "duplicate", "file": file_name}
    
    # Use provided uuid if present, otherwise None
    provided_uuid = meta.get('uuid', None)
    # check if log exists (if it was uploaded by web app it will exist, if not create it)
    log = get_log_file(provided_uuid) if provided_uuid else None
    if not log:
        log = create_log_in_database(
            meta['log_start_time'], 
            meta['unit_number'], 
            df_hash,
            meta['unit_type'], 
            file_name,
            provided_uuid=provided_uuid
        )

    meta.update({"uuid": log.id, "log_num": log.log_number, "file_stem": log.file_stem})

    archived_path = meta['unit_output_folder'] / "in_logs_processed" / f"{meta['file_stem']}.log"
    archive_log(log_path, archived_path)

    update_log_file_status(meta['uuid'], "LOG file Moved")

    # If there is no data in the log file, we can finalize it immediately
    if meta['len'] == 0 and not continues:
        meta['log_end_time'] = meta['log_start_time']
        update_log_file_len(log.id, 0, 0)
        update_log_end_time(log.id, meta['log_end_time'])
        update_log_file_status(log.id, "Zero Data")
        return {"status": "zero_data", "file": file_name}

    # Finalize metadata: log length and end time
    log_len_seconds = df.iloc[-1, 0]
    meta['log_len_seconds'] = log_len_seconds
    start_time = parser.parse(meta['log_start_time'])
    meta['log_end_time'] = start_time + timedelta(seconds=log_len_seconds)

    if continues:
        df, meta = merge_continued_logs(df, meta, continues, file_name, global_dbc_files)

    update_log_end_time(log.id, meta['log_end_time']) # update database record for end time and file len
    update_log_file_len(log.id, meta['log_len_seconds'], len(df))
    save_mf4_files(df, meta, global_dbc_files)
    update_log_file_status(log.id, "Processing Complete")

    return {"status": "processed", "uuid": log.id, "input_file_name": file_name, "log_len": len(df), "output_file_name": meta['file_stem'], "multi_input_files": continues}


def process_new_files() -> int:
    logger.debug("Looking for new CAN Log files to process")
    files_to_process = get_files_to_process(INPUT_FILES)
    logger.debug("Found files: %s", files_to_process)

    global_dbc_files = [(f, 0) for f in get_dbc_file_list(DBC_FOLDER)]
    processed_count = 0

    while True:
        files_to_process = get_files_to_process(INPUT_FILES)
        if not files_to_process:
            logger.debug("No more files to process")
            break
        result = process_log_file(files_to_process[0], global_dbc_files)
        logger.info("Processed file %s: status:%s", result.get('input_file_name', ''), result.get('status', ''))
        if result.get('status') == "processed":
            processed_count += 1

    logger.info("*EXPORT COMPLETE*")
    return processed_count


if __name__ == "__main__":
    setup_environment()
    try:
        while True:
            logger.info("Processing new files")
            process_new_files()
            time.sleep(SLEEP_TIME_BETWEEN_PROCESSINGS)
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
