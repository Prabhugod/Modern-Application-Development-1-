# Description: This file contains the configuration for the Flask app.
#Importing the required libraries
from dotenv import load_dotenv
import os

#Loading the environment variables
load_dotenv()

#Importing the app variable from app.py
from app import app

#Setting the configuration for the app
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.secret_key = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

#for creation of secret key
'''
import secrets

# Generate a random secret key with 140 characters
secret_key = secrets.token_hex(70)  

print(f"Random Secret Key: {secret_key}")

'''