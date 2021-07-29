from flask import Flask, request
import json
import os
from pathlib import Path
app = Flask(__name__)

# DATA_FOLDER = Path("/data/in_logs/")
DATA_FOLDER = Path("./data/")
DATA_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/data_file/', methods=['GET'])
def check_for_file():
    unit_type = request.args['unit_type']
    unit_number = request.args['unit_number']
    log_time_file = request.args['log_time'].replace(":", "-").replace(".","-")
    print("getting if file exists for: {},{},{}".format(unit_type, unit_number, log_time_file))
    if os.path.exists(DATA_FOLDER / ("out/{}/{}/in_logs_processed/{}.LOG".format(unit_type, unit_number, log_time_file))):
        return "", 200
    return "", 404

@app.route('/data_file/', methods=['POST'])
def post():
    print(request.args)
    print(request.content_length)
    print(request.content_type)
    print(request.__dict__)
    log_name = request.args['log_name']
    unit_id = request.args['unit_id']
    with open(DATA_FOLDER / "in_logs" / "{}_{}".format(unit_id, log_name), 'wb') as the_file:
        the_file.write(request.data)
    return ""

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")