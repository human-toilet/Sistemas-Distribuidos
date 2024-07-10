#dependencias
from flask import Blueprint
from src.code.chord import Server

#inicializar el server
server = Server(8000)

#crear el blueprint 'auth' e importar las vistas
auth = Blueprint('auth', __name__, template_folder='templates')
import src.app.auth.routes