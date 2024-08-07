#dependencias
from flask import Flask
from src.visual.config import SECRET_KEY
from src.visual.auth import auth

#inicializar la app
def create_app():
  app = Flask(__name__)
  app.config['SECRET_KEY'] = SECRET_KEY
  app.register_blueprint(auth)
  return app

