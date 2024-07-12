from src.utils import set_id
import socket

#operaciones chord
JOIN = 'join'
CONFIRM_FIRST = 'conf_first'
FIX_FINGER = 'fix_fing'

BROADCAST_IP = '255.255.255.255' #dirección de broadcast
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
    
  def _send_data(self, op: str, data=None) -> bytes:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((self.ip, self.port))
        s.sendall(f'{op}|{data}'.encode('utf-8'))
        return s.recv(1024)
      
    except Exception as e:
      print(f"Error sending data: {e}")
      return b''
  
  ############################ INTERACCIONES CON LA DB #######################################
  #registrar un usuario
  def register(self, id: str, name: str, number: int):
    response = self._send_data(REGISTER, f'{id}|{name}|{number}').decode()
    return response
  
  #logear a un usuario
  def login(self, id: str, name: str, number: int):
    response = self._send_data(LOGIN, f'{id}|{name}|{number}').decode()
    return response
      
  #un usuario agreaga un contacto
  def add_contact(self, id: str, name: str, number: int):
    response = self._send_data(ADD_CONTACT, f'{id}|{name}|{number}').decode()
    return response
  
  #un usuario envia un sms
  def send_msg(self, id: str, name: str, number: int, msg: str) -> str:
    response = self._send_data(SEND_MSG, f'{id}|{name}|{number}|{msg}')
    return response
  
  #un usuario recibe un sms
  def recv_msg(self, id: str, name: str, number: int, msg: str) -> str:
    response = self._send_data(RECV_MSG, f'{id}|{name}|{number}|{msg}')
    return response
  ###############################################################################################
  
  #unir un nodo a la red
  def join(self, id, ip, port):
    response = self._send_data(JOIN, f'{ip}|{port}')
    return response
  
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
  def _send_data(self, op: str, data=None) -> bytes:
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(f'{op}|{data}'.encode('utf-8'), (BROADCAST_IP, UDP_PORT))
    
    except Exception as e:
      print(f"Error sending data: {e}")
      return b''
  
  def join(self):
    self._send_data(JOIN, 'join')
  
  def fix_finger(self, ip: str):
    self._send_data(FIX_FINGER, 'fix finger')