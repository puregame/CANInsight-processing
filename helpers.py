import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
import os
import logging
import json

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

def read_log_to_mf4(csv_file):
    f = open(csv_file, 'r')
    meta = json.loads(f.readline())

    df = pd.read_csv(f, error_bad_lines=True,
                        na_values='00', 
                        parse_dates=True, 
                        dtype={'Data0': str,'Data1': str,'Data2': str,'Data3': str,'Data4': str,'Data5': str,'Data6': str,'Data7': str})
    df = df.fillna(value='00')

    logging.debug('converting all columns into integer values')
    # converting all columns into integer values
    hex_to_int = lambda x: int(str(x), 16)
    df['CAN_ID']=df.CAN_ID.apply(hex_to_int)
    df['Data0']=df.Data0.apply(hex_to_int)
    df['Data1']=df.Data1.apply(hex_to_int)
    df['Data2']=df.Data2.apply(hex_to_int)
    df['Data3']=df.Data3.apply(hex_to_int)
    df['Data4']=df.Data4.apply(hex_to_int)
    df['Data5']=df.Data5.apply(hex_to_int)
    df['Data6']=df.Data6.apply(hex_to_int)
    df['Data7']=df.Data7.apply(hex_to_int)
    logging.debug('conversion complete')

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
    mdf.append(sig, acq_source=CAN_SIGNAL_SOURCE)
    return mdf, meta