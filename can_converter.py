import numpy as np
from asammdf import MDF, Signal
from asammdf.blocks.source_utils import Source
import asammdf.blocks.v4_constants as v4c
import pandas as pd
import json
from helpers import read_simple_csv_to_mf4, CAN_SIGNAL_DTYPE, CAN_SIGNAL_SOURCE
from pathlib import Path
import os

MACHINE_TYPE = "MMC5EV"

input_files = Path("/data/in_csv/")
processed_files = Path("/data/in_csv_processed/")
output_files = Path("/data/out_mf4/")

dbc_folder = Path('/dbc/') # dbc_machine_types[MACHINE_TYPE]["dbc_folder"]

files_to_process = os.listdir(input_files)
print("input data files: {}".format(files_to_process))


def read_csv_to_mf4(csv_file):
    f = open(csv_file, 'r')
    meta = json.loads(f.readline())

    df = pd.read_csv(f, error_bad_lines=True,
                        na_values='00', 
                        parse_dates=True, 
                        dtype={'Data0': str,'Data1': str,'Data2': str,'Data3': str,'Data4': str,'Data5': str,'Data6': str,'Data7': str})
    df = df.fillna(value='00')

    print('converting all columns into integer values')
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
    print('conversion complete')

    row_count=df.shape[0]
    
    ID=df['CAN_ID'].to_numpy()
    Bytes = (df[['Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']].values)
    T=df['datetime'].to_numpy()
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

def get_dbc_file_list(folder):
    files = os.listdir(folder)
    return filter(lambda x: x[-4:]==".dbc", files)

for file in files_to_process:
    file_name = file.replace(".log", "")
    print("processing file: {}".format(file_name))
    mf4, meta = read_csv_to_mf4(input_files / file)
    new_file_name = "{}-{}-{}".format(meta['log_start_time'].replace(":", "-").replace(".","-"), meta['unit_type'], meta['unit_number'])
    mf4.save(output_files / "raw-{}.mf4".format(new_file_name))
    dbc_files = list(get_dbc_file_list(dbc_folder/meta['unit_type']))

    mf4_extract = mf4.extract_bus_logging({"CAN": dbc_files})
    mf4_extract.save(output_files / "extracted-{}.mf4".format(new_file_name))
    os.rename(input_files/file, processed_files/"{}.log".format(new_file_name))
print("*EXPORT COMPELTE*")