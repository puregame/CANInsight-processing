import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
import os
import json

from log_logger import logger

# Constants for can signal conversion

# ASAMMDF CAN signal dtypes
CAN_SIGNAL_DTYPE = np.dtype(
    [
        ("CAN_DataFrame.BusChannel", "<u1"),
        ("CAN_DataFrame.ID", "<u4"),
        ("CAN_DataFrame.IDE", "<u1"), # IDE = extended data frame
        ("CAN_DataFrame.DLC", "<u1"),
        ("CAN_DataFrame.DataLength", "<u1"),
        ("CAN_DataFrame.DataBytes", "(8,)u1"),
        ("CAN_DataFrame.Dir", "<u1"),
        ("CAN_DataFrame.EDL", "<u1"),
        ("CAN_DataFrame.BRS", "<u1")
    ]
)

#ASAMMDF CAN Signal Source Object
CAN_SIGNAL_SOURCE=Source(
    name="CAN",
    path="CAN",
    comment="",
    source_type=v4c.SOURCE_BUS,
    bus_type=v4c.BUS_TYPE_CAN,
)

def get_dbc_file_list(folder):
    if os.path.exists(folder):
        files = os.listdir(folder)
        return map(lambda x: folder/x, filter(lambda x: x[-4:]==".dbc", files))
    return []

hex_to_int = lambda x: int(str(x), 16)

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

def read_log_to_df(file):
    logger.debug("Reading file {} to dataframe".format(file))
    f = open(file, 'r')
    meta = json.loads(f.readline())
    logger.debug("\tloaded json files")
    continues = False

    df = pd.read_csv(f,
                        dtype={'CAN_ID': str, 'Data0': str,'Data1': str,'Data2': str,'Data3': str,'Data4': str,'Data5': str,'Data6': str,'Data7': str},
                        on_bad_lines='skip')
    df = df.fillna(value='00')
    
    
    df.drop(df.index[df['timestamp']==0.0], inplace=True) # drop all rows where timestamp is zero
    df.drop(df.index[df['timestamp'].apply(is_val_float) == False], inplace=True) # drop all where timestamp is not float 
    df['timestamp'] = df['timestamp'].astype(np.float64)

    logger.debug("\tread data to dataframe")

    # if timestamps are not floats, then this file probably has continuation
    if df['timestamp'].dtype != np.float64 and len(df) > 0:
        if df.iloc[-1, 0] == "---- EOF NEXT FILE TO FOLLOW ----":
            logger.debug("this file has eof, combining with next file")
            continues = True
            # remove last row and convert timestamps to float64
            df.drop(df.tail(1).index,inplace=True) # drop last row
            df['timestamp']=df.timestamp.apply(lambda x: np.float64(x))
        else:
            raise Exception("Timestamps are not floats and last row is not EOF string!")

    for column in ['CAN_BUS', 'CAN_EXT', 'CAN_ID', 'Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']:
        df.drop(df.index[df[column].apply(is_val_hex) == False], inplace=True)

    logger.debug('\tconverting all columns into integer values')
    # converting all columns into integer values
    df['CAN_ID']=df.CAN_ID.apply(hex_to_int)
    df['Data0']=df.Data0.apply(hex_to_int)
    df['Data1']=df.Data1.apply(hex_to_int)
    df['Data2']=df.Data2.apply(hex_to_int)
    df['Data3']=df.Data3.apply(hex_to_int)
    df['Data4']=df.Data4.apply(hex_to_int)
    df['Data5']=df.Data5.apply(hex_to_int)
    df['Data6']=df.Data6.apply(hex_to_int)
    df['Data7']=df.Data7.apply(hex_to_int)
    logger.debug('\tconversion complete')
    return df, meta, continues


def df_to_mf4(df):
    row_count=df.shape[0]
    
    ID=df['CAN_ID'].to_numpy()
    Bytes = (df[['Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']].values)
    T=df['timestamp'].to_numpy()
    BusChannel=df['CAN_BUS'].to_numpy()
    IDE = df['CAN_EXT'].to_numpy()
    LEN = df['CAN_LEN'].to_numpy()

    CAN_SIGNAL_SOURCE=Source(
        name="CAN",
        path="CAN",
        comment="",
        source_type=v4c.SOURCE_BUS,
        bus_type=v4c.BUS_TYPE_CAN,
    )   

    arrays = [
        BusChannel,
        ID,
        IDE,
        LEN,
        LEN,
        Bytes,
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
    ]
    sig = Signal(
        samples=np.core.records.fromarrays(arrays, dtype=CAN_SIGNAL_DTYPE),
        timestamps=T,
        name="CAN_DataFrame",
        source=CAN_SIGNAL_SOURCE,
        master_metadata=['Timestamp', 0] # 0 = seconds, see Line 2636 of mdf_v4.py
    )

    mdf = MDF(version='4.11')
    if len(ID) > 0:
        # if there are no samples in the file then this will fail, only if there are samples should be append the signal
        mdf.append(sig, acq_source=CAN_SIGNAL_SOURCE)
    return mdf

# tail function not used, included for future use
def tail(path, lines=20):
    ''' Open file at path, read and return the last N lines '''
    f = open(path, 'rb')
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            f.seek(0,0)
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b'\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b''.join(reversed(blocks))
    return b'\n'.join(all_read_text.splitlines()[-total_lines_wanted:])