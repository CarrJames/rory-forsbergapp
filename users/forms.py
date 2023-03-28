from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, FileField


class StartForm(FlaskForm):
    username = StringField()
    email = EmailField()
    csv_file = FileField()
    submit = SubmitField()