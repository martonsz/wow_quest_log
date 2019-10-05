import os
import re
import traceback
from flask import Flask, request, render_template, flash, redirect, url_for
from flask_basicauth import BasicAuth
from werkzeug.utils import secure_filename

from read_log import LogReader
from dbutil import WowDatabase

UPLOAD_FOLDER = "./upload"
ALLOWED_EXTENSIONS = {"txt"}

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = b'_5#yyyL"F4Q8z\n\xec]/'

app.config["BASIC_AUTH_USERNAME"] = "admin"
app.config["BASIC_AUTH_PASSWORD"] = os.getenv("WOW_BASIC_AUTH_PASSWORD", "admin")
basic_auth = BasicAuth(app)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def shutdown_server():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()


@app.route("/", methods=["GET"])
@basic_auth.required
def index():
    db = WowDatabase()
    try:
        include_ignored = request.args.get("include_ignored") == "True"

        ignore_quest_name = request.args.get("ignore_quest")
        if ignore_quest_name:
            ignore = request.args.get("ignore") == "True"
            ignore_quest_name = re.sub(" \(\d+\)$", "", ignore_quest_name)
            db.set_ignore_quest(ignore_quest_name, ignore)
            return redirect("/")

        return render_template("index.html.j2", quests=db.get_quests(include_ignored))
    finally:
        db.close()


@app.route("/", methods=["POST"])
@basic_auth.required
def upload_file():
    er = None
    try:
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        username = request.form.get("username_radio")
        if username == "__NEW__":
            username = request.form.get("username_txt")

        if not username:
            flash("No username given")
            return redirect("/")
        print(f"username: {username}")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            # return redirect(url_for("uploaded_file", filename=filename))

            log_reader = LogReader(file_path, username)
            log_reader.insert_quests()
            return redirect("/")
    except Exception as e:
        er = e
        traceback.print_exc()

    flash(f"Something when wrong {er}")
    return redirect("/")


@app.route("/shutdown")
@basic_auth.required
def shutdown():
    """ Shutdown server so that Docker can restart the container """
    shutdown_server()
    return "Server shutting down..."


if __name__ == "__main__":
    app.run(host="0.0.0.0", ssl_context='adhoc', port=5000)
    print("Exiting")
