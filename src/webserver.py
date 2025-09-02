from fileinput import filename
from pydoc import render_doc
from database.crud import get_vehicle_by_unit_number, new_log_file, new_vehicle, get_vehicles, get_comments_for_log, get_logs_for_unit, get_log_file, new_log_comment, delete_log_comment, hide_show_log_file, update_log_file_headline, update_log_file_status
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
from webserver_logger import handler
import os
from pathlib import Path

from config import DATA_FOLDER
from database.upgrade import init_and_upgrade_db


app = Flask(__name__)
app.logger.addHandler(handler)
init_and_upgrade_db()

output_files = DATA_FOLDER / "out/"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/vehicles/')
def unit_list():
    return render_template("vehicles.html", vehicles=get_vehicles())

@app.route("/vehicles/<vehicle_type>/<unit_id>/")
def specific_unit(vehicle_type, unit_id):
    page = int(request.args.get("page", 1))
    per_page = 10  # or any number you want
    logs, has_next = get_logs_for_unit(unit_id, page, per_page)
    has_prev = page > 1
    return render_template(
        "vehicle.html",
        vehicle=get_vehicle_by_unit_number(unit_id),
        logs=logs,
        page=page,
        has_next=has_next,
        has_prev=has_prev,
        showing_hidden=False
    )

@app.route("/vehicles/<vehicle_type>/<unit_id>/hidden")
def get_hidden_logs(vehicle_type, unit_id):
    page = int(request.args.get("page", 1))
    per_page = 10  # or any number you want
    logs, has_next = get_logs_for_unit(unit_id, page, per_page, hidden=True)
    has_prev = page > 1
    return render_template(
        "vehicle.html",
        vehicle=get_vehicle_by_unit_number(unit_id),
        logs=logs,
        page=page,
        has_next=has_next,
        has_prev=has_prev,
        showing_hidden=True
    )

@app.route("/logs/<uuid>/hide", methods=['GET', 'POST'])
def hide_log(uuid):
    """ Hide the log and redirect to the specific unit page """
    if request.method == "POST":
        if request.form.get('submit_button') == "Hide Log":
            print("hiding log: {}".format(uuid))
            hide_show_log_file(uuid, hidden=True)
    log = get_log_file(uuid)
    vehicle = get_vehicle_by_unit_number(log.unit_number)
    return redirect(url_for('.specific_unit', vehicle_type=vehicle.vehicle_type, unit_id=log.unit_number))

@app.route("/logs/<uuid>/show", methods=['GET', 'POST'])
def show_log(uuid):
    """ Show the log and redirect to the specific unit page """
    if request.method == "POST":
        if request.form.get('submit_button') == "Show Log":
            print("showing log: {}".format(uuid))
            hide_show_log_file(uuid, hidden=False)
    log = get_log_file(uuid)
    return redirect(url_for('.specific_unit', unit_id=log.unit_number))


@app.route("/logs/<uuid>/update_log_headline", methods=['GET', 'POST'])
def update_log_headline(uuid):
    """ Update the headline and return to the log file page"""
    log = get_log_file(uuid)
    if request.method == "POST":
        if request.form.get('submit_button') == "Submit Headline":
            print("updating headline: {}".format(log.id))
            update_log_file_headline(log.id, request.form.get('headline'))
    vehicle = get_vehicle_by_unit_number(log.unit_number)
    comments = get_comments_for_log(log.id)
    log = get_log_file(uuid)
    return render_template("log_file.html", vehicle=vehicle, log=log, comments=comments)


@app.route("/logs/<uuid>/", methods=['GET', 'POST'])
def get_log(uuid):
    log = get_log_file(uuid)
    if request.method == "POST":
        if request.form.get('submit_button') == "Submit Comment":
            comment = request.form.get("comment")
            timestamp = (request.form.get("timestamp"))
            new_log_comment(log.id, comment, timestamp)
        if request.form.get('submit_button') == "Delete Comment":
            delete_log_comment(request.form.get('comment_id'))
    vehicle = get_vehicle_by_unit_number(log.unit_number)
    comments = get_comments_for_log(log.id)
    return render_template("log_file.html", vehicle=vehicle, log=log, comments=comments)


@app.route("/logs/<uuid>/download/")
def download_log(uuid):
    log = get_log_file(uuid)
    vehicle = get_vehicle_by_unit_number(log.unit_number)
    return send_from_directory(directory=output_files/vehicle.vehicle_type/log.unit_number, path=log.file_stem + ".mf4", as_attachment=True, download_name=log.file_stem + ".mf4")


@app.route("/v")
def api_version():
    app.logger.debug("Version route was hit")
    return "0.3.11" # update this to docker version!

@app.route('/data_file/', methods=['GET'])
def check_for_file():
    app.logger.debug("got request for getting data file status")
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
        return "No vehicle for this unit", 400

    # if log file exists return 409 (conflict) do not save file
    if get_log_file(log_start_time, unit_number):
        return "", 409
    
    # create the log file and mark it as "uploading"
    log_id, log_num = new_log_file(log_start_time, unit_number, status="Uploading", original_file_name="{}_{}".format(unit_number, log_name))

    initial_upload_name = DATA_FOLDER / "in_logs/uploading" / "{}_{}".format(unit_number, log_name)
    final_upload_name = DATA_FOLDER / "in_logs" / "{}_{}".format(unit_number, log_name)

    # make sure data file does not exist before writing
    if not os.path.isfile(initial_upload_name):
        with open(initial_upload_name, 'wb') as the_file:
            the_file.write(request.data)
    else:
        return "", 409
    # move file to folder to process
    os.rename(initial_upload_name, final_upload_name)
    # change log file status to "uploaded"
    update_log_file_status(log_id, "Uploaded")
    return "", 200

if __name__ == '__main__':
    app.logger.addHandler(handler)
    app.run(debug=True, host="0.0.0.0")
