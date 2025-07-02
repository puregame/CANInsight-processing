import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
import os
import json

from log_converter_logger import logger

# Constants for CAN signal conversion
CAN_SIGNAL_DTYPE = np.dtype([
    ("CAN_DataFrame.BusChannel", "<u1"),
    ("CAN_DataFrame.ID", "<u4"),
    ("CAN_DataFrame.IDE", "<u1"),
    ("CAN_DataFrame.DLC", "<u1"),
    ("CAN_DataFrame.DataLength", "<u1"),
    ("CAN_DataFrame.DataBytes", "(8,)u1"),
    ("CAN_DataFrame.Dir", "<u1"),
    ("CAN_DataFrame.EDL", "<u1"),
    ("CAN_DataFrame.BRS", "<u1")
])

CAN_SIGNAL_SOURCE = Source(
    name="CAN",
    path="CAN",
    comment="",
    source_type=v4c.SOURCE_BUS,
    bus_type=v4c.BUS_TYPE_CAN,
)

def get_dbc_file_list(folder):
    if not os.path.exists(folder):
        raise FileNotFoundError("DBC Folder not found.")
    return map(lambda x: folder / x, filter(lambda x: x.endswith(".dbc"), os.listdir(folder)))

def hex_to_int(x):
    return int(str(x), 16)

def is_val_hex(val):
    try:
        int(str(val), 16)
        return True
    except ValueError:
        return False

def is_val_float(val):
    try:
        float(val)
        return True
    except ValueError:
        return False

def read_csv_data(df):
    continues = False
    df = df.fillna('00')
    logger.debug("\tRead CSV data to dataframe")

    if df['timestamp'].dtype != np.float64 and not df.empty:
        if df.iloc[-1, 0] == "---- EOF NEXT FILE TO FOLLOW ----":
            logger.debug("\t\tthis file has eof, marking for combining with next file")
            df.drop(df.tail(1).index, inplace=True)
            df['timestamp'] = df['timestamp'].astype(np.float64)
            continues = True
        else:
            logger.warning("\t\t\tTimestamps are not floats and last row is not EOF string! This file contains invalid timestamps.")

    df = df[df['timestamp'].apply(is_val_float)]
    df['timestamp'] = df['timestamp'].astype(np.float64)

    for column in ['CAN_ID', 'Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']:
        df = df[df[column].apply(is_val_hex)]

    logger.debug('\tconverting all columns into integer values')
    for column in ['CAN_ID', 'Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']:
        df[column] = df[column].apply(hex_to_int)

    logger.debug('\tconversion complete')
    return df, continues

def split_string_every_n_chars(s, n=2):
    return [s[i:i+n] for i in range(0, len(s), n)]

def dat_line_to_data(line):
    try:
        data = {}
        data['timestamp'] = np.float64(line[:line.find("-")])
        line = line[line.find("-") + 1:]
        data['CAN_BUS'] = np.float64(int(line[0]))
        data['CAN_ID'] = line[line.find("-") + 1:line.find("#")]
        int(data['CAN_ID'], 16)
        data['CAN_EXT'] = float(len(data['CAN_ID']) > 3)
        data_str = line[line.find("#") + 1:]
        can_message = split_string_every_n_chars(data_str, 2)
        data['CAN_LEN'] = len(can_message)
        can_message += ['00'] * (8 - len(can_message))
        for byte in can_message[:7]:
            int(byte, 16)
        for i in range(8):
            data[f"Data{i}"] = can_message[i]
        return data
    except ValueError:
        logger.info("\t\t\tIncorrect data line format: {}".format(line))
        raise Exception("Malformed DAT Packet")

def data_to_csv_line(data):
    return ",".join(str(data[k]) for k in [
        'timestamp', 'CAN_BUS', 'CAN_EXT', 'CAN_ID', 'CAN_LEN',
        'Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7']) + "\n"

def read_dat_file(f):
    continues = False
    tmp_file_path = "/tmp/test_file.csv"
    with open(tmp_file_path, "w") as csv_file:
        csv_file.write("timestamp,CAN_BUS,CAN_EXT,CAN_ID,CAN_LEN,Data0,Data1,Data2,Data3,Data4,Data5,Data6,Data7\n")
        for i, line in enumerate(f):
            line = line.strip()
            if line == "---- EOF NEXT FILE TO FOLLOW ----":
                continues = True
                break
            try:
                csv_file.write(data_to_csv_line(dat_line_to_data(line)))
            except Exception as e:
                logger.info(f"\t\tException processing line: {line}. Skipping line")
                logger.info(e)
            if (i % 1000000) == 1:
                logger.debug(f"\t\t\tDone {i} lines")

    df = pd.read_csv(tmp_file_path,
                     dtype={col: str for col in ['CAN_ID', 'Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7']},
                     on_bad_lines='skip')

    for column in ['CAN_ID', 'Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']:
        df[column] = df[column].apply(hex_to_int)

    return df, continues

def read_log_to_df(file):
    logger.debug(f"Reading file {file} to dataframe")
    with open(file, 'r') as f:
        meta = json.loads(f.readline())
        logger.debug("\tloaded metadata from file")
        if "log_type" in meta and meta["log_type"].startswith("CSV"):
            logger.debug("\tProcessing file as CSV")
            df = pd.read_csv(f, dtype={col: str for col in ['CAN_ID','Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7']}, on_bad_lines='skip')
            df, continues = read_csv_data(df)
        elif "log_type" in meta and meta["log_type"].startswith("DAT"):
            logger.debug("\tProcessing file as DAT")
            f.readline()  # Skip header line
            df, continues = read_dat_file(f)
        else:
            logger.debug("\tNo log_type, processing file as CSV")
            df = pd.read_csv(f, dtype={col: str for col in ['CAN_ID','Data0','Data1','Data2','Data3','Data4','Data5','Data6','Data7']}, on_bad_lines='skip')
            df, continues = read_csv_data(df)

    return df, meta, continues

def df_to_mf4(df):
    row_count = df.shape[0]
    Bytes = df[[f'Data{i}' for i in range(8)]].values.astype('u1')
    arrays = [
        df['CAN_BUS'].to_numpy(dtype='u1'),
        df['CAN_ID'].to_numpy(dtype='u4'),
        df['CAN_EXT'].to_numpy(dtype='u1'),
        df['CAN_LEN'].to_numpy(dtype='u1'),
        df['CAN_LEN'].to_numpy(dtype='u1'),
        Bytes,
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
    ]
    sig = Signal(
        samples=np.rec.fromarrays(arrays, dtype=CAN_SIGNAL_DTYPE),
        timestamps=df['timestamp'].to_numpy(),
        name="CAN_DataFrame",
        source=CAN_SIGNAL_SOURCE,
        master_metadata=['Timestamp', 0]
    )
    mdf = MDF(version='4.11')
    if row_count > 0:
        mdf.append(sig, acq_source=CAN_SIGNAL_SOURCE)
    return mdf

def tail(path, lines=20):
    with open(path, 'rb') as f:
        f.seek(0, 2)
        block_end = f.tell()
        block_number = -1
        blocks = []
        lines_left = lines
        BLOCK_SIZE = 1024
        while lines_left > 0 and block_end > 0:
            seek_pos = block_number * BLOCK_SIZE
            if block_end + seek_pos > 0:
                f.seek(seek_pos, 2)
                blocks.append(f.read(BLOCK_SIZE))
            else:
                f.seek(0)
                blocks.append(f.read(block_end))
            lines_found = blocks[-1].count(b'\n')
            lines_left -= lines_found
            block_end -= BLOCK_SIZE
            block_number -= 1
        return b'\n'.join(b''.join(reversed(blocks)).splitlines()[-lines:])
