# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from flask import Flask, render_template
from flask import redirect, url_for, request
# from db_conn_251 import DB_conn
from trip_route import trip_route
from user_route import user_route
import dl_route
import warnings
import os

warnings.filterwarnings('ignore')

app = Flask(__name__)
app.register_blueprint(trip_route, url_prefix="/trip")
app.register_blueprint(user_route, url_prefix='/user')
app.register_blueprint(dl_route.dl_route, url_prefix='/dl')

app.secret_key = os.urandom(24)  # set the secret key value by randomly generating string

@app.route('/')
def main_page():
    return render_template("index.html")

@app.route('/jump_user')
def jump_user():
    return render_template("search-page-user.html")

@app.route('/jump_trip')
def jump_trip():
    return render_template("search-page-trip.html")

@app.route('/jump_dl')
def jump_dl():
    dl_route.files = []
    dl_route.files_names = []
    dl_route.lines = []
    dl_route.processed_dfs = []
    dl_route.goods_names = []
    dl_route.categorys = []
    dl_route.output_paths = []
    return render_template("classification-page.html")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=8080)
    app.run(debug=False, threaded=False)



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
