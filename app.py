# Description: This file is the main file for the application. It imports all the other files and runs the application.
# Importing the required libraries
from flask import Flask, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

# Creating the app variable
app = Flask(__name__)

# Importing the config file, models and routes file
import config
import models
import api
import routes
