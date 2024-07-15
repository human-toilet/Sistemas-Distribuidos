#dependencias
from src.utils import set_id
import socket

#operaciones chord
JOIN = 'join'
CONFIRM_FIRST = 'conf_first'
FIX_FINGER = 'fix_fing'
FIND_FIRST = 'fnd_first'
REQUEST_DATA = 'req_data'

BROADCAST_IP = '192.168.161.255' #dirección de broadcast
TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP

#operadores database
REGISTER = 'reg'
LOGIN = 'log'
ADD_CONTACT = 'add_cnt'
SEND_MSG = 'send'
RECV_MSG = 'recv'

#nodos referentes a otros servidores
class NodeReference:
  def __init__(self, ip: str, port: str):
    self._id = set_id(ip)
    self._ip = ip
    self._port = port
    
  #enviar data 
  def _send_data(self, op: str, data=None) -> bytes:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((self._ip, int(self._port)))
        s.sendall(f'{op}|{data}'.encode('utf-8'))
        return s.recv(1024)
      
    except Exception as e:
      print(f"Error sending data: {e}")
      return b''
  
  
  ############################ INTERACCIONES CON LA DB #######################################
  #registrar un usuario
  def register(self, id: int, name: str, number: int) -> bytes:
    response = self._send_data(REGISTER, f'{id}|{name}|{number}')
    return response
  
  #logear a un usuario
  def login(self, id: int, name: str, number: int) -> bytes:
    response = self._send_data(LOGIN, f'{id}|{name}|{number}')
    return response
      
  #un usuario agreaga un contacto
  def add_contact(self, id: int, name: str, number: int) -> bytes:
    response = self._send_data(ADD_CONTACT, f'{id}|{name}|{number}')
    return response
  
  #un usuario envia un sms
  def send_msg(self, id: int, name: str, number: int, msg: str) -> bytes:
    response = self._send_data(SEND_MSG, f'{id}|{name}|{number}|{msg}')
    return response
  
  #un usuario recibe un sms
  def recv_msg(self, id: int, name: str, number: int, msg: str) -> bytes:
    response = self._send_data(RECV_MSG, f'{id}|{name}|{number}|{msg}')
    return response
  ############################################################################################
  
  
  ############################### OPERACIONES CHORD ##########################################
  #unir un nodo a la red
  def join(self, ip, port):
    response = self._send_data(JOIN, f'{ip}|{port}')
    return response
  
  #buscar el nodo 'first'
  def find_first(self):
    response = self._send_data(FIND_FIRST)
    return response
  
  #pedir data a mis conexiones
  def request_data(self, id: int):
    response = self._send_data(REQUEST_DATA, f'{id}')
    return response
  ############################################################################################ 
  
  @property
  def id(self):
    return self._id
  
  @property
  def ip(self):
    return self._ip
  
  @property
  def port(self):
    return self._port
  
#enviar mensajes por broadcast a la red
class BroadcastRef():  
  #enviar data
  def _send_data(self, op: str, data=None) -> bytes:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(f'{op}|{data}'.encode('utf-8'), (BROADCAST_IP, UDP_PORT))
    
    except Exception as e:
      print(f"Error sending data: {e}")
      return b''
  
  #mandar una solicitud a todos los nodos para unirme
  def join(self):
    self._send_data(JOIN)
  
  #mandar una solicitud a todos los nodos para que actualicen sus finger tables
  def fix_finger(self):
    self._send_data(FIX_FINGER)
    
    