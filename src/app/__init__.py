#dependencias
from flask import Flask
from src.app.config import SECRET_KEY
from src.app.authentication import auth
from src.app.whatsapp import wp

#inicializar la app
def create_app():
  app = Flask(__name__)
  app.config['SECRET_KEY'] = SECRET_KEY
  app.register_blueprint(auth)
  app.register_blueprint(wp)
  return app

