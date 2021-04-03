from flask import Flask, request
import json
from pathlib import Path
app = Flask(__name__)

LOG_FOLDER = Path("/data/in_logs/")
LOG_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/', methods=['POST'])
def post():
    log_name = request.args['log_name']
    with open(LOG_FOLDER/"{}".format(log_name), 'wb') as the_file:
        the_file.write(request.data)
    return ""
    # r = request.data.decode("utf-8").split('\r\n')
    # meta = json.loads(r[0])
    # print(meta)

    # print(repr(r[1]))

if __name__ == '__main__':
    app.run(debug=True)