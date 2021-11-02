# CAN Insight Log Processor
This project is designed to be used with the CAN Insight (Insert Link) hardware but could easily be adapted to work with any csv-style CAN logs.

## What It Does
The code constantly searches for new log files to be placed into the `in_logs` folder. The processor takes this raw CAN data in CSV format, converts it to the .mf4 format and applies a .dbc file to it. Applying the .dbc files converts the raw CAN data into signals in physical units (pressure, temperature, speed ect.) which are human-readable and graphable. Ouptut from the processor are two .mf4 files, the first is the raw CAN data, the second being the physical signals extracted using .dbc files. When a new log is detected it is processed and saved into the `out` folder. 

## How It Works
This project uses the [ASAMMDF](https://pypi.org/project/asammdf/) library to convert incomming CSV files into an MF4 format. The secret sauce of this project is to properly format incomming CSV data so that it can be picked up by the ASAMMDF `extract_bus_logging` function.

## Requirements
Docker is the recommended method for running the project, however the code can be run directly on any computer by installing python and the required libraries in `requirements.txt`. See below for step-by-step running instructions.

[ASAMMDFGUI](https://asammdf.readthedocs.io/en/latest/gui.html) is recommended for viewing .MF4 files.
[Kvaser Database Editor](https://www.kvaser.com/download/) is recommended for viewing and building .dbc files.

# Folder Setup and Mounting
To process log files you must first set up the file structure which will store the input and output files. One top-level folder will store all required files for the processing operations. Choose where your log files will be and create the following sub-directories.

- in_logs - folder with input log files (copy logs to be processed into this folder)
- out - folder where outputs will go
- dbc - folder for .dbc files

## Out Folder
All processed data will be placed in the out folder. Metadata from the log files is used to build sub-folders. Each "unit_type" will have a folder and each "unit_number" will have a folder. Typically "unit_type" will be the vehicle type, for example "Ford-Ranger" or "KUBOTA-M7". The "unit_number" should be a unique identifier for the specific vehicle, such as the last few digits of the VIN or serial number. Ouput files will be built in folders like this: `\out\unit_type\unit_number\`.

## DBC Folder
DBC files tell the processor which CAN message IDs contain which physical values, for more information see [this link](https://www.kvaser.com/developer-blog/an-introduction-j1939-and-dbc-files/) and [this link](https://www.csselectronics.com/screen/page/can-dbc-file-database-intro/language/en). DBC files placed in this folder will be applied to all unit types. To apply a dbc file to a single unit type simply place it in a folder named the desired unit type. For example any DBC files in `\dbc\KUBOTA-M7\` would be applied to any incomming log files with a unit_type of `KUBOTA-M7`.

# How to Run
See run-docker-compose.md for details on how to run the software in docker

# Roadmap
- No future improvements currently planned. 