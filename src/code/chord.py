#dependencias
from src.code.db import DB
from src.code.comunication import NodeReference, BroadcastRef 
from src.code.comunication import REGISTER, LOGIN, ADD_CONTACT, SEND_MSG, RECV_MSG
from src.code.comunication import JOIN, CONFIRM_FIRST, FIX_FINGER, FIND_FIRST, REQUEST_DATA
from src.code.db import DIR
from src.code.handle_data import HandleData
from src.utils import set_id, get_ip, create_folder
import socket
import threading
import time

TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP

#server
class Server:
  def __init__(self):
    self._ip = get_ip()
    self._id = set_id(self._ip)
    self._tcp_port = TCP_PORT
    self._udp_port = UDP_PORT
    self._ref = NodeReference(self._ip, self._tcp_port)
    self._broadcast = BroadcastRef()
    self._handler = HandleData(self._id)
    self._succ = self._ref
    self._pred = None
    self._finger = [self._ref] * 160
    self._leader: bool
    self._first: bool
    
    #hilos
    threading.Thread(target=self._start_udp_server).start()
    threading.Thread(target=self._start_tcp_server).start()
    threading.Thread(target=self._set_leader).start()
    threading.Thread(target=self._set_first).start()
    
    #ejecutar al unirme a la red
    create_folder(f'{DIR}/db')
    self._broadcast.join() 
    self._broadcast.fix_finger()
    self._request_data()
  
  ############################### OPERACIONES CHORD ##########################################
  #unir un nodo a la red
  def _join(self, id: int, ip: str, port: str):
    if id < self._id:
      if self._pred == None:
        response = f'{self._ip}|{self._tcp_port}|{self._ip}|{self._tcp_port}'
        self._pred = NodeReference(ip, port)
        return response
      
      response = f'{self._pred.ip}|{self._pred.port}|{self._ip}|{self._tcp_port}'
      self._pred = NodeReference(ip, port)
      return response
    
    else:
      if self._leader:
        response = f'{self._id}|{self._ip}|{self._tcp_port}|{self._succ.id}|{self._succ.ip}|{self._succ.port}'
        self._succ = NodeReference(ip, port)
        return response
  
      response = self._succ.join(ip, port)
      return response 
  
  #saber si soy el nodo de menor id
  def _set_first(self):
    while(True):
      self._first = True if self._pred == None or self._pred.id > self.id else False
      time.sleep(5)
    
  #saber si soy el nodo de mayor id
  def _set_leader(self):
    while(True):
      self._leader = True if self._pred == None or self._succ.id < self.id else False
      time.sleep(5)
  
  #actualizar la finger cuando entra un nodo
  def _fix_finger(self, node: NodeReference):
    for i in range(160):
      if node.id < self._finger[i].id:
        if self._id + 2 ** i <= node.id:
          self._finger[i] = node
      
      else:
        if self._id == self._finger[i].id:
          self._finger[i] = node
  
  #escoger el nodo mas cercano en la busqueda logaritmica
  def _closest_preceding_finger(self, id: int) -> NodeReference:
    for i in range(160):
      if self._finger[i] > id:
        if i == 0:
          return self._finger[i]
        
        return self._finger[i - 1]
  
  #encontrar el nodo 'first'
  def _find_first(self):
    if self._first:
      return f'{self._ip}|{self._tcp_port}'
    
    response = self._succ.find_first()
    return response
  
  #pedirle data a mi sucesor
  def _request_data(self):
    if self._succ.id != self._id:
      response_succ = self._succ.request_data(self._id)
      response_pred = self._pred.request_data(self._id)
      self._handler.create(response_succ)
      self._handler.create(response_pred)
    
    else:
      print('Block myself')
  ############################################################################################ 
  
  ############################## INTERACCIONES CON LA DB #####################################
  #registrar un usuario
  def register(self, id: int, name: str, number: int) -> str:
    if not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = data_first[1]
      first = NodeReference(ip, port)
      return first.register(id, name, number)
    
    else:
      return self._register(id, name, number)
  
  #registrar un usuario
  def _register(self, id: int, name: str, number: int) -> str:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.register(name, number)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).register(id, name, number)
    return response
  
  #logear a un usuario
  def login(self, id: int, name: str, number: int) -> str:
    if not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = data_first[1]
      first = NodeReference(ip, port)
      return first.login(id, name, number)
    
    else:
      return self._login(id, name, number)
  
  #logear a un usuario
  def _login(self, id: int, name: str, number: int) -> str:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.login(name, number)
      print(response)
      return response

    response = self._closest_preceding_finger(id).login(id, name, number)
    print(response)
    return response
  
  #un usuario agreaga un contacto
  def add_contact(self, id: int, name: str, number: int) -> str:
    if not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = data_first[1]
      first = NodeReference(ip, port)
      return first.add_contact(id, name, number)
    
    else:
      return self._add_contact(id, name, number)
  
  #un usuario agreaga un contacto
  def _add_contact(self, id: int, name: str, number: int) -> str:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.add_contact(id, name, number)
      print(response)
      return response

    response = self._closest_preceding_finger(id).add_contact(id, name, number)
    return response
  
  #un usuario envia un sms
  def send_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = data_first[1]
      first = NodeReference(ip, port)
      return first.send_msg(id, name, number, msg)
    
    else:
      return self._send_msg(id, name, number, msg)
  
  #un usuario envia un sms
  def _send_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.send_msg(id, name, number, msg)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).send_msg(id, name, number)
    print(response)
    return response
  
  #un usuario recibe un sms
  def recv_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = data_first[1]
      first = NodeReference(ip, port)
      return first.recv_msg(id, name, number, msg)
    
    else:
      return self._recv_msg(id, name, number, msg)
  
  #un usuario recibe un sms
  def _recv_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.recv_msg(id, name, number, msg)
      print(response)
      return response
    
    response = self._closest_preceding_finger(id).recv_msg(id, name, number)
    print(response)
    return response
  ############################################################################################
  
  #enviar data a oros servidores
  def _send_data(self, op: str, ip: str, port: str, data=None):
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip, port))
        s.sendall(f'{op}|{data}'.encode('utf-8'))
      
    except Exception as e:
      print(f"Error sending data: {e}")
      return b''
  
  #iniciar server tcp
  def _start_tcp_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self.ip, self._tcp_port))
      print(f'Socket TCP binded to ({self._ip}, {self._tcp_port})')
      s.listen(10)
      
      while True:
        conn, addr = s.accept()
        print(f'new connection from {addr}' )
        data = conn.recv(1024).decode().split('|')
        option = data[0]
        
        if option == CONFIRM_FIRST:
          action = data[1]
          ip = data[2]
          port = data[3]   
          first = NodeReference(ip, port)
          
          if action == JOIN:             
            data_resp = first.join(self._id, self._ip, self._tcp_port).decode().split('|')
            self._pred = NodeReference(data_resp[0], data_resp[1])
            self._succ = NodeReference(data_resp[2], data_resp[3])
          
        elif option == FIND_FIRST:
          data_resp = self._find_first()
          conn.sendall(data_resp)
        
        elif option == REGISTER:
          id = int(data[1])
          name = data[2]
          number = str(data[3])
          data_resp = self._register(id, name, number)
          conn.sendall(data_resp)
          
        elif option == LOGIN:
          id = int(data[1])
          name = data[2]
          number = str(data[3])
          data_resp = self._login(id, name, number)
          conn.sendall(data_resp)
          
        elif option == ADD_CONTACT:
          id = int(data[1])
          name = data[2]
          number = str(data[3])
          data_resp = self._add_contact(id, name, number)
          conn.sendall(data_resp)
          
        elif option == SEND_MSG:
          id = int(data[1])
          name = data[2]
          number = str(data[3])
          msg = data[4]
          data_resp = self._send_msg(id, name, number, msg)
          conn.sendall(data_resp)
          
        elif option == RECV_MSG:
          id = int(data[1])
          name = data[2]
          number = str(data[3])
          msg = data[4]
          data_resp = self._recv_msg(id, name, number, msg)
          conn.sendall(data_resp)
          
        elif option == JOIN:
          id = int(data[1])
          ip = data[2]
          port = data[3]
          data_resp = self._join(id, ip, port)
          
          if data_resp[0] == self._ip and data_resp[1] == self._tcp_port:
            self._succ = NodeReference(ip, id)
            
          elif data_resp[2] == self._ip and data_resp[3] == self._tcp_port:
            self._pred = NodeReference(ip, id)
          
        elif option == REQUEST_DATA:
          id = int(data[1])
          data_resp = self._handler.data(id)
          conn.sendall(data_resp)
              
        conn.close()
  
  #iniciar server udp
  def _start_udp_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      s.bind(('', self._udp_port))
      print(f'Socket UDP binded to {self._udp_port}')
  
      while(True):
        data_recv = s.recvfrom(1024)
        data = data_recv[0].decode().split('|')
        addr = data_recv[1]
        print(f'Recived data: {data} from {addr[0]}')
        option = data[0]
        
        if option == JOIN:
          if addr[0] != self._ip and self._first:
            self._send_data(CONFIRM_FIRST, addr[0], self._tcp_port, f'{JOIN}|{self._ip}|{self._tcp_port}')
          
          else:
            print('Block myself')
            
        if option == FIX_FINGER:
          if addr[0] != self._ip:
            ref = NodeReference(addr[0], TCP_PORT)
            self._fix_finger(ref)
          
          else:
            if not self._leader:
              self._finger = [self._succ] * 160
            
            else:
              print('Block myself')
            
  @property
  def id(self):
    return self._id
  
  @property
  def ip(self):
    return self._ip
  
  @property
  def tcp_port(self):
    return self._tcp_port
  
  

    
    
    
  