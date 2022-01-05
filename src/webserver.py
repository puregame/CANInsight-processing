from database.crud import get_vehicle_by_unit_number, new_vehicle
from flask import Flask, request
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path

from config import DATA_FOLDER
from database.upgrade import init_and_upgrade_db
from database.crud import *



app = Flask(__name__)
# logging.basicConfig(, level=logging.DEBUG)
init_and_upgrade_db()

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/data_file/', methods=['GET'])
def check_for_file():
    app.logger.error("got request for getting data file status")
    unit_type = request.args['unit_type']
    unit_number = request.args['unit_number']
    if not get_vehicle_by_unit_number(unit_number):
        app.logger.debug("creating unit: {}".format(unit_number))
        new_vehicle(unit_number, unit_type)
    log_start_time = request.args['log_time']

    if get_log_file(log_start_time, unit_number):
        # if file has been uploaded send 200 for file exists
        return "", 200
    return "", 404

@app.route('/data_file/', methods=['POST'])
def post():
    log_name = request.args['log_name']
    unit_number = request.args['unit_number']
    log_start_time = request.args['log_time']
    # if unit id does not exist then create it
    if not get_vehicle_by_unit_number(unit_number):
        app.logger.debug("creating unit: {}".format(unit_number))
        new_vehicle(unit_number)

    # if log file exists return 409 (conflict) do not save file
    if get_log_file(log_start_time, unit_number):
        return "", 409

    initial_upload_name = DATA_FOLDER / "in_logs" / "{}_{}".format(unit_number, log_name)

    # make sure data file does not exist before writing
    if not os.path.isfile(initial_upload_name):
        with open(initial_upload_name, 'wb') as the_file:
            the_file.write(request.data)
    else:
        return "", 409
    return "", 200

if __name__ == '__main__':
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s: %(message)s")
    handler = RotatingFileHandler(filename=DATA_FOLDER/'webserver.log', maxBytes=10000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.run(debug=True, host="0.0.0.0")