# app/__init__.py
from flask import Flask
# Initializetheapp
app = Flask(__name__,instance_relative_config= True)
# Load theviews
from app import views
# Load theconfigfile
app.config.from_object('config')
