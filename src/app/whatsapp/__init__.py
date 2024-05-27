#dependencias
from flask import Blueprint

#crear el blueprint 'auth' e importar las vistas
wp = Blueprint('wp', __name__, template_folder='templates')
import src.app.whatsapp.routes