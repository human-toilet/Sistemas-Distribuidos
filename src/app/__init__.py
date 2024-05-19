#dependencias
from flask import Flask, Blueprint
from src.app.config import SECRET_KEY

#blueprints
auth = Blueprint('auth', __name__, template_folder='templates')
whatsapp = Blueprint('whatsapp', __name__, template_folder='templates')
import src.app.routes


#inicializar la app
def create_app():
  app = Flask(__name__)
  app.config['SECRET_KEY'] = SECRET_KEY
  app.register_blueprint(auth)
  app.register_blueprint(whatsapp)
  return app

