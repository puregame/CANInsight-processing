import os
import shutil

from pathlib import Path

from database.models import Vehicle, LogFile
from log_converter_logger import logger


from config import DATA_FOLDER

def check_files_exist_strs(output_files:Path, vehicle_type:str, unit_number:str, file_stem:str) -> dict:
    return {
        "regular_log": (output_files / vehicle_type / unit_number / (file_stem + ".mf4")).is_file(),
        "raw_logs": (output_files / vehicle_type / unit_number / "raw_logs" / ("raw-" + file_stem + ".mf4")).is_file(),
        "input_log_raw": (output_files / vehicle_type / unit_number / "in_logs_processed" / (file_stem + ".log")).is_file()
    }


def check_files_exist(output_files:Path, vehicle:Vehicle, log:LogFile) -> dict:
    return {
        "regular_log": (output_files / vehicle.vehicle_type / log.unit_number / (log.file_stem + ".mf4")).is_file(),
        "raw_logs": (output_files / vehicle.vehicle_type / log.unit_number / "raw_logs" / ("raw-" + log.file_stem + ".mf4")).is_file(),
        "input_log_raw": (output_files / vehicle.vehicle_type / log.unit_number / "in_logs_processed" / (log.file_stem + ".log")).is_file()
    }

def move_vehicle_files(old_vehicle_type:str, new_vehicle_type:str, unit_number:str) -> bool:
    src = os.path.join(DATA_FOLDER / "out/", old_vehicle_type, unit_number)
    dst = os.path.join(DATA_FOLDER / "out/", new_vehicle_type, unit_number)
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.move(src, dst)
            logger.info(f"Moved {src} to {dst} for unit {unit_number}")
            return True
        except Exception as e:
            logger.error(f"Error moving {src} to {dst}: {e}")
    logger.warning(f"Source directory {src} does not exist")
    return False