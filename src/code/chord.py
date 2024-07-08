#dependencias
from src.code.utils import set_id
from src.code.db import DB
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
      
  @property
  def id(self):
    return self._id
  
  @property
  def ip(self):
    return self._ip
  
  @property
  def port(self):
    return self._port
  

class Node:
  def __init__(self, port: str):
    self._ip = socket.gethostbyname(socket.gethostname())
    self._id = set_id(self._ip)
    self._port = port
    self._succ = NodeReference(self._ip, self._port)
    self._pred = None
    self._finger = [self._succ] * 160
    self._box = set()
    self._leader: bool
    
    #hilos
    threading.Thread(target=self._set_leader).start()
    threading.Thread(target=self._start_server).start()
    
  def _set_leader(self):
    while(True):
      self._leader = True if self._succ == None or self._pred.id > self.id else False
      time.sleep(10)
  
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
    
  def _register(self, id: str, name: str, number: int):
    if id in self._box:
      response = DB.register(name, number)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).register(id, name, number)
    print(response)
    return response
  
  def _login(self, id: str, name: str, number: int):
    if id in self._box:
      return DB.login(name, number)
    
    response = self._closest_preceding_finger(id).login(id, name, number)
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
          data_resp = self._register(id, name, number)
          conn.sendall(data_resp)
          
        elif option == LOGIN:
          id = data[1]
          name = data[2]
          number = str(data[3])
          data_resp = self._register(id, name, number)
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
  
  

    
    
    
  