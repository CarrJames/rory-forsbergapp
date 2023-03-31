from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'userlogs'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    email = db.Column(db.String(100))
    csv_filename = db.column(db.String(100))
    added = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, username, email, csv_filename):
        self.username = username
        self.email = email
        self.csv_filename = csv_filename

def init_db():
    db.drop_all()
    db.create_all()
    new_user = User(username='user1', email='test@test.com', csv_filename='test.csv')
    db.session.add(new_user)    
    db.session.commit()