#dependencias
from flask import Blueprint

#crear el blueprint 'auth' e importar las vistas
auth = Blueprint('auth', __name__, template_folder='templates')
import src.app.authentication.routes