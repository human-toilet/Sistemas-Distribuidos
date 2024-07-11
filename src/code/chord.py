#dependencias
from src.code.db import DB
from src.utils import set_id
import socket
import threading
import time

#operaciones chord

#operadores database
REGISTER = 'r'
LOGIN = 'l'
ADD_CONTACT = 'ac'
SEND_MSG = 'sm'
RECV_MSG = 'rm'

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
    
  def register(self, id: str, name: str, number: int):
    response = self._send_data(REGISTER, f'{id}|{name}|{number}').decode()
    return response
  
  def login(self, id: str, name: str, number: int):
    response = self._send_data(LOGIN, f'{id}|{name}|{number}').decode()
    return response
      
  def add_contact(self, id: str, name: str, number: int):
    response = self._send_data(ADD_CONTACT, f'{id}|{name}|{number}').decode()
    return response
  
  def send_msg(self, id: str, name: str, number: int, msg: str) -> str:
    response = self._send_data(SEND_MSG, f'{id}|{name}|{number}|{msg}')
    return response
  
  def recv_msg(self, id: str, name: str, number: int, msg: str) -> str:
    response = self._send_data(RECV_MSG, f'{id}|{name}|{number}|{msg}')
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
  
#mi servidor  
class Server:
  def __init__(self, port: int):
    self._ip = socket.gethostbyname(socket.gethostname())
    self._id = set_id(self._ip)
    self._port = port
    self._ref = NodeReference(self._ip, self._port)
    self._succ = self._ref
    self._pred = None
    self._finger = [self._ref] * 160
    self._leader: bool
    
    #hilos
    threading.Thread(target=self._set_leader).start()
    threading.Thread(target=self._start_server).start()
    
  def _set_leader(self):
    while(True):
      self._leader = True if self._pred == None or self._succ.id < self.id else False
      time.sleep(5)
  
  def _fix_finger(self, node: NodeReference):
    for i in range(160):
      if node.id < self._finger[i].id:
        if self._id + 2 ** i <= node.id:
          self._finger[i] = node
      
      else:
        break
  
  def _closest_preceding_finger(self, id: str) -> NodeReference:
    for i in range(160):
      if self._finger[i] != None and self._finger[id] > id:
        return self._finger[i - 1]
    
  def register(self, id: str, name: str, number: int) -> str:
    if self._leader or id <= self._id:
      response = DB.register(name, number)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).register(id, name, number)
    return response
  
  def login(self, id: str, name: str, number: int) -> str:
    if self._leader or id <= self._id:
      response = DB.login(name, number)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).login(id, name, number)
    print(response)
    return response
  
  def add_contact(self, id: str, name: str, number: int) -> str:
    if self._leader or id <= self._id:
      response = DB.add_contact(id, name, number)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).add_contact(id, name, number)
    return response
  
  def send_msg(self, id: str, name: str, number: int, msg: str) -> str:
    if self._leader or id <= self._id:
      response = DB.send_msg(id, name, number, msg)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).send_msg(id, name, number)
    print(response)
    return response
  
  def recv_msg(self, id: str, name: str, number: int, msg: str) -> str:
    if self._leader or id <= self._id:
      response = DB.recv_msg(id, name, number, msg)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).recv_msg(id, name, number)
    print(response)
    return response
  
  def _start_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self.ip, self.port))
      s.listen(10)
      
      while True:
        conn, addr = s.accept()
        print(f'new connection from {addr}' )
        data = conn.recv(1024).decode().split('|')
        option = data[0]
        
        if option == REGISTER:
          id = data[1]
          name = data[2]
          number = str(data[3])
          data_resp = self.register(id, name, number)
          conn.sendall(data_resp)
          
        elif option == LOGIN:
          id = data[1]
          name = data[2]
          number = str(data[3])
          data_resp = self.register(id, name, number)
          conn.sendall(data_resp)
          
        elif option == ADD_CONTACT:
          id = data[1]
          name = data[2]
          number = str(data[3])
          data_resp = self.add_contact(id, name, number)
          conn.sendall(data_resp)
          
        elif option == SEND_MSG:
          id = data[1]
          name = data[2]
          number = str(data[3])
          msg = data[4]
          data_resp = self.send_msg(id, name, number, msg)
          conn.sendall(data_resp)
          
        elif option == RECV_MSG:
          id = data[1]
          name = data[2]
          number = str(data[3])
          msg = data[4]
          data_resp = self.recv_msg(id, name, number, msg)
          conn.sendall(data_resp)
          
        if data_resp:
            response = f'{data_resp.id},{data_resp.ip}'.encode()
            conn.sendall(response)
            
        conn.close()
  
  @property
  def id(self):
    return self._id
  
  @property
  def ip(self):
    return self._ip
  
  @property
  def port(self):
    return self._port
  
  

    
    
    
  