from flask import Flask, request
import json
import os
from pathlib import Path
app = Flask(__name__)

LOG_FOLDER = Path("/data/in_logs/")
LOG_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/data_file/', methods=['GET'])
def check_for_file():
    unit_type = request.args['unit_type']
    unit_number = request.args['unit_number']
    log_time_file = request.args['log_time']
    print("getting if file exists for: {},{},{}".format(unit_type, unit_number, log_time_file))
    if os.path.exists(Path("/data/out/{}/{}/in_logs_processed/{}.LOG".format(unit_type, unit_number, log_time_file))):
        return ("PATH EXISTS!"), 200
    return "path does not exit", 404

@app.route('/data_file/', methods=['POST'])
def post():
    log_name = request.args['log_name']
    with open(LOG_FOLDER/"{}".format(log_name), 'wb') as the_file:
        the_file.write(request.data)
    return ""

if __name__ == '__main__':
    app.run(debug=True)