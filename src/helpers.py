import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
import os
import json

from log_converter_logger import logger

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
    if not os.path.exists(folder):
        raise FileNotFoundError("DBC Folder not found.")
    files = os.listdir(folder)
    return map(lambda x: folder/x, filter(lambda x: x[-4:]==".dbc", files))

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

def read_csv_file(f):
    continues = False
    df = pd.read_csv(f,
                        dtype={'CAN_ID': str, 'Data0': str,'Data1': str,'Data2': str,'Data3': str,'Data4': str,'Data5': str,'Data6': str,'Data7': str},
                        on_bad_lines='skip')
    f.close()
    df = df.fillna(value='00')
    logger.debug("\tRead CSV data to dataframe")

    # if timestamps are not floats, then this file probably has continuation
    if df['timestamp'].dtype != np.float64 and len(df) > 0:
        if df.iloc[-1, 0] == "---- EOF NEXT FILE TO FOLLOW ----":
            logger.debug("\t\tthis file has eof, marking for combining with next file")
            continues = True
            # remove last row and convert timestamps to float64
            df.drop(df.tail(1).index,inplace=True) # drop last row
            df['timestamp']=df.timestamp.apply(lambda x: np.float64(x))
        else:
            logger.warn("\t\t\tTimestamps are not floats and last row is not EOF string! \
                                    This file contains invalid timestamps.")
    
    df.drop(df.index[df['timestamp']==0.0], inplace=True) # drop all rows where timestamp is zero
    df.drop(df.index[df['timestamp'].apply(is_val_float) == False], inplace=True) # drop all where timestamp is not float 
    df['timestamp'] = df['timestamp'].astype(np.float64)

    # for all columns that will be interpreted as hex, drop any values that are not hexadecimal
    for column in ['CAN_ID', 'Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']:
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
    return df, continues

def split_string_every_n_chars(s, n=2):
    return [s[i:i+n] for i in range(0, len(s), n)]

def dat_line_to_data(line:str):
    try:
        data = {}
        data['timestamp'] = np.float64(line[:line.find("-")])
        line = line[line.find("-")+1:]
        data['CAN_BUS'] = np.float64(int(line[0]))
        data['CAN_ID'] = line[line.find("-")+1:line.find("#")]
        int(data['CAN_ID'], 16) # thorw value error if can ID is not in hex format
        data["CAN_EXT"] = np.float64(int((len(data['CAN_ID']) > 3)))
        data_str = line[line.find("#")+1:]
        can_message = split_string_every_n_chars(data_str, 2)
        data['CAN_LEN'] = len(can_message)
        can_message += ['00'] * (8 - len(can_message))
        for i in range(7): # throw valueerror if any of the data is not in hex format
            int(can_message[i], 16)
        data["Data0"] = can_message[0]
        data["Data1"] = can_message[1]
        data["Data2"] = can_message[2]
        data["Data3"] = can_message[3]
        data["Data4"] = can_message[4]
        data["Data5"] = can_message[5]
        data["Data6"] = can_message[6]
        data["Data7"] = can_message[7]
    except ValueError as e:
        logger.info("Incorrect data line format: {}".format(line))
        raise Exception("Malformed DAT Packet")
    return data

def data_to_csv_line(data):
    return "{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(data['timestamp'], data['CAN_BUS'], data["CAN_EXT"], data["CAN_ID"], data['CAN_LEN'],
                data['Data0'],data['Data1'],data['Data2'],data['Data3'],data['Data4'],data['Data5'],data['Data6'],data['Data7'])

def read_dat_file(f):
    continues = False
    header = f.readline()
    df = pd.DataFrame({'timestamp': pd.Series(dtype=np.float64),
                       'CAN_BUS': pd.Series(dtype=np.int8,),
                       'CAN_EXT': pd.Series(dtype=np.int8),
                       'CAN_ID': pd.Series(dtype=str),
                       'CAN_LEN': pd.Series(dtype=np.int8),
                       'Data0': pd.Series(dtype=str), 
                       'Data1': pd.Series(dtype=str), 
                       'Data2': pd.Series(dtype=str), 
                       'Data3': pd.Series(dtype=str), 
                       'Data4': pd.Series(dtype=str), 
                       'Data5': pd.Series(dtype=str), 
                       'Data6': pd.Series(dtype=str), 
                       'Data7': pd.Series(dtype=str)})
    can_frames = []
    logger.debug("\t\tStarting looping through lines")
    i = 0
    csv_file = open("/tmp/test_file.csv", "w")
    csv_file.write("timestamp,CAN_BUS,CAN_EXT,CAN_ID,CAN_LEN,Data0,Data1,Data2,Data3,Data4,Data5,Data6,Data7\n")
    for line in f:
        line = line.replace("\n", "")
        if line == "---- EOF NEXT FILE TO FOLLOW ----":
            continues = True
            break
        try:
            csv_file.write(data_to_csv_line(dat_line_to_data(line)))
        except Exception as ee:
            logger.error("Exception at line: {} Skipping line".format(line))
            logger.error(ee)
            pass

        i+=1
        if (i % 1000000) == 1:
            logger.debug("\t\t\tDone {} lines".format(i))
    csv_file.close()
    logger.debug("\t\tDone looping through lines")
    
    csv_file = open("/tmp/test_file.csv", "r")
    df = pd.read_csv(csv_file,
                        dtype={'CAN_ID': str, 'Data0': str,'Data1': str,'Data2': str,'Data3': str,'Data4': str,'Data5': str,'Data6': str,'Data7': str},
                        on_bad_lines='skip')

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
    return df, continues

def read_log_to_df(file):
    logger.debug("Reading file {} to dataframe".format(file))
    f = open(file, 'r')
    meta = json.loads(f.readline())
    logger.debug("\tloaded metadata from file")
    if "log_type" in meta:
        if meta["log_type"][:3] == "CSV":
            logger.debug("\tProcessing file as CSV")
            df, continues = read_csv_file(f)
        if meta["log_type"][:3] == "DAT":
            logger.debug("\tProcessing file as DAT")
            df, continues = read_dat_file(f)
    else:
        logger.debug("\tNo log_type, processing file as CSV")
        df, continues = read_csv_file(f)

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
