# BusEye Processor
The BusEye Processor is a companion software for the [BusEye CL2](https://perspic.ca/shop/category/can-bus-dataloggers-2) CAN data logger. It automatically processes incoming log files in CSV format and converts them into industry-standard MF4 files. It also supports DBC decoding to produce human-readable signals in physical units.

Although optimized for BusEye CL2, it can be adapted to work with any CSV-style CAN logs.

## What It Does
The processor continuously monitors the in_logs directory for new log files. When a file is detected:

1. It converts the raw CAN data (CSV) into an .mf4 file.
2. It applies DBC files to decode CAN frames into physical signals (e.g., speed, temperature, pressure).
3. It outputs two .mf4 files:
   Raw CAN Data
   Decoded Signals

These files are saved in the structured out folder for easy access and analysis.

Metadata is stored in a database to be eaily queried by the web interface.

## How It Works
The project uses the [ASAMMDF library](https://pypi.org/project/asammdf/) to perform the CSV-to-MF4 conversion and DBC signal extraction. The key to its functionality is properly formatting the incoming CSV files so they can be consumed by ASAMMDF's extract_bus_logging function.

## Requirements
Recommended: Run via Docker
Alternative: Run directly on any machine with Python and the dependencies in *requirements.txt*

Optional Tools:
[ASAMMDFGUI](https://asammdf.readthedocs.io/en/latest/gui.html) - for viewing .MF4 files.
[Kvaser Database Editor](https://www.kvaser.com/download/) - for creating and editing .dbc files.

# Folder Setup and Mounting
Create a top-level directory to organize the required subfolders:

buseye-processor/
├── in_logs/      # Place incoming CSV log files here
├── out/          # Processed output files go here
└── dbc/          # Store DBC files here

### Log file name convention
Log files are named based on the unit number and order in which they were processed. E.G. the first log that the processor encounters for unit123 with a unit type of Kubota will be placed in `out/Kubota/unit123/` and will be named `unit123_000001.mf4`. (Leading zeroes are used to ensure sorting by filename is effective).

# Environment Variables and Configuration

DB_BACKEND - if "postgres" then use postgres, otherwise use SQLITE
If using postgres:
   DB_USERNAME - default root
   DB_PASSWORD - default root
   DB_HOSTNAME - hostname (Default localhost)
   DB_PORT - Database port (default 5432)
   DB_DATABASE - Database name to use (default logserver_db)

## in_logs
Place all CSV log files you want processed in this folder.

## out
Processed logs are organized into subdirectories using metadata from each log:

out/
├── unit_type/
│   └── unit_number/
│       ├── raw.mf4
│       └── decoded.mf4

unit_type: Typically a vehicle or equipment type (e.g., Ford-Ranger, KUBOTA-M7)
unit_number: A unique identifier like a serial number or last digits of a VIN

## dbc
DBC files define how CAN message IDs map to physical signals.

Place global DBC files directly in dbc/

To assign a DBC to a specific unit type, create a subfolder named after the unit type:

dbc/
├── global.dbc
├── KUBOTA-M7/
│   └── custom_M7.dbc
└── Ford-Ranger/


# How to Run
See run-docker-compose.md for details on how to run the software in docker

## Run Locally
`apt install python3-pip python3.12-venv`
`python3 -m venv venv`
`source venv/bin/activate`
`pip install -r processor/requirements.txt -r webserver/requirements.txt`
`cd src`
`python log_converter.py`

# Roadmap
- No future improvements currently planned. 


# setup in WSL

 - NOTE: must install pgsql library
    sudo apt install libpq-dev


# Running tests
cd into src/ folder

To run all tests:
`python3 -m unittest discover -s tests -p "test_*.py"`

To run a specific test
`python3 -m unittest tests.test_log_converter`