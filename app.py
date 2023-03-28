from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_uploads import UploadSet, configure_uploads
import pandas as pd
import googlemaps
import json
import os
from io import StringIO
import requests
import shutil
from PIL import Image
from IPython.display import HTML

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOADED_CSV_DEST'] = 'uploads/csv'

csv_uploads = UploadSet('csv')
configure_uploads(app, csv_uploads)

class MyForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'],'FILE FORMATE MUST BE .CSV')
    ])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = MyForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        csv_filename = csv_uploads.save(form.csv_file.data)

        #GETTING THE ADRESSES
        formatted_address(csv_filename)
        return redirect(url_for('success'))
    return render_template('index.html', form=form)

@app.route('/success')
def success():
    return "Form submitted successfully!"


def formatted_address(csv_filename):
    locations = pd.read_csv('uploads/csv/' + csv_filename)
    gmaps = googlemaps.Client(key='AIzaSyBwP_5ZGFGEhgo1Zc9cxW5l2jjEz5-gd1o')

    approx_address = []

    for i in range(0,len(locations)):
        loc1 = locations[['latitude (deg)', 'longitude (deg)']].iloc[i]
        reverse_geocode_result = gmaps.reverse_geocode((loc1['latitude (deg)'], loc1['longitude (deg)']))
        jsonString = json.dumps(reverse_geocode_result)
        jsonFile = open("data.json", "w")
        jsonFile.write(jsonString)
        jsonFile.close()
        with open('data.json', 'r', encoding='utf-8') as f:
            my_data = json.load(f)
            f_address = my_data[0]['formatted_address']
            approx_address.append(f_address)

    locations['approx-address'] = approx_address
    print(csv_filename)
    locations.to_csv('outputs/'+ csv_filename, index=False)

if __name__ == '__main__':
    app.run(debug=True)
