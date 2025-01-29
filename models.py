#Importing the required libraries
from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash, check_password_hash

# Creating the database object
db = SQLAlchemy(app)

# Creating the Models
# Define the association table for the many-to-many relationship between albums and songs
album_song_association = db.Table(
    'album_song_association',
    db.Column('album_id', db.Integer, db.ForeignKey('albums.album_id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.song_id'), primary_key=True)
)

# Define the association table for the many-to-many relationship between playlists and songs
playlist_song_association = db.Table(
    'playlist_song_association',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.playlist_id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.song_id'), primary_key=True)
)


class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(15), unique=True, nullable=False)
    passhash = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(10), nullable=False)

    # Define relationship
    creator = db.relationship('Creators', back_populates='user', uselist=False)
    ratings = db.relationship('Ratings', back_populates='user')
    playlists = db.relationship('Playlists', back_populates='user')

    # Creating the password hashing function
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')

    # Creating the password setter function
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    # Creating the password checker function
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Creators(db.Model):
    __tablename__ = 'creators'
    creator_id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    artist_name = db.Column(db.String(50), nullable=False)
    contact_info = db.Column(db.String(50), nullable=False)
    Flag = db.Column(db.Boolean, default=False, nullable=False)
    
    # Establish a back-reference to Users
    user = db.relationship('Users', back_populates='creator')
    song = db.relationship('Songs', back_populates='creator')
    albums = db.relationship('Albums', back_populates='creator')

class Songs(db.Model):
    __tablename__ = 'songs'
    song_id = db.Column(db.Integer, primary_key=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('creators.creator_id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    singer = db.Column(db.String(50), nullable=False)
    song_path = db.Column(db.String(100), nullable=False)
    lyrics_path = db.Column(db.String(100), nullable=False)
    thumbnail_path = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    release_date = db.Column(db.DateTime, nullable=False)
    genre = db.Column(db.String(10), nullable=False)

    #Define relationships
    creator = db.relationship('Creators', back_populates='song')
    albums = db.relationship('Albums', secondary=album_song_association, back_populates='songs')
    playlists = db.relationship('Playlists', secondary=playlist_song_association, back_populates='songs')
    ratings = db.relationship('Ratings', back_populates='song')

class Albums(db.Model):
    __tablename__ = 'albums'
    album_id = db.Column(db.Integer, primary_key = True, nullable = False)
    name = db.Column(db.String(40),  nullable = False)
    creator_id = db.Column(db.Integer, db.ForeignKey('creators.creator_id'), nullable = False)
    thumbnail_path = db.Column(db.String(100),  nullable = False)
    release_date = db.Column(db.DateTime, nullable = False)
    genre = db.Column(db.String(10),  nullable = False)

    # Define many-to-many relationship
    songs = db.relationship('Songs', secondary=album_song_association, back_populates='albums')
    creator = db.relationship('Creators', back_populates='albums')


class Playlists(db.Model):
    __tablename__ = 'playlists'
    playlist_id = db.Column(db.Integer, primary_key = True, nullable = False)
    name = db.Column(db.String(40),  nullable = False)
    thumbnail_path = db.Column(db.String(100),  nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable = False)

    #Define relationships
    user = db.relationship('Users', back_populates='playlists')
    songs = db.relationship('Songs', secondary=playlist_song_association, back_populates='playlists')

class Ratings(db.Model):
    __tablename__ = 'ratings'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True, nullable = False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.song_id'), primary_key=True, nullable = False)
    rating = db.Column(db.Integer, nullable = False)

    # Define relationships
    user = db.relationship('Users', back_populates='ratings')
    song = db.relationship('Songs', back_populates='ratings')

#creating database if it doesn't exist
with app.app_context():
    db.create_all()

    #Create admin if admin doesn't exist
    admin = Users.query.filter_by(role='admin').first()
    if not admin:
        admin = Users(username='admin', password='admin', name='admin', email='admin@admin.com', role='admin')
        db.session.add(admin)
        db.session.commit()                     