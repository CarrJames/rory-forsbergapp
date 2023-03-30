from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False)
    csv_file = db.Column(db.String(100), nullable=False)

    def __init__(self, username, email, csv_file):
        self.username = username
        self.email = email
        self.csv_file = csv_file

def init_db():
    db.drop_all()
    db.create_all()
    new_user = User(username='user1', email='test@test.com', csv_file='test.csv')
    db.session.add(new_user)    
    db.session.commit()