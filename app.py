from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_uploads import UploadSet, configure_uploads
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from docx import Document
from docx.shared import Inches
from flask_login import login_required
import os, requests, shutil, json, googlemaps, smtplib, ssl, folium
from datetime import datetime
from PIL import Image
from IPython.display import HTML
from email.message import EmailMessage
import geopandas as gpd
import geopy.distance
from rtree import index
from shapely.geometry import Point
import pandas as pd
import pickle


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
app.config['UPLOADED_CSV_DEST'] = 'uploads/csv'
#   DATABASE CONFIGURATION
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///userlogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#   FILE UPLOAD CONFIGURATION
csv_uploads = UploadSet('csv')
configure_uploads(app, csv_uploads)
# Spatial Index configuration (doesnt work inside the cell-tower function)
idx = index.Index()
# creating the database model
class User(db.Model):
    __tablename__ = 'userlogs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    email = db.Column(db.String(100))
    csv_file = db.Column(db.String(100), nullable=False)
    added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, username, email, csv_file):
        self.username = username
        self.email = email
        self.csv_file = csv_file
# call to create the database model
def init_db():
    db.drop_all()
    db.create_all()
    new_user = User(username='user1', email='test@test.com', csv_file='test.csv')
    db.session.add(new_user)    
    db.session.commit()
# deleting all prior entries to the database
@app.route('/clear_db', methods=['POST'])
def clear_db():
    all_users = db.session.query(User).all()
    for user in all_users:
        db.session.delete(user)
    db.session.commit()
    return render_template('logs.html')
# form set up for the index page
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
    session['logged_in'] = False
    form = MyForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        csv_filename = csv_uploads.save(form.csv_file.data)
        # Adding the inputs to the database
        new_user = User(username=form.username.data, email=form.email.data, csv_file=csv_filename)
        db.session.add(new_user)
        db.session.commit()   
        # adding the email and csv to the session so I can access them in different functions
        session['email'] = email
        session['csv_filename'] = csv_filename
        formatted_address(csv_filename)
        session['logged_in'] = True
        return redirect(url_for('success'))
    return render_template('index.html', form=form)
# returning full page of pano images
@app.route('/formatted')
def formatted():
    return render_template('pano.html')

@app.route('/success')
def success():
    return render_template('success.html')
# shows database entries
@app.route('/logs')
def logs():
    data=User.query.all()
    return render_template('logs.html', data=data)
# func for showing closest cell towers
@app.route('/celldist')
def celldist():
    column_names = ['latitude', 'longitude']
    df = pd.read_csv(r'C:\Users\Rory\Desktop\UNI3\dis-test\cell-tower\234-revised.csv', names=column_names, header=None)
    # Converting it to a geopandas df
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    for i, tower in gdf.iterrows():
        if tower.geometry is not None:
            idx.insert(i, tower.geometry.bounds)
    coords_filename = f'uploads/csv/{session.get("csv_filename")}'
    coords_df = pd.read_csv(coords_filename)
    result_df = find_closest_towers(coords_df, gdf, idx)
    results = pd.DataFrame(result_df, columns=['latitude', 'longitude', 'geometry'])
    results.to_csv('results.csv')
    # mapping it using folium 
    m = folium.Map(location=[52.7, -1.4], zoom_start=6)
    fg1 = folium.FeatureGroup(name='Cell Towers', show=True)
    for i, row in results.iterrows():
        folium.Marker(location=[row['latitude'], row['longitude']],
                    tooltip=f"ID: {i}",
                    icon=folium.Icon(color='red')
                    ).add_to(fg1)
    
# Create a feature group for the second set of markers (green color)
    fg2 = folium.FeatureGroup(name='Inputted', show=True)
    for i, row in coords_df.iterrows():
        folium.Marker(location=[row['latitude (deg)'], row['longitude (deg)']], 
                    tooltip=f"ID: {i}",
                    icon=folium.Icon(color='green')
                    ).add_to(fg2)

# Add the feature groups to the map object
    fg1.add_to(m)
    fg2.add_to(m)
    folium.LayerControl().add_to(m)
    map_html = m._repr_html_()
    return render_template('celltowers.html', map=map_html)
    
# email function using temporary email 
@app.route('/send_email', methods=['POST'])
def send_email():
    email_sender = 'disformatter@gmail.com'
    email_password = 'bqcwnzqvxhcryylq'
    email_reciever = session.get('email')

    subject = 'Document of Formatted Addresses'
    body = 'Please find the formatted addresses document attached.'

    em = EmailMessage()

    em['From'] = email_sender
    em['To'] = email_reciever
    em['Subject'] = subject
    em.set_content(body)

    with open('output.docx', 'rb') as f:
        file_data = f.read()
    em.add_attachment(file_data, maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename='output.docx')
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_reciever, em.as_string())
    return render_template('sent.html')
# empties the uploads folder and the static folder to reduce application size
@app.before_first_request
def empty_folders():
    upload_folder = app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads', 'csv')
    temp_folder = app.config['TEMP_FOLDER'] = os.path.join(os.getcwd(), 'static')
    for folder in [upload_folder, temp_folder]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

# address formatter using googles reverse geocoder api 
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
    pano(csv_filename)
# pano stitching using googles static api 
def pano(csv_filename):
    locations_pano = pd.read_csv('outputs/' + csv_filename)
    headings = [0, 90, 180, 270]
    locations_pano['img_source'] = locations_pano['approx-address']
    for i in range(0, len(locations_pano)):
        lat1 = locations_pano.iloc[i]['latitude (deg)']
        long1 = locations_pano.iloc[i]['longitude (deg)']
        address = locations_pano.iloc[i]['approx-address']
        for heading in headings:
            input_heading = heading
            url = "https://maps.googleapis.com/maps/api/streetview?location={},{}&size=640x640&pitch=0&fov=90&heading={}&key=AIzaSyBwP_5ZGFGEhgo1Zc9cxW5l2jjEz5-gd1o".format(lat1, long1, input_heading)
            response = requests.get(url,stream=True)
            if response.status_code == 200:
                with open(f"standalone_images/{heading}.jpg", "wb") as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)

    ## CREATING PANO IMAGE BY STITCHING
        filenames = ["standalone_images/0.jpg", "standalone_images/90.jpg", "standalone_images/180.jpg", "standalone_images/270.jpg"]

        images = [Image.open(filename) for filename in filenames]
        widths, heights = zip(*(i.size for i in images))

        total_width = sum(widths)
        max_height = max(heights)

        pano_image = Image.new("RGB", (total_width, max_height), color="white")

        x_offset = 0
        for x, image in enumerate(images):
            pano_image.paste(image, (x_offset, 0))
            x_offset += widths[x]
        ## OUTPUTTING PANO IMAGES WITH ADDRESS NAME AS FILE NAME
        filename = str(i) +'.jpg'
        pano_image.save('static/' + filename)
        width = 1280
        height = 320
        locations_pano['img_source'].iloc[i] = r"<img src='{{ url_for('static', filename=" + repr(filename) + ") }}'>"
    to_word(csv_filename)
    # TO HTML
    locations_html = locations_pano.drop(columns=['GPS week', 'GPS second', 'solution status', 'height (m)'])
    # putting the images together into a html file
    result_html = locations_html.to_html()
    result_html_replaced = result_html.replace('&lt;','<').replace('&gt;','>')
    text_file = open('templates/pano.html', "w")
    text_file.write('{% extends "base.html" %}')
    text_file.write('{% block content %}')
    text_file.write(result_html_replaced)
    text_file.write('{% endblock %}')
    text_file.close()

# func for finding the closest cell towers
def find_closest_towers(coords_df, gdf, idx):
    closest_towers = []
    for i, row in coords_df.iterrows():
        point = Point(row['longitude (deg)'], row['latitude (deg)'])
        # Get indices of candidate towers from spatial index
        candidate_indices = list(idx.nearest(point.bounds))
        # Calculate distances to candidate towers and find closest one
        closest_distance = float('inf')
        closest_tower = None
        for i in candidate_indices:
            tower = gdf.iloc[i]
            distance = point.distance(tower.geometry)
            if distance < closest_distance:
                closest_distance = distance
                closest_tower = tower
        closest_towers.append(closest_tower)
    return closest_towers

# formatting document in a word format
def to_word(csv_filename):
    locations_toword = pd.read_csv('outputs/' + csv_filename)
    locations_toword = locations_toword.drop(columns=['GPS week', 'GPS second', 'solution status', 'height (m)'])
    doc = Document()
    table = doc.add_table(rows=1, cols=len(locations_toword.columns))

    header = table.rows[0].cells
    for i in range(len(locations_toword.columns)):
        header[i].text = locations_toword.columns[i]
    header[-1].text = 'Image'

    for index, row in locations_toword.iterrows():
        row_cells = table.add_row().cells
        for i in range(len(locations_toword.columns)):
            row_cells[i].text = str(row[i])
        image_cell = row_cells[-1]
        image_cell.add_paragraph().add_run().add_picture('static/' + str(index) + '.jpg', width=Inches(4.0), height=Inches(1.8))

    doc.save('output.docx')

if __name__ == '__main__':
    app.run(debug=True)
