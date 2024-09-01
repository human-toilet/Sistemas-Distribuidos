#dependencias
from src.code.db import DB
from src.code.comunication import NodeReference, BroadcastRef, send_data
from src.code.comunication import REGISTER, LOGIN, ADD_CONTACT, SEND_MSG, RECV_MSG, GET
from src.code.comunication import JOIN, CONFIRM_FIRST, FIX_FINGER, FIND_FIRST, REQUEST_DATA, CHECK_PREDECESOR, NOTIFY, UPDATE_PREDECESSOR, UPDATE_FINGER, UPDATE_JOIN, DATA_PRED, FALL_SUCC
from src.code.db import DIR
from src.code.handle_data import HandleData
from src.utils import set_id, get_ip, create_folder
import socket
import threading
import time

TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP
STABILIZE_PORT = 9000 #puerto de escucha del socket stabilize

#server
class Server:
  def __init__(self):
    self._ip = get_ip() #ip
    self._id = set_id(self._ip) #id
    self._tcp_port = TCP_PORT #puerto del socket tp
    self._udp_port = UDP_PORT #puerto del socket udp
    self._stabilize_port = STABILIZE_PORT #puerto del socket estabilizador
    self._ref = NodeReference(self._ip, self._tcp_port) #referencia a mi mismo para la finger table
    self._broadcast = BroadcastRef() #comunicacion por broadcast
    self._handler = HandleData(self._id) #manejar la data de la db
    self._succ = self._ref #inicialmente soy mi sucesor
    self._pred = None #inicialmente no tengo predecessor
    self._pred_info = '' #data replicada por mi predecesor
    self._pred_pred = ''
    self._finger = [self._ref] * 160 #finger table
    self._leader: bool #saber si soy el lider
    self._first: bool #saber si soy el primer nodo
    
    #hilos
    threading.Thread(target=self._start_broadcast_server).start()
    threading.Thread(target=self._start_tcp_server).start()
    threading.Thread(target=self._start_udp_server).start()
    threading.Thread(target=self._start_stabilize_server).start()
    threading.Thread(target=self._set_leader).start()
    threading.Thread(target=self._set_first).start()
    threading.Thread(target=self._info).start()
    threading.Thread(target=self._check_predecessor).start()
    
    #ejecutar al unirme a la red
    create_folder(f'{DIR}/db')
    self._broadcast.join() 
    time.sleep(2) #esperar 2 segundos entre el 'join' y el 'fix finger'
    self._broadcast.fix_finger() 
    time.sleep(2) #esperar 2 segundos entre el 'fix finger' y el 'request data'
    self._request_data()
    print('Ready for use')
  
  ############################### OPERACIONES CHORD ##########################################
  #unir un nodo a la red
  def _join(self, ip: str, port: str) -> bytes:
    id = set_id(ip)
    
    if self._pred == None:
      response = f'{self._ip}|{self._tcp_port}|{self._ip}|{self._tcp_port}'
      self._pred = NodeReference(ip, port)
      self._succ = NodeReference(ip, port)
      return response.encode()
      
    elif id < self._id:
      response = f'{self._pred.ip}|{self._pred.port}|{self._ip}|{self._tcp_port}'
      send_data(UPDATE_JOIN, self._pred.ip, self._udp_port, f'{ip}|{port}')
      self._pred = NodeReference(ip, port)
      return response.encode()
    
    elif self._leader:
        response = f'{self._ip}|{self._tcp_port}|{self._succ.ip}|{self._succ.port}'
        send_data(UPDATE_JOIN, self._succ.ip, self._udp_port, f'{ip}|{port}')
        self._succ = NodeReference(ip, port)
        return response.encode()
  
    response = self._closest_preceding_finger(id).join(ip, port)
    return response 
  
  #saber si soy el nodo de menor id
  def _set_first(self) -> bytes:
    while(True):
      self._first = True if self._pred == None or self._pred.id > self._id else False
    
  #saber si soy el nodo de mayor id
  def _set_leader(self):
    while(True):
      self._leader = True if self._pred == None or self._succ.id < self._id else False
  
  #imprimir informacion de tus adyacentes
  def _info(self):
    while True:
      time.sleep(10)
      print(f'my ip: {self._ip}')
      print(f'pred: {self._pred.ip if self._pred != None else None}, succ: {self._succ.ip}') 
      print(f'{"first" if self._first else "not first"}, {"leader" if self._leader else "not leader"}')
   
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
      if self._finger[i].id > id:
        if i == 0:
          return self._finger[i]
        
        return self._finger[i - 1]
  
  #encontrar el nodo 'first'
  def _find_first(self) -> bytes:
    if self._leader:
      return f'{self._succ.ip}|{self._succ.port}'.encode()
    
    response = self._finger[-1].find_first()
    return response
  
  #pedirle data a mi sucesor
  def _request_data(self):
    if self._succ.id != self._id:
      response_succ = self._succ.request_data(self._id).decode()
      response_pred = self._pred.request_data(self._id).decode()
      self._handler.create(response_succ)
      self._handler.create(response_pred)
   
  #pedirle data a mi predecesor cada 5 segundos   
  def _check_predecessor(self):
    while True:
      if self._pred != None:
        try:
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self._pred.ip, STABILIZE_PORT))
            s.settimeout(5)
            s.sendall(CHECK_PREDECESOR.encode('utf-8'))
            self._pred_info = s.recv(1024).decode()
            ip_pred_pred = self._pred_info.split('|')[-1]

        except:
          print(f'Socket ({self._pred.ip}, {self._pred.port}) disconnected')
          self._handler.create(self._pred_info)
          self._broadcast.update_finger(self._pred.id)
          
          if ip_pred_pred != self._ip:
            try:  
              with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_pred_pred, STABILIZE_PORT))
                s.settimeout(5)
                s.sendall(f'{FALL_SUCC}|{self._ip}|{self._tcp_port}')
                s.recv(1024).decode()

            except:
              print(f'Socket {ip_pred_pred} disconnected too')
              self._handler.create(self._pred_pred)
              self._broadcast.update_finger(set_id(ip_pred_pred))

              if ip_pred_pred != self._succ.ip:
                self._broadcast.notify(set_id(ip_pred_pred))
          
          else:
            self._pred = None
            self._succ = self._ref
            self._finger = [self._ref] * 160
      
        time.sleep(5)
  ############################################################################################ 
  
  ############################## INTERACCIONES CON LA DB #####################################
  #registrar un usuario
  def register(self, id: int, name: str, number: int) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.register(id, name, number).decode()
    
    else:
      return self._register(id, name, number).decode()
  
  #registrar un usuario
  def _register(self, id: int, name: str, number: int) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.register(name, number)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).register(id, name, number)
    return response
  
  #logear a un usuario
  def login(self, id: int, name: str, number: int) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.login(id, name, number).decode()
    
    else:
      return self._login(id, name, number).decode()
  
  #logear a un usuario
  def _login(self, id: int, name: str, number: int) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.login(name, number)
      print(response)
      return response.encode()

    response = self._closest_preceding_finger(id).login(id, name, number)
    print(response)
    return response
  
  #un usuario agreaga un contacto
  def add_contact(self, id: int, name: str, number: int) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.add_contact(id, name, number).decode()
    
    else:
      return self._add_contact(id, name, number).decode()
  
  #un usuario agreaga un contacto
  def _add_contact(self, id: int, name: str, number: int) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.add_contact(id, name, number)
      print(response)
      return response.encode()

    response = self._closest_preceding_finger(id).add_contact(id, name, number)
    return response
  
  #un usuario envia un sms
  def send_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.send_msg(id, name, number, msg).decode()
    
    else:
      return self._send_msg(id, name, number, msg).decode()
  
  #un usuario envia un sms
  def _send_msg(self, id: int, name: str, number: int, msg: str) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.send_msg(id, name, number, msg)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).send_msg(id, name, number, msg)
    print(response)
    return response
  
  #un usuario recibe un sms
  def recv_msg(self, id: int, name: str, number: int, msg: str) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.recv_msg(id, name, number, msg).decode()
    
    else:
      return self._recv_msg(id, name, number, msg).decode()
  
  #un usuario recibe un sms
  def _recv_msg(self, id: int, name: str, number: int, msg: str) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.recv_msg(id, name, number, msg)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).recv_msg(id, name, number, msg)
    print(response)
    return response
  
  #operaciones get
  def get(self, id: int, endpoint: str) -> str:
    if id < self._id and not self._first:
      data_first = self._find_first().decode().split('|')
      ip = data_first[0]
      port = int(data_first[1])
      first = NodeReference(ip, port)
      return first.get(id, endpoint).decode()
    
    else:
      return self._get(id, endpoint).decode()
    
  #operaciones get
  def _get(self, id: int, endpoint: str) -> bytes:
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.get(id, endpoint)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).get(id, endpoint)
    print(response)
    return response
  ############################################################################################
  
  ###################################### SOCKETS #############################################
  #iniciar server tcp
  def _start_tcp_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self._ip, self._tcp_port))
      print(f'Socket TCP binded to ({self._ip}, {self._tcp_port})')
      s.listen(10)
      
      while True:
        conn, addr = s.accept()
        print(f'new connection in TCP from {addr}' )
        data = conn.recv(1024).decode().split('|')
        print(f'Recived data: {data}')
        option = data[0]
          
        if option == FIND_FIRST:
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
          
        elif option == GET:
          id = int(data[1])
          endpoint = data[2]
          data_resp = self._get(id, endpoint)
          conn.sendall(data_resp)
          
        elif option == JOIN:
          ip = data[1]
          port = data[2]
          data_resp = self._join(ip, port)
          conn.sendall(data_resp)
          
        elif option == REQUEST_DATA:
          id = int(data[1])
          data_resp = self._handler.data(True, id).encode()
          conn.sendall(data_resp)
              
        conn.close()
  
  #iniciar server para escuchar broadcasting
  def _start_broadcast_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      s.bind(('', self._udp_port))
      print(f'Socket broadcast binded to {self._udp_port}')
  
      while(True):
        data_recv = s.recvfrom(1024)
        data = data_recv[0].decode().split('|')
        addr = data_recv[1]
        
        if self._ip != addr[0]:
          print(f'Recived data: {data} from {addr[0]}')
          
        option = data[0]
        
        if option == JOIN:
          if addr[0] != self._ip and self._first:
            send_data(CONFIRM_FIRST, addr[0], self._udp_port, f'{JOIN}|{self._ip}|{self._tcp_port}')
            
        elif option == FIX_FINGER:
          if addr[0] != self._ip:
            ref = NodeReference(addr[0], TCP_PORT)
            self._fix_finger(ref)
          
          else:
            self._finger = [self._succ] * 160
              
        elif option == NOTIFY:
          id = int(data[1])
          
          if addr[0] != self._ip:
            if self._succ.id == id:
              self._succ = NodeReference(addr[0], self._tcp_port)
              send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self._ip}|{self._tcp_port}')
          
          else:
            if self._succ.id == id:
              self._pred = None
              self._succ = self._ref
              self._finger = [self._ref] * 160
        
        elif option == UPDATE_FINGER:
          id = int(data[1])
          sust = NodeReference(addr[0], TCP_PORT)
          
          for i in range(160):
            if self._finger[i].id == id:
              self._finger[i] = sust
              
  #iniciar server udp
  def _start_udp_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self._ip, self._udp_port))
      print(f'Socket UDP binded to ({self._ip}, {self._udp_port})')
      
      while(True):
        data_recv = s.recvfrom(1024)
        data = data_recv[0].decode().split('|')
        addr = data_recv[1]
        print(f'Recived data in UDP socket: {data} from {addr[0]}')
        option = data[0]
        
        if option == CONFIRM_FIRST:
          action = data[1]
          ip = data[2]
          port = int(data[3])
          first = NodeReference(ip, port)
          
          if action == JOIN:            
            data_resp = first.join(self._ip, self._tcp_port).decode().split('|')
            self._pred = NodeReference(data_resp[0], int(data_resp[1]))
            self._succ = NodeReference(data_resp[2], int(data_resp[3]))
        
        elif option == UPDATE_PREDECESSOR:
          ip = data[1]
          port = int(data[2])
          self._pred = NodeReference(ip, port)
          
        elif option == UPDATE_JOIN:
          ip = data[1]
          port = int(data[2])
          self._succ = NodeReference(ip, port)
          
        elif option == DATA_PRED:
          data = data[1]
          self._pred_pred = data
                  
  #iniciar server stabilize
  def _start_stabilize_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self._ip, self._stabilize_port))
      print(f'Socket stabilize binded to ({self._ip}, {self._stabilize_port})')
      s.listen(10)
      
      while True:
        conn, addr = s.accept()
        print(f'new connection in stabilize from {addr}' )
        data = conn.recv(1024).decode().split('|')
        print(f'Recived data: {data}')
        option = data[0]
        
        if option == CHECK_PREDECESOR:
          data = self._handler.data(False) + self._ip
          conn.sendall(f'{data}'.encode('utf-8'))
          
          if self._pred.id != self._succ.id:
            send_data(DATA_PRED, self._succ.ip, self._udp_port, self._pred_info)
            
        elif option == FALL_SUCC:
          ip = data[1]
          port = int(data[2])
          self._succ = NodeReference(ip, port)
          conn.sendall(f'ok'.encode())
          send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self._ip}|{self._tcp_port}')
        
        conn.close()
  ############################################################################################
