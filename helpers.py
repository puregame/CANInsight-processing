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
    files = os.listdir(folder)
    return filter(lambda x: x[-4:]==".dbc", files)

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

def read_simple_csv_to_mf4(csv_file):
    df = pd.read_csv(csv_file,error_bad_lines=False)
    df = df.fillna(value=0)
    pd.set_option('precision', 5)
    print(df)
    
    print('converting all data points to string' )
    df['Data0'] = df['Data0'].apply(str)
    df['Data1'] = df['Data1'].apply(str)
    df['Data2'] = df['Data2'].apply(str)
    df['Data3'] = df['Data3'].apply(str)
    df['Data4'] = df['Data4'].apply(str)
    df['Data5'] = df['Data5'].apply(str)
    df['Data6'] = df['Data6'].apply(str)
    df['Data7'] = df['Data7'].apply(str)
    print('finished converting all data points to strings')
    print(df)
    
    print('checking csv file for faulty lines')
    # checking all of the data for faulty rows and collecting the indices of the faulty rows
    index = []
    for i in df.iterrows():
        try:
            k0 =  int(i[1]['Data0'], 16)
            k1 =  int(i[1]['Data1'], 16)
            k2 =  int(i[1]['Data2'], 16)
            k3 =  int(i[1]['Data3'], 16)
            k4 =  int(i[1]['Data4'], 16)
            k5 =  int(i[1]['Data5'], 16)
            k6 =  int(i[1]['Data6'], 16)
            k7 =  int(i[1]['Data7'], 16)
        except ValueError:
            index.append(i[0])
    print('finished checking for faulty lines')
    print(df)
    #dropping the rows that are faulty and replacing the dataframe with the new version
    #the names of the rows do no change so they must be referenced by using iloc
    df=df.drop(index=index)
    
    print('converting all columns into integer values')
    # converting all columns into integer values
    hex_to_int = lambda x: int(str(x), 16)
    df['ID']=df.ID.apply(hex_to_int)
    df['Data0']=df.Data0.apply(hex_to_int)
    df['Data1']=df.Data1.apply(hex_to_int)
    df['Data2']=df.Data2.apply(hex_to_int)
    df['Data3']=df.Data3.apply(hex_to_int)
    df['Data4']=df.Data4.apply(hex_to_int)
    df['Data5']=df.Data5.apply(hex_to_int)
    df['Data6']=df.Data6.apply(hex_to_int)
    df['Data7']=df.Data7.apply(hex_to_int)
    print('conversion complete')
    print(df)
    
    df['Timestamp']=df['Timestamp'].astype('float64')
    #converting time stamp to seconds and making each time stamp unique
    #the incrementation by 6 is assuming no more than 6 can messages will be logged in the same millisecond
    row_count=df.shape[0]
    print('differentiating time stamp values ')
    for i in range(0,row_count,6):
        val1=df.iat[i,0]
        df.iat[i,0]=(val1/1000)+0.000001
        if(i+1<row_count):
            val2=df.iat[(i+1),0]
            df.iat[i+1,0]=(val2/1000)+0.000002   
            if(i+2<row_count):
                val3=df.iat[i+2,0]
                df.iat[i+2,0]=(val3/1000)+0.000003   
                if(i+3<row_count):
                    val4=df.iat[i+3,0]
                    df.iat[i+3,0]=(val4/1000)+0.000004
                    if(i+4<row_count):
                        val5=df.iat[i+4,0]
                        df.iat[i+4,0]=(val5/1000)+0.000005   
                        if(i+5<row_count):
                            val6=df.iat[i+5,0]
                            df.iat[i+5,0]=(val6/1000)+0.000006
                            
    ID=df['ID'].to_numpy()
    Bytes = (df[['Data0', 'Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6', 'Data7']].values)
    T=df['Timestamp'].to_numpy()
    print(Bytes)
    
    arrays = [
        np.ones(row_count, dtype='u1'),
        ID,
        np.zeros(row_count, dtype='u1'),
        np.full(row_count, 8, dtype='u1'),
        np.full(row_count, 8, dtype='u1'),
        Bytes,
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
        np.zeros(row_count, dtype='u1'),
    ]
    sig = Signal(
        samples=np.core.records.fromarrays(arrays, dtype=CAN_SIGNAL_DTYPE),
        timestamps=T,
        name='CAN_DataFrame',
        source=CAN_SIGNAL_SOURCE,
        master_metadata=['Timestamp', 0] # 0 = seconds, see Line 2636 of mdf_v4.py
    )

    mdf = MDF(version='4.11')
    mdf.append(sig, acq_source=CAN_SIGNAL_SOURCE)
    return mdf
    