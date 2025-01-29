#importing the required libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from app import app
from sqlalchemy import func
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import os
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from models import db, Users, Creators, Songs, Albums, Playlists, Ratings

# Creating authentication decorator for the routes
#When we use @auth_required above a function definition, 
#it is equivalent to calling function = auth_required(function).
def auth_required(function):
    @wraps(function)
    def inn(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.')
            return redirect(url_for('login'))
        return function(*args, **kwargs)
    return inn

# Creating the decorator for the routes
@app.route('/')
def home():
    flash('Welcome to the Music App. Please Login to continue.')
    flash('If you are a new user, please register first.')
    return render_template('welcome_page.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handling the form submission
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        
        # If the username or password is empty
        if username == '' or password == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('login'))

        # If the username doesn't exist
        if not user:
            flash('Please check your Username and try again.')
            return redirect(url_for('login'))

        # If the username exists, check the password
        if not user.check_password(password):
            flash('Please check your Password and try again.')
            return redirect(url_for('login'))

        # If the user is not an admin
        if user.role == 'admin':
            flash('kindly login through admin login page')
            return redirect(url_for('admin_login'))

        # If login is successful
        session['user_id'] = user.user_id
        return redirect(url_for('index'))

    # If it's a GET request, render the login page
    return render_template('user_login_page.html')

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Handling the form submission
        emailid = request.form.get('emailid')
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')

        # If any of the fields are empty
        if emailid == '' or username == '' or name == '' or password == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('register_user'))

        # If the username or email already exists
        if Users.query.filter_by(username=username).first() or Users.query.filter_by(email=emailid).first():
            flash('Username or Email id already exists. Please choose some other Username or Use another Email id.')
            return redirect(url_for('register_user'))
            
        # Add the new user to the database
        user = Users(email=emailid, username=username, name=name, password=password, role="general")
        db.session.add(user)
        db.session.commit()
        flash('User Successfully Registered. Please Login to continue.')
        return redirect(url_for('login'))
           
    # If it's a GET request, render the registration page
    return render_template('register_user_page.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        # Handling the form submission
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        
        # If the username or password is empty
        if username == '' or password == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('admin_login'))

        # If the username doesn't exist
        if not user:
            flash('Please check your Username and try again.')
            return redirect(url_for('admin_login'))

        # If the username exists, check the password
        if not user.check_password(password):
            flash('Please check your Password and try again.')
            return redirect(url_for('admin_login'))

        # If the user is not an admin
        if user.role != 'admin':
            flash('You are not authorized to log in as an admin.')
            return redirect(url_for('admin_login'))
        
        # If login is successful
        session['user_id'] = user.user_id
        return redirect(url_for('admin_dashboard'))

    # If it's a GET request, render the login page
    return render_template('admin_login_page.html')


@app.route('/home')
# @auth_required is equivalent to calling function = auth_required(function).
@auth_required
def index():
    user = Users.query.get(session['user_id'])
    top_rated_songs = db.session.query(
        Songs, 
        func.round(func.avg(Ratings.rating), 2).label('average_rating')
    ).join(Ratings).group_by(Songs).order_by(func.avg(Ratings.rating).desc()).limit(6).all()
    songs = Songs.query.all()  
    all_albums = Albums.query.all()
    genres = set(song.genre for song in songs)  

    return render_template('index.html', user=user, top_rated_songs=top_rated_songs, songs=songs, all_albums=all_albums, genres=genres)


@app.route('/search')
@auth_required
def search():
    User = Users.query.get(session['user_id'])
    search_query = request.args.get('search_query')
    if search_query == '':
        flash('Please enter a search query.')
        return redirect(url_for('index'))                 
    songs_results = Songs.query.filter(Songs.name.ilike(f"%{search_query}%")).all()
    songs_results2 = Songs.query.filter(Songs.genre.ilike(f"%{search_query}%")).all()
    albums_results = Albums.query.filter(Albums.name.ilike(f"%{search_query}%")).all()
    albums_results2 = Albums.query.join(Creators).filter(Creators.artist_name.ilike(f"%{search_query}%")).all()
    albums_results3 = Albums.query.filter(Albums.genre.ilike(f"%{search_query}%")).all()
    playlists_results = Playlists.query.filter(Playlists.name.ilike(f"%{search_query}%")).all()
    return render_template('search_bar.html', user=User, songs=songs_results, albums=albums_results, playlists=playlists_results, search_query=search_query, songs2=songs_results2, albums2=albums_results2, albums3=albums_results3)

@app.route('/create_playlist', methods=['GET', 'POST'])
@auth_required
def create_playlist():
    user = Users.query.get(session['user_id'])
    songs = Songs.query.all()
    if request.method == 'POST':
        # Save the thumbnail file to a secure location
        thumbnail_file = request.files['thumbnail_file']
        thumbnail_filename = secure_filename(thumbnail_file.filename)

        # Ensure the 'thumbnail' directory exists
        thumbnails_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumbnails_directory, exist_ok=True)

        thumbnail_path = os.path.join(thumbnails_directory, thumbnail_filename)
        thumbnail_file.save(thumbnail_path)

        # Getting response from the upload page
        playlist_name = request.form.get('name')
        

        # If any of the fields are empty
        if playlist_name == '' or thumbnail_filename == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('create_playlist'))
        # Add the new playlist to the database
        playlist = Playlists(name=playlist_name, thumbnail_path=thumbnail_path, user_id=session['user_id'])
        db.session.add(playlist)
        db.session.commit()
        flash('Playlist Successfully Created.')
        return redirect(url_for('index'))

    return render_template('create_playlist.html', user=user, songs=songs)

@app.route('/view_playlist/<int:playlist_id>')
@auth_required
def view_playlist(playlist_id):
    user = Users.query.get(session['user_id'])
    playlist = Playlists.query.get(playlist_id)
    songs = playlist.songs
    return render_template('view_playlist.html', user=user, playlist=playlist, songs=songs)

@app.route('/add_song_to_playlist/<int:playlist_id>', methods=['GET', 'POST'])
@auth_required
def add_song_to_playlist(playlist_id):
    user = Users.query.get(session['user_id'])
    playlist = Playlists.query.get(playlist_id)
    songs = Songs.query.all()

    if request.method == 'POST':
        # Get the selected song_id from the form
        song_id = request.form.get('song_id')
        
       # Check if the song is already in the playlist
        if any(song.song_id == int(song_id) for song in playlist.songs):
            flash('Song is already in the playlist.')
        
        # Add the selected song to the playlist
        else:
          playlist.songs.append(Songs.query.get(song_id))
          db.session.commit()
          flash('Song successfully added to the playlist.')
        
        return redirect(url_for('view_playlist', playlist_id=playlist.playlist_id))
        
    return render_template('add_song_to_playlist.html', user=user, playlist=playlist, songs=songs) 

@app.route('/remove_song_from_playlist/<int:playlist_id>/<int:song_id>', methods=['POST'])
@auth_required
def remove_song_from_playlist(playlist_id, song_id):
    user = Users.query.get(session['user_id'])
    playlist = Playlists.query.get(playlist_id)
    song = Songs.query.get(song_id)

    # Check if the song is associated with the playlist
    if song in playlist.songs:
        # Remove the song from the album
        playlist.songs.remove(song)
        db.session.commit()
        flash('Song successfully removed from the playlist.')
    else:
        flash('Song not found in the playlist.')

    return redirect(url_for('view_playlist', user=user, playlist=playlist, playlist_id=playlist.playlist_id))

@app.route('/view_album/<int:album_id>')
@auth_required
def view_album(album_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)

    if album:
        # Retrieve the songs associated with the album
        songs = album.songs  # Assuming a relationship like album.songs is defined
        return render_template('view_album.html', user=user, creator=creator, album=album, songs=songs)
    else:
        flash('Album not found.')
    return redirect(url_for('creator'))

@app.route('/creator', methods=['GET', 'POST'])
@auth_required
def creator():
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id = session['user_id']).first()
    creator_id = creator.creator_id
    song_count = Songs.query.filter_by(creator_id=creator_id).count()
    avg_rating = db.session.query(func.round(func.avg(Ratings.rating), 2).label('average_rating')).\
    join(Songs).\
    join(Creators, Songs.creator_id == Creators.creator_id).\
    filter(Creators.user_id == Ratings.user_id).\
    filter(Creators.creator_id == creator_id).scalar()
    album_count = Albums.query.filter_by(creator_id=creator_id).count()
    creator_songs = Songs.query.filter_by(creator_id = creator_id).all()
    album_names = Albums.query.filter_by(creator_id = creator_id).all()

    # Check if creator is blacklisted (flag set to True)
    if creator and creator.Flag :
        flash('Access to creator account is restricted. Please contact admin.')
        return redirect(url_for('index'))  

    return render_template('creator_page.html', user = user, song_count = song_count, avg_rating=avg_rating, creator_songs = creator_songs, album_count = album_count, creator = creator, album_names = album_names)

@app.route('/upload_song', methods=['GET', 'POST'])
@auth_required
def upload_song():
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()

    if request.method == 'POST':
        # Save the song file to a secure location
        song_file = request.files['song_file']
        song_filename = secure_filename(song_file.filename)

        # Ensure the 'songs' directory exists
        songs_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'songs')
        os.makedirs(songs_directory, exist_ok=True)

        song_path = os.path.join(songs_directory, song_filename)
        song_file.save(song_path)

        # Save the thumbnail file to a secure location
        thumbnail_file = request.files['thumbnail_file']
        thumbnail_filename = secure_filename(thumbnail_file.filename)

        # Ensure the 'thumbnail' directory exists
        thumbnails_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumbnails_directory, exist_ok=True)

        thumbnail_path = os.path.join(thumbnails_directory, thumbnail_filename)
        thumbnail_file.save(thumbnail_path)

        # Save the lyrics file to a secure location
        lyrics_file = request.files['lyrics_file']
        lyrics_filename = secure_filename(lyrics_file.filename)

        # Ensure the 'lyrics' directory exists
        lyrics_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'lyrics')
        os.makedirs(lyrics_directory, exist_ok=True)

        lyrics_path = os.path.join(lyrics_directory, lyrics_filename)
        lyrics_file.save(lyrics_path)

        # Get the form data
        title = request.form.get('title')
        singer = request.form.get('singer')
        release_date = request.form.get('release_date')
        duration = request.form.get('duration')
        genre = request.form.get('genre')


        # Convert the release_date string to a datetime object
        release_date = datetime.strptime(release_date, '%Y-%m-%d')

        # If any of the fields are empty
        if title == '' or singer == '' or release_date == '' or duration == '' or genre == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('upload_song'))

        # Add the new song to the database
        song = Songs( creator_id=creator.creator_id, name=title, singer=singer, release_date=release_date, song_path=song_path, lyrics_path=lyrics_path, thumbnail_path = thumbnail_path, duration=duration, genre=genre)
        db.session.add(song)
        db.session.commit()
        flash('Song Successfully Uploaded.')
        return redirect(url_for('creator'))

    # If it's a GET request, render the upload song page
    return render_template('upload_song.html', user=user, creator=creator)

@app.route('/view_lyrics/<int:song_id>', methods=['GET'])
@auth_required
def view_lyrics(song_id): 
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    song = Songs.query.get(song_id)
    if song:
        with open(song.lyrics_path, 'r') as lyrics_file:
            lyrics_content = lyrics_file.read()           
    return render_template('view_lyrics.html', lyrics_content=lyrics_content, song=song, user=user, creator=creator)

@app.route('/rate_song', methods=['POST'])
@auth_required
def rate_song():
    data = request.json
    user_id = session.get('user_id')
    song_id = data.get('song_id')
    rating = data.get('rating')

    if song_id and rating and user_id:
        # Check if the user has already rated the song
        existing_rating = Ratings.query.filter_by(user_id=user_id, song_id=song_id).first()

        if existing_rating:
            # Update the existing rating
            existing_rating.rating = rating
        else:
            # Create a new rating
            new_rating = Ratings(user_id=user_id, song_id=song_id, rating=rating)
            db.session.add(new_rating)

        db.session.commit()

        # Include the flash message in the JSON response
        return jsonify({'success': True, 'message': 'Rating submitted successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400


@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
@auth_required
def edit_song(song_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    song = Songs.query.get(song_id)
    if request.method == 'POST':
       singer = request.form.get('singer')
       thumbnail_file = request.files['thumbnail_file']
       song_file = request.files['song_file']
       lyrics_file = request.files['song_file']
       genre = request.form.get('genre')

       # If any of the fields are empty
       if singer == '' or lyrics_file == '' or thumbnail_file == '' or song_file == '' or  genre == '' :
           flash('Please fill all the fields and try again.')
           return redirect(url_for('/creator/edit_song'))
        
        # Save the song file to a secure location
       song_file = request.files['song_file']
       song_filename = secure_filename(song_file.filename)
       song_path = os.path.join(app.config['UPLOAD_FOLDER'], 'songs', song_filename)
       song_file.save(song_path)

       # Save the lyrics file to a secure location
       lyrics_file = request.files['lyrics_file']
       lyrics_filename = secure_filename(lyrics_file.filename)
       lyrics_path = os.path.join(app.config['UPLOAD_FOLDER'], 'lyrics', lyrics_filename)
       lyrics_file.save(lyrics_path)

       # Save the thumbnail file to a secure location
       thumbnail_file = request.files['thumbnail_file']
       thumbnail_filename = secure_filename(thumbnail_file.filename)
       thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
       thumbnail_file.save(thumbnail_path)

       # update to the database
       song.singer = singer
       song.thumbnail_path = thumbnail_path
       song.song_path = song_path
       song.lyrics_path = lyrics_path
       song.genre = genre
       db.session.commit()
       flash('Song Successfully Edited.')
       return redirect(url_for('creator'))

    #If it's a GET request, render the profile page
    return render_template('edit_song.html', user = user, creator = creator, song = song)


@app.route('/delete_song/<int:song_id>', methods=['GET', 'POST'])
@auth_required
def delete_song(song_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    song = Songs.query.get(song_id)
    song_path = song.song_path
    thumbnail_path = song.thumbnail_path
    lyrics_path = song.lyrics_path

    if request.method == 'POST':
        # Delete associated ratings
        for rating in song.ratings:
                db.session.delete(rating)
        # Delete the associated files
        delete_file(song_path)
        delete_file(thumbnail_path)
        delete_file(lyrics_path)

        # Delete the song from the database
        db.session.delete(song)
        db.session.commit()
        flash('Song Successfully Deleted.')
        return redirect(url_for('creator'))
    return render_template('delete_song.html', user = user, creator = creator, song = song)

#Delete the file from the file system
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

@app.route('/delete_song_admin/<int:song_id>', methods=['GET', 'POST'])
@auth_required
def delete_song_admin(song_id):
    user = Users.query.get(session['user_id'])
    song = Songs.query.get(song_id)
    song_path = song.song_path
    thumbnail_path = song.thumbnail_path
    lyrics_path = song.lyrics_path

    if request.method == 'POST':
        # Delete associated ratings
        for rating in song.ratings:
                db.session.delete(rating)
        # Delete the associated files
        delete_file(song_path)
        delete_file(thumbnail_path)
        delete_file(lyrics_path)

        # Delete the song from the database
        db.session.delete(song)
        db.session.commit()
        flash('Song Successfully Deleted.')
        return redirect(url_for('tracks'))
    return render_template('delete_song_admin.html', user = user, song = song)

@app.route('/create_album', methods=['GET', 'POST'])
@auth_required
def create_album():
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    creator_id = creator.creator_id

    if request.method == 'POST':

        # Save the thumbnail file to a secure location
        thumbnail_file = request.files['thumbnail_file']
        thumbnail_filename = secure_filename(thumbnail_file.filename)

        # Ensure the 'thumbnail' directory exists
        thumbnails_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumbnails_directory, exist_ok=True)

        thumbnail_path = os.path.join(thumbnails_directory, thumbnail_filename)
        thumbnail_file.save(thumbnail_path)

        #Getting response from the upload page
        album_name = request.form.get('name')
        release_date = request.form.get('release_date')
        genre = request.form.get('genre')

        # Convert the release_date string to a datetime object
        release_date = datetime.strptime(release_date, '%Y-%m-%d')

        # If any of the fields are empty
        if album_name == '' or release_date == '' or genre == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('create_album'))

        # Add the new album to the database
        album = Albums(name=album_name, creator_id = creator_id,thumbnail_path = thumbnail_path, release_date=release_date, genre=genre)
        db.session.add(album)
        db.session.commit()
        flash('Album Successfully Created.')
        return redirect(url_for('creator'))
    return render_template('create_album.html', user=user, creator=creator)

@app.route('/add_song/<int:album_id>', methods=['GET', 'POST'])
@auth_required
def add_song(album_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)
    creator_albums = Albums.query.filter_by(creator_id=creator.creator_id).all()
    creator_songs = Songs.query.filter_by(creator_id=creator.creator_id).all()

    if request.method == 'POST':
        song_id = request.form.get('song_id')
        song = Songs.query.get(song_id)
        # Check if the song is already associated with the album
        if song in album.songs:
            flash('Song is already in the Album.')
        
        else:
        # Add the song to the album
          album.songs.append(song)
          db.session.commit()
          flash('Song Successfully Added to the Album.')
          return redirect(url_for('creator'))
    return render_template('add_song.html', user=user, creator=creator, creator_songs=creator_songs, creator_albums=creator_albums)

@app.route('/view_song/<int:album_id>')
@auth_required
def view_song(album_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)

    if album:
        # Retrieve the songs associated with the album
        songs = album.songs  
        return render_template('view_song.html', user=user, creator=creator, album=album, songs=songs)
    else:
        flash('Album not found.')
    return redirect(url_for('creator'))

@app.route('/remove_song/<int:album_id>/<int:song_id>', methods=['POST'])
@auth_required
def remove_song(album_id,song_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)
    song = Songs.query.get(song_id)

    # Check if the song is associated with the album
    if song in album.songs:
        # Remove the song from the album
        album.songs.remove(song)
        db.session.commit()
        flash('Song successfully removed from the album.')
    else:
        flash('Song not found in the album.')
    return redirect(url_for('view_song',user=user, creator=creator, album_id=album_id, song_id=song_id))


@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
@auth_required
def edit_album(album_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)
    if request.method == 'POST':
        album_name = request.form.get('name')
        thumbnail_file = request.files['thumbnail_file']
        release_date = request.form.get('release_date')
        genre = request.form.get('genre')

        # Convert the release_date string to a datetime object
        release_date = datetime.strptime(release_date, '%Y-%m-%d')
        
        thumbnail_filename = secure_filename(thumbnail_file.filename)

        # Ensure the 'thumbnail' directory exists
        thumbnails_directory = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        os.makedirs(thumbnails_directory, exist_ok=True)

        thumbnail_path = os.path.join(thumbnails_directory, thumbnail_filename)
        thumbnail_file.save(thumbnail_path)

        # If any of the fields are empty
        if album_name == '' or release_date == '' or genre == '':
            flash('Please fill all the fields and try again.')
            return redirect(url_for('edit_album'))

        # Edit the album in the database
        album.name = album_name
        album.thumbnail_path = thumbnail_path
        album.release_date = release_date
        album.genre = genre
        db.session.commit()
        flash('Album Successfully Edited.')
        return redirect(url_for('creator'))
    return render_template('edit_album.html', user=user, creator=creator, album=album)

@app.route('/delete_album/<int:album_id>', methods=['GET', 'POST'])
@auth_required  
def delete_album(album_id):
    user = Users.query.get(session['user_id'])
    creator = Creators.query.filter_by(user_id=session['user_id']).first()
    album = Albums.query.get(album_id)
    thumbnail_path = album.thumbnail_path
    if request.method == 'POST':

        # Delete the associated files
        delete_file(thumbnail_path)

        # Delete the album from the database
        db.session.delete(album)
        db.session.commit()
        flash('Album Successfully Deleted.')
        return redirect(url_for('creator'))
    return render_template('delete_album.html', user=user, creator=creator, album=album)



@app.route('/profile', methods=['GET', 'POST'])
@auth_required
def profile():
    # Handling the form submission
    if request.method == 'POST':
        user = Users.query.get(session['user_id'])
        creator = Creators.query.filter_by(user_id=session['user_id']).first()
        email = request.form.get('emailid')
        username = request.form.get('username')
        name = request.form.get('name')
        password = request.form.get('password')

        # If the user wants to be a creator
        if request.form.get('option1') == 'yes':
            role = 'creator' 
        else:
            role = 'general'

        # If any of the fields are empty
        if email == '' or username == '' or name == '' or password == '' :
           flash('Please fill all the fields and try again.')
           return redirect(url_for('profile'))

        # Check for the password
        if not user.check_password(password):
            flash('Please check your Password and try again.')
            return redirect(url_for('profile'))
        
        #comitting the changes to the database
        user.role = role
        if role == 'creator':
            # Update existing creator profile or create a new one
            if creator is None:
                creator = Creators(user_id=session['user_id'], artist_name=name, contact_info=email)
                db.session.add(creator)
            else:
                creator.artist_name = name
                creator.contact_info = email
        else:
            # Delete the creator profile if it exists
            if creator is not None:
                db.session.delete(creator)
        db.session.commit()

        #Checking if the user got upgraded to creator or not
        if user.role == 'creator':
           flash('Successfully registered as a creator.')
        else:
            flash('Successfully updated your profile.')
        return redirect(url_for('profile'))
    
    #If it's a GET request, render the profile page
    return render_template('profile_page.html', user = Users.query.get(session['user_id']))

@app.route('/admin_dashboard')
@auth_required
def admin_dashboard():
    user = Users.query.get(session['user_id'])
    top_rated_songs = db.session.query(
        Songs, 
        func.round(func.avg(Ratings.rating), 2).label('average_rating')
    ).join(Ratings).group_by(Songs).order_by(func.avg(Ratings.rating).desc()).limit(10).all()
    songs = Songs.query.all()  
    total_users = Users.query.filter(Users.role != 'admin').count()
    total_creators = Creators.query.count()
    total_tracks = Songs.query.count()
    total_albums = Albums.query.count()
    total_genres = db.session.query(Songs.genre).distinct().count()

    #Generate Bar Chart for song statistics
    song_statistics_graph = song_statistics()

    # Get user distribution data
    user_distribution_data = {
        'General Users': total_users - total_creators,
        'Creators': total_creators
    }

    # Generate user distribution pie chart
    pie_chart_image = generate_pie_chart(user_distribution_data)

    return render_template('admin_dashboard.html', user=user, total_users=total_users, total_creators=total_creators, total_tracks=total_tracks, total_albums=total_albums, total_genres=total_genres, song_statistics_graph=song_statistics_graph, pie_chart_image=pie_chart_image,songs=songs, top_rated_songs=top_rated_songs)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/admin_dashboard/tracks', methods=['GET', 'POST'])
@auth_required
def tracks():
    user = Users.query.get(session['user_id'])
    songs = Songs.query.all()
    return render_template('tracks.html', user = user, songs = songs)

@app.route('/admin_dashboard/albums', methods=['GET', 'POST'])
@auth_required
def albums():
    user = Users.query.get(session['user_id'])
    creators = Creators.query.all()
    albums = Albums.query.all()
    return render_template('albums.html', user = user, albums = albums, creators = creators)

@app.route('/admin_dashboard/creators', methods=['GET', 'POST'])
@auth_required
def creators():
    user = Users.query.get(session['user_id'])
    creators = Creators.query.all()
    return render_template('creators.html', user = user, creators = creators)


@app.route('/delete_album_admin/<int:album_id>', methods=['GET', 'POST'])
@auth_required  
def delete_album_admin(album_id):
    user = Users.query.get(session['user_id'])
    album = Albums.query.get(album_id)
    thumbnail_path = album.thumbnail_path
    if request.method == 'POST':

        # Delete the associated files
        delete_file(thumbnail_path)

        # Delete the album from the database
        db.session.delete(album)
        db.session.commit()
        flash('Album Successfully Removed.')
        return redirect(url_for('albums'))
    return render_template('delete_album_admin.html', user=user, album=album)

@app.route('/toggle_blacklist/<int:creator_id>', methods=['POST'])
@auth_required
def toggle_blacklist(creator_id):
    creator = Creators.query.get(creator_id)
    if creator:
        creator.Flag = not creator.Flag
        db.session.commit()
        if creator.Flag:
            flash('Creator Blacklisted Successfully.')
        else:
            flash('Creator Whitelisted Successfully.')    
    return redirect(url_for('creators'))

@app.route('/song_statistics')
@auth_required
def song_statistics():
    # Fetch data from the database (replace Songs with your actual model)
    songs = Songs.query.all()

    # Extract genre names
    genres = [song.genre for song in songs]

    # Count occurrences of each genre
    genre_counts = {}
    for genre in genres:
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

    # Create a bar chart
    plt.bar(genre_counts.keys(), genre_counts.values(), color='blue')
    plt.xlabel('Genres')
    plt.ylabel('Number of Songs')
    plt.title('Song Statistics by Genre')

    # Save the plot to a BytesIO object
    img_bytes_io = BytesIO()
    plt.savefig(img_bytes_io, format='png')
    img_bytes_io.seek(0)

    # Encode the image as a base64 string
    img_base64 = base64.b64encode(img_bytes_io.getvalue()).decode('utf-8')

    # Close the figure to free up resources
    plt.close()  

    return img_base64

@app.route('/distribution_of_users')
@auth_required
def generate_pie_chart(data):
    labels = data.keys()
    sizes = data.values()

    # Create a pie chart
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#36a2eb', '#ff6384'])
    plt.axis('equal')  
    plt.title('Distribution of Peoples')

    # Save the plot to a BytesIO object
    img_bytes_io = BytesIO()
    plt.savefig(img_bytes_io, format='png')
    plt.close()

    # Encode the image as a base64 string
    img_base64 = base64.b64encode(img_bytes_io.getvalue()).decode('utf-8')

    return img_base64