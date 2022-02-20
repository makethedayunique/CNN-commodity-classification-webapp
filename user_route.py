from flask import Flask, redirect, request, url_for, render_template, flash
from flask import Blueprint
from db_conn import DB_conn
from env_paras import *

user_route = Blueprint('user_route', __name__)

@user_route.route('/search-user', methods=['POST', 'GET'])
def search_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        return redirect(url_for('user_route.user_info', user_id = user_id))
    else:
        user_id = request.args.get('user_id')
        return redirect(url_for('user_route.user_info', user_id = user_id))

@user_route.route('/user-info/<user_id>')
def user_info(user_id):
    error = 'Invalid input, please check and input again!'
    if user_id is None or len(user_id.strip()) == 0:
        flash(error)
        return render_template("search-page-user.html")
    user_conn = DB_conn(db_name=DB_NAME_USER)
    trip_conn = DB_conn(db_name=DB_NAME)
    df_user_info = user_conn.find_user_info(user_id)
    df_user_trips, df_user_com = trip_conn.find_trips_to_user(user_id)
    if df_user_info.shape[0] == 0:
        flash(error)
        return render_template("search-page-user.html")

    user_info_dicc = dict(df_user_info)
    return render_template('user_info.html',
                           user_id = user_id,
                           info_dicc = user_info_dicc,
                           trip_menu = df_user_trips,
                           com_info = df_user_com)