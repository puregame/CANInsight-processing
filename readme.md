# CAN Log Processor
This project is designed to be used with the CAN Insight (Insert Link) hardware but could easily be adapted to work with any csv-style CAN logs.

## What It Does
The code constantly searches for new files to be placed into the `in_logs` folder, when a new log is detected it is processed and saved into the `out` folder. The project also processes CAN data by transforming it with the help of `.dbc` files. Final output is a processed `.mf4` file which contains physical values read on the CAN bus and can be easily graphed for analysis.

## Requirements
Docker is the recommended method for running the project in its own container, however the code can be run directly on any machine by installing python and the required libraries in `requirements.txt.`. See below for step-by-step running instructions.

# Folder Setup and Mounting
To process log files you must first set up the file structure which will store the input and output files. One top-level folder will store all required input and output files for the processing operations.

- in_logs - folder with input log files (copy logs to be processed into this folder)
- out - folder where outputs will go
- dbc - folder for dbc files

## Out Folder
All processed data will be placed in the out folder. Metadata from the log files is used to build sub-folders. Each "unit_type" will have a folder and each "unit_number" will have a folder. Typically "unit_type" will be the vehicle type, for example "Ford-Ranger" or "KUBOTA-M7". The "unit_number" should be a unique identifier for the specific vehicle, such as the last few digits of the VIN or serial number. Ouput files will be built in folders like this: `\out\unit_type\unit_number\`.

## DBC folder
DBC files tell the processor which CAN message IDs contain which phyical values, for more informaiton see [link](google.ca). DBC files placed in this folder will be applied to all unit types. To apply a dbc file to a single unit type simply place it in a folder named the desired unit type. For example any DBC files in `\dbc\KUBOTA-M7\` would be applied to any incomming log files with a unit_type of `KUBOTA-M7`.

# How to Run
These steps are designed to work on a single PC, more advanced docker commands and settings can be used as desired.

1. Download and install Docker.
2. Create a new folder on your computer where all log files will be stored, any location is acceptable and this can change in the future.
3. Create a few folders in this top level directory, `in_logs`, `out` and `dbc`.
4. Build your DBC files in [Kvaser Database Editor](https://www.kvaser.com/download/). Save them in the `dbc` folder.
5. Record some CAN data, see CAN_EXAMPLE.LOG for an example of the file structure required.
6. Build the Docker image using the command `docker build -t can/log_processor -f .\Dockerfile .`
7. Run a new docker container using the command `docker run --mount "type=bind,source=<folder created in step 2>,destination=/data/" -d can/log_processor`
8. Place files into the `in_log` file and watch them get processed!

docker run --mount "type=bind,source=C:\Software\can_data,destination=/data/" can/log_processor