from flask import Flask, redirect, request, url_for, render_template, flash
from flask import Blueprint
from db_conn import DB_conn
from env_paras import *

trip_route = Blueprint('trip_route', __name__)


@trip_route.route('/search-trip', methods = ['POST', 'GET'])
def search_trip():
    if request.method == 'POST':
        upload_id = request.form['upload_id']
        return redirect(url_for('trip_route.trip_info', upload_id = upload_id))
    else:
        upload_id = request.args.get('upload_id')
        return redirect(url_for('trip_route.trip_info', upload_id = upload_id))

@trip_route.route('/trip-info/<upload_id>')
def trip_info(upload_id):
    error = 'Invalid input, please check and input again!'

    if upload_id is None or len(upload_id.strip()) == 0:
        flash(error)
        return render_template("search-page-trip.html")

    trip_conn = DB_conn(db_name=DB_NAME)
    df_trip = trip_conn.find_trip_img(upload_id)
    trip_info = trip_conn.find_trip_info(upload_id)
    trip_items = trip_conn.find_trip_details(upload_id)

    if df_trip.shape[0] == 0:
        flash(error)
        return render_template("search-page-trip.html")
    else:
        image_url = df_trip['image_url'].tolist()
        return render_template('upload_trip.html',
                                image_url = image_url,
                                trip_info = trip_info,
                                trip_items = trip_items)
