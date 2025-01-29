#This file contains the API for the application. It is used to create the API endpoints for the application.
#Importing the required libraries
from flask import Flask,jsonify,request
from flask_restful import Api, Resource, reqparse, fields, marshal_with
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename
from models import db, Songs, Albums , Creators, Users
from datetime import datetime
import os,config,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from app import app

#Creating the app variable
api = Api(app)

#Delete the file from the file system
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

#Creating the API endpoints
class ValidationError(HTTPException):
    def __init__(self, code, message):
        data = {"error": {"code": code, "Error": message}}
        self.response = jsonify(data)
        self.code = code

class NotFoundError(ValidationError):
    def __init__(self):
        super().__init__(code=404, message="Can't find the resource you are looking for")

#CRUD Opertaions for Songs
songs_parser = reqparse.RequestParser()
songs_parser.add_argument('creator_id')
songs_parser.add_argument('name')
songs_parser.add_argument('singer')
songs_parser.add_argument('release_date')
songs_parser.add_argument('song_path')
songs_parser.add_argument('lyrics_path')
songs_parser.add_argument('thumbnail_path')
songs_parser.add_argument('duration')
songs_parser.add_argument('genre')


class SongsAPI(Resource):
    def get(self):
        all_songs_obj = Songs.query.all()
        all_songs = []
        
        for songs in all_songs_obj:
            this_song = {
                'song_id': songs.song_id,
                'creator_id': songs.creator_id,
                'name': songs.name,
                'singer': songs.singer,
                'song_path': songs.song_path,
                'lyrics_path': songs.lyrics_path,
                'thumbnail_path': songs.thumbnail_path,
                'duration': songs.duration,
                'release_date': songs.release_date.strftime('%Y-%m-%d'),
                'genre': songs.genre
            }
            all_songs.append(this_song)
        return all_songs
    
    def post(self):
        # args = songs_parser.parse_args()
        
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
        # Convert release_date to a datetime object
        release_date_str = request.form.get('release_date', None)
        release_date = datetime.strptime(release_date_str, '%Y-%m-%d') 
       
        # Get the form data
        creator_id=request.form.get('creator_id',None)
        name=request.form.get('name',None)
        singer=request.form.get('singer',None)
        release_date=release_date
        duration=request.form.get('duration',None)
        genre=request.form.get('genre',None)

        # Retrieve the creator object based on creator_id
        creator = Creators.query.get(creator_id)
        if creator is None:
            return {'message': 'Creator not found'}, 404


        # Create a new song object
        new_song = Songs(
            creator_id=creator_id,name=name,singer=singer,release_date=release_date,song_path=song_path,lyrics_path=lyrics_path,thumbnail_path=thumbnail_path, duration=duration, genre=genre
        )

        

        db.session.add(new_song)
        db.session.commit()

         # Return the details of the added song along with the success message
        song_details = {
        'song_id': new_song.song_id,
        'creator_id': new_song.creator_id,
        'name': new_song.name,
        'singer': new_song.singer,
        'release_date': new_song.release_date.strftime('%Y-%m-%d') if new_song.release_date else None,
        'song_path': new_song.song_path,
        'lyrics_path': new_song.lyrics_path,
        'thumbnail_path': new_song.thumbnail_path,
        'duration': new_song.duration,
        'genre': new_song.genre
        }
        return {'message': 'Song added successfully', 'song_details': song_details}, 201

    def put(self,song_id):
        song = Songs.query.get(song_id)
        singer = request.form.get('singer')
        thumbnail_file = request.files['thumbnail_file']
        song_file = request.files['song_file']
        lyrics_file = request.files['song_file']
        genre = request.form.get('genre')

        if not song:
            return {'message': 'Song not found'}, 404
        
        if song:
            if singer:
                song.singer = singer
            if thumbnail_file:
                thumbnail_filename = secure_filename(thumbnail_file.filename)
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
                thumbnail_file.save(thumbnail_path)
                song.thumbnail_path = thumbnail_path
            if song_file:
                song_filename = secure_filename(song_file.filename)
                song_path = os.path.join(app.config['UPLOAD_FOLDER'], 'songs', song_filename)
                song_file.save(song_path)
                song.song_path = song_path
            if lyrics_file:
                lyrics_filename = secure_filename(lyrics_file.filename)
                lyrics_path = os.path.join(app.config['UPLOAD_FOLDER'], 'lyrics', lyrics_filename)
                lyrics_file.save(lyrics_path)
                song.lyrics_path = lyrics_path
            if genre:
                song.genre = genre
        db.session.commit()
        return {'message': 'Song updated successfully'}, 200


    def delete(self,song_id):
        song = Songs.query.get(song_id)
        
        if not song:
           return {'message': 'Song not found'}, 404

        song_path = song.song_path
        thumbnail_path = song.thumbnail_path
        lyrics_path = song.lyrics_path

        if song:

        # Delete the associated files
          delete_file(song_path)
          delete_file(thumbnail_path)
          delete_file(lyrics_path)

        # Delete the song from the database
        db.session.delete(song)
        db.session.commit()
    
        return {'message': 'Song deleted successfully'}, 200   

#Adding the API resources
api.add_resource(SongsAPI, "/api/all_songs", "/api/delete_song/<int:song_id>", "/api/edit_song/<int:song_id>" )

#CRUD Opertaions for Albums
albums_parser = reqparse.RequestParser()

class AlbumsAPI(Resource):
    def get(self):
        all_albums_obj = Albums.query.all()
        all_albums = []
        
        for albums in all_albums_obj:
            this_album = {
                'album_id': albums.album_id,
                'creator_id': albums.creator_id,
                'name': albums.name,
                'release_date': albums.release_date.strftime('%Y-%m-%d'),
                'thumbnail_path': albums.thumbnail_path,
                'genre': albums.genre
            }
            all_albums.append(this_album)
        return all_albums
    
    def post(self, creator_id):
       # Parse form data
       name = request.form.get('name')
       release_date_str = request.form.get('release_date')
       genre = request.form.get('genre')
       thumbnail_file = request.files.get('thumbnail_file')

       # Retrieve the creator object based on creator_id
       creator = Creators.query.get(creator_id)

       if creator is None:
         return {'message': 'Creator not found'}, 404

        # Convert release_date to a datetime object
       release_date = datetime.strptime(release_date_str, '%Y-%m-%d') if release_date_str else None

        # Handle thumbnail file
       thumbnail_path = None
       if thumbnail_file:
          thumbnail_filename = secure_filename(thumbnail_file.filename)
          thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
          thumbnail_file.save(thumbnail_path)

      # Create a new album object
       new_album = Albums(
          creator_id=creator_id,
          name=name,
          release_date=release_date,
          thumbnail_path=thumbnail_path,
          genre=genre
        )

       db.session.add(new_album)
       db.session.commit()

       return {'message': 'Album added successfully'}, 201
 
    def delete (self, album_id):
        album = Albums.query.get(album_id)
        if not album:
            return {'message': 'Album not found'}, 404

        thumbnail_path = album.thumbnail_path

        if album:
            delete_file(thumbnail_path)
            db.session.delete(album)
            db.session.commit()
        
        return {'message': 'Album deleted successfully'}, 200

    def put(self, album_id):
        album = Albums.query.get(album_id)
        name = request.form.get('name')
        release_date_str = request.form.get('release_date')
        genre = request.form.get('genre')
        thumbnail_file = request.files.get('thumbnail_file')

        if not album:
            return {'message': 'Album not found'}, 404
        
        if album:
            if name:
                album.name = name
            if release_date_str:
                release_date = datetime.strptime(release_date_str, '%Y-%m-%d')
                album.release_date = release_date
            if genre:
                album.genre = genre
            if thumbnail_file:
                thumbnail_filename = secure_filename(thumbnail_file.filename)
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails', thumbnail_filename)
                thumbnail_file.save(thumbnail_path)
                album.thumbnail_path = thumbnail_path
        db.session.commit()
        return {'message': 'Album updated successfully'}, 200

#Adding the API resources
api.add_resource(AlbumsAPI, "/api/all_albums", "/api/add_album/<int:creator_id>" , "/api/delete_album/<int:album_id>", "/api/edit_album/<int:album_id>" )

#Getting the graphs for admin dashboard
class AdminAPI(Resource):
    def get(self, graph_type):
        if graph_type == 'song_statistics':
            return self.generate_song_statistics()
        elif graph_type == 'distribution_of_users':
            return self.generate_distribution_of_users()
        else:
            return {'error': 'Invalid graph type'}, 400

    def generate_song_statistics(self):
        # Fetch data from the database
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
        plt.savefig('static/images/song_statistics.png', format='png')
        plt.close()
        return {'message': 'Song statistics generated successfully'}

    def generate_distribution_of_users(self):
        total_users = Users.query.count()
        total_creators = Creators.query.count()

        # Get user distribution data
        user_distribution_data = {
        'General Users': total_users - total_creators,
        'Creators': total_creators
        }

        labels = user_distribution_data.keys()
        sizes = user_distribution_data.values()


        # Create a pie chart
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#36a2eb', '#ff6384'])
        plt.axis('equal')
        plt.title('Distribution of Peoples')
        plt.savefig('static/images/pie_chart.png', format='png')
        plt.close()
        return {'message': 'Distribution of users generated successfully'}

# Add the resource to the API with a dynamic route
api.add_resource(AdminAPI, '/api/dashboard_graphs/<string:graph_type>')
