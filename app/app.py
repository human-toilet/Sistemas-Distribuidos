#dependencias
from flask import Flask
from app.config import SECRET_KEY
from app import authentication

#inicializar la app
def create_app():
  app = Flask(__name__)
  app.config['SECRET_KEY'] = SECRET_KEY
  app.register_blueprint(authentication)
  return app

