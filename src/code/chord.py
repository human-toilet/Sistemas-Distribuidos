#dependencias
from src.code.db import DB
from src.code.comunication import NodeReference, BroadcastRef, send_data
from src.code.comunication import REGISTER, LOGIN, ADD_CONTACT, SEND_MSG, RECV_MSG, GET
from src.code.comunication import JOIN, CONFIRM_FIRST, FIX_FINGER, FIND_FIRST, REQUEST_DATA, CHECK_PREDECESOR, NOTIFY, UPDATE_PREDECESSOR, UPDATE_FINGER, UPDATE_SUCC, DATA_PRED, FALL_SUCC
from src.code.db import DIR
from src.code.handle_data import HandleData
from src.utils import set_id, get_ip, create_folder
import queue
import socket
import threading
import time

TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP

#server
class Server:
  def __init__(self):
    self._ip = get_ip() #ip
    self._id = set_id(self._ip) #id
    self._tcp_port = TCP_PORT #puerto del socket tp
    self._udp_port = UDP_PORT #puerto del socket udp
    self._ref = NodeReference(self._ip, self._tcp_port) #referencia a mi mismo para la finger table
    self._broadcast = BroadcastRef() #comunicacion por broadcast
    self._handler = HandleData(self._id) #manejar la data de la db
    self._succ = self._ref #inicialmente soy mi sucesor
    self._pred = None #inicialmente no tengo predecessor
    self._pred_info = '' #data replicada por mi predecesor
    self._pred_pred = '' #data del predecesor de mi predecesor
    self._finger = [self._ref] * 160 #finger table
    self._leader: bool #saber si soy el lider
    self._first: bool #saber si soy el primer nodo
    self._fix_finger_queue = queue.Queue() #cola de mensajes para arreglar la "finger table"
    self._update_finger_queue = queue.Queue() #cola de mensajes para actualizar la "finger table"
    
    #hilos
    threading.Thread(target=self._start_broadcast_server).start()
    threading.Thread(target=self._start_tcp_server).start()
    threading.Thread(target=self._start_udp_server).start()
    threading.Thread(target=self._set_leader).start()
    threading.Thread(target=self._set_first).start()
    threading.Thread(target=self._info).start()
    threading.Thread(target=self._check_predecessor).start()
    threading.Thread(target=self._handle_fix_finger).start()
    threading.Thread(target=self._handle_update_finger).start()
    
    #ejecutar al unirme a la red
    create_folder(f'{DIR}/db')
    self._broadcast.join() 
    time.sleep(2) #esperar 2 segundos entre el 'join' y el 'fix finger'
    self._broadcast.fix_finger() 
    time.sleep(2) #esperar 2 segundos entre el 'fix finger' y el 'request data'
    self._request_data(pred=True) if self._id > self._succ.id else self._request_data(succ=True)
    print('Ready for use')
  
  ############################### OPERACIONES CHORD ##########################################
  #unir un nodo a la red
  def _join(self, ip: str, port: str) -> bytes:
    id = set_id(ip)
    
    #si estoy solo en la red soy tu sucesor y tu predecesor
    if self._pred == None:
      response = f'{self._ip}|{self._tcp_port}|{self._ip}|{self._tcp_port}'
      self._pred = NodeReference(ip, port)
      self._succ = NodeReference(ip, port)
      return response.encode()
      
    #si tu id es menor, entonces estas entre tu mi predecesor y yo
    elif id < self._id:
      response = f'{self._pred.ip}|{self._pred.port}|{self._ip}|{self._tcp_port}'
      send_data(UPDATE_SUCC, self._pred.ip, self._udp_port, f'{ip}|{port}')
      self._pred = NodeReference(ip, port)
      return response.encode()
    
    #si eres mayor que yo pero yo soy el "lider", entonces estas entre el "first" y yo
    elif self._leader:
        response = f'{self._ip}|{self._tcp_port}|{self._succ.ip}|{self._succ.port}'
        send_data(UPDATE_PREDECESSOR, self._succ.ip, self._udp_port, f'{ip}|{port}')
        self._succ = NodeReference(ip, port)
        return response.encode()

    #acotamos x debajo y le dejamos la tarea al siguiente nodo
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
  def _fix_finger(self, node: NodeReference, id=None):
    for i in range(160): 
      if id == None:
        if node.id < self._finger[i].id:
          #si el nodo entrante es menor que el nodo en cuestion y se puede hacer cargo de ese id, actualizamos
          if self._id + (2 ** i) <= node.id:
            self._finger[i] = node

        #si el nodo entrante es mayor, pero el nodo en cuestion esta manejando un dato de mayor id que el
        elif self._finger[i].id < self._id + 2 ** i:
            self._finger[i] = node
      
      #si el parametro id tiene valor, lo que hacemos es sustituir el nodo entrante x el nodo del id pasado por parametro
      else:
        if self._finger[i].id == id:
          self._finger[i] = node  
      
  #escoger el nodo mas cercano en la busqueda logaritmica
  def _closest_preceding_finger(self, id: int) -> NodeReference:
    for i in range(160):
      if self._id + (2 ** i) > id:
        return self._finger[i - 1]
  
  #encontrar el nodo 'first'
  def _find_first(self) -> bytes:
    if self._leader:
      return f'{self._succ.ip}|{self._succ.port}'.encode()
    
    response = self._finger[-1].find_first()
    return response
  
  #pedirle data a mi sucesor
  def _request_data(self, pred=False, succ=False):
    #si no estoy solo
    if self._succ.id != self._id:
      if succ:
        response_succ = self._succ.request_data(self._id).decode()
        self._handler.create(response_succ)
          
      if pred:
        response_pred = self._pred.request_data(self._id).decode()
        self._handler.create(response_pred)
        
  #pedirle data a mi predecesor cada 5 segundos   
  def _check_predecessor(self):
    while True:
      #si no estoy solo
      if self._pred != None:
        try:
          with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self._pred.ip, self._pred.port)) #nos conectamos x via TCP al predecesor
            s.settimeout(5) #configuramos el socket para lanzar un error si no recibe respuesta en 5 segundos
            s.sendall(CHECK_PREDECESOR.encode('utf-8')) #chequeamos que no se ha caido el predecesor
            self._pred_info = s.recv(1024).decode() #guardamos la info enviada
            ip_pred_pred = self._pred_info.split('|')[-1] #guardamos el id del predecesor de nuestro predecesor

        except:
          #al no recibir respuesta, intuimos que se cayo y procedemos a guardar la data que nos envio
          print(f'Socket ({self._pred.ip}, {self._pred.port}) disconnected')
          self._handler.create(self._pred_info)
          #le comunicamos al resto que se cayo el predecesor y pedimos que actuailice:
          #si somos el "first", significa que se cayo el lider, y se deben actualizar las "finger tables" con el predecesor del lider
          #de lo contrario, que se actualicen con nosotros
          self._broadcast.update_finger(self._pred.id, ip_pred_pred if self._first else self._ip, TCP_PORT)
          
          #nos aseguramos de que al menos habia 3 nodos
          if ip_pred_pred != self._ip:
            try:  
              #tratamos de conectarnos con el predecesor de nuestro predecesor para comunicarle que se cayo su sucesor
              #seguimos el mismo proceso
              with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_pred_pred, TCP_PORT))
                s.settimeout(5)
                s.sendall(f'{FALL_SUCC}|{self._ip}|{self._tcp_port}')
                s.recv(1024).decode()

            except:
              #en este punto, el predecesor de nuestro predecesor tambien se cayo, por lo que tambien salvamos sus datos
              print(f'Socket {ip_pred_pred} disconnected too')
              self._handler.create(self._pred_pred)

              #si al menos somos 4, pregunto quien es el sucesor del nodo caid
              if ip_pred_pred != self._succ.ip:
                self._broadcast.notify(set_id(ip_pred_pred))

          #eramos 2 nodos, por lo que al caerse 2, nos quedamos solos, por lo que toca resetearnos
          else:
            self._pred = None
            self._succ = self._ref
            self._finger = [self._ref] * 160

        time.sleep(5)
        
  #arreglar la "finger table" constantemente
  def _handle_fix_finger(self):
    while True:
      ip, port = self._fix_finger_queue.get()
      
      try:
        #arreglar la "finger table" siempre que haya data
        ref = NodeReference(ip, port)
        self._fix_finger(ref)
        print('Finger table fixed!')
        
      finally:
        self._fix_finger_queue.task_done()
        
  #actualizar la "finger table" constantemente
  def _handle_update_finger(self):
    while True:
      ip, port, id = self._update_finger_queue.get()
      
      try:
        #actualizar la "finger table" siempre que haya data
        ref = NodeReference(ip, port)
        self._fix_finger(ref, id)
        print('Finger table updated')
        
      finally:
        self._update_finger_queue.task_done()
  ############################################################################################ 
  
  ############################## INTERACCIONES CON LA DB #####################################
  #registrar un usuario
  def register(self, id: int, name: str, number: int) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.register(name, number)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).register(id, name, number)
    return response
  
  #logear a un usuario
  def login(self, id: int, name: str, number: int) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.login(name, number)
      print(response)
      return response.encode()

    response = self._closest_preceding_finger(id).login(id, name, number)
    print(response)
    return response
  
  #un usuario agreaga un contacto
  def add_contact(self, id: int, name: str, number: int) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.add_contact(id, name, number)
      print(response)
      return response.encode()

    response = self._closest_preceding_finger(id).add_contact(id, name, number)
    return response
  
  #un usuario envia un sms
  def send_msg(self, id: int, name: str, number: int, msg: str) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.send_msg(id, name, number, msg)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).send_msg(id, name, number, msg)
    print(response)
    return response
  
  #un usuario recibe un sms
  def recv_msg(self, id: int, name: str, number: int, msg: str) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.recv_msg(id, name, number, msg)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).recv_msg(id, name, number, msg)
    print(response)
    return response
  
  #operaciones get
  def get(self, id: int, endpoint: str) -> str:
    #si el dato tiene menor id que nosotros, le pedimos al "first" que haga la operacion
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
    #si el dato tiene menor id que nosotros o tiene mayor id pero somos el "lider", nos encargamos de el
    if (id < self._id) or (id > self._id and self._leader):
      response = DB.get(id, endpoint)
      print(response)
      return response.encode()
    
    response = self._closest_preceding_finger(id).get(id, endpoint)
    print(response)
    return response
  ############################################################################################
  
  ################################### HANDLING SOCKETS #######################################
  #manejar varias peticiones en el socket TCP
  def _handle_client_tcp(self, conn: socket, addr: tuple):
    print(f'new connection in TCP from {addr[0]}' )
    data = conn.recv(1024).decode().split('|')
    print(f'Recived data: {data}')
    option = data[0]

    if option == FIND_FIRST:
      data_resp = self._find_first()

    elif option == REGISTER:
      id = int(data[1])
      name = data[2]
      number = str(data[3])
      data_resp = self._register(id, name, number)

    elif option == LOGIN:
      id = int(data[1])
      name = data[2]
      number = str(data[3])
      data_resp = self._login(id, name, number)

    elif option == ADD_CONTACT:
      id = int(data[1])
      name = data[2]
      number = str(data[3])
      data_resp = self._add_contact(id, name, number)

    elif option == SEND_MSG:
      id = int(data[1])
      name = data[2]
      number = str(data[3])
      msg = data[4]
      data_resp = self._send_msg(id, name, number, msg)

    elif option == RECV_MSG:
      id = int(data[1])
      name = data[2]
      number = str(data[3])
      msg = data[4]
      data_resp = self._recv_msg(id, name, number, msg)

    elif option == GET:
      id = int(data[1])
      endpoint = data[2]
      data_resp = self._get(id, endpoint)

    elif option == JOIN:
      ip = data[1]
      port = int(data[2])
      data_resp = self._join(ip, port)

    elif option == REQUEST_DATA:
      id = int(data[1])
      data_resp = self._handler.data(True, id).encode()
       
    elif option == CHECK_PREDECESOR:
      data_resp = (self._handler.data(False) + self._pred.ip).encode()
      
      #si somos al menos 3 nodos, le mando a mi sucesor la data de mi predecesor
      if self._pred.id != self._succ.id:
        send_data(DATA_PRED, self._succ.ip, self._udp_port, self._pred_info)
            
    elif option == FALL_SUCC:
      ip = data[1]
      port = int(data[2])
      self._succ = NodeReference(ip, port)
      data_resp = f'ok'.encode()
      self._request_data(succ=True) #pido data a mi sucesor al actualizar mi posicion
      send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self._ip}|{self._tcp_port}') #si se cayo mi sucesor, le digo a su sucesor que soy su  nuevo predecesor 
      
    conn.sendall(data_resp)
    conn.close()
  
  #manejar varias peticiones broadcast
  def _handle_broadcast(self, data_recv: tuple):
    data = data_recv[0].decode().split('|')
    addr = data_recv[1]
    option = data[0]

    if self._ip != addr[0]:
      print(f'Recived data: {data} from {addr[0]}')

    if option == JOIN:
      #si alguien se unio, le digo que somos el "first", para unirlo posteriormente
      if addr[0] != self._ip and self._first:
        send_data(CONFIRM_FIRST, addr[0], self._udp_port, f'{self._ip}|{self._tcp_port}')

    elif option == FIX_FINGER:
      if addr[0] != self._ip:
        #si tenemos menor id que el nodo que se unio, ponemos en la cola su id  para actualizar nuestra "finger table"
        if self._id < set_id(addr[0]):
          self._fix_finger_queue.put((addr[0], TCP_PORT))
        
        #si tenemos mayor id, le decimos que nos ponga a nosotros en su finger table
        else:  
          send_data(FIX_FINGER, addr[0], UDP_PORT)

    elif option == NOTIFY:
      id = int(data[1])

      if addr[0] != self._ip:
        #si se cayo mi sucesor, me actualizo con quien lo notifico, le pido data si tiene y le comunico que se actualice conmigo
        if self._succ.id == id:
          self._succ = NodeReference(addr[0], self._tcp_port)
          self._request_data(succ=True)
          send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self._ip}|{self._tcp_port}')
          #si el nodo que me notifico tiene menor id que yo, que actualicen al nodo caido conmigo, pues soy el nuevo lider
          #en caso contrario, que actualicen con el nodo notificante
          self._broadcast.update_finger(id, self._ip if self._id > set_id(addr[0]) else addr[0], TCP_PORT)

      else:
        #si el nodo caido resulta ser mi sucesor, significa que eramos 3, por lo que me quedo solo y me reinicio
        if self._succ.id == id:
          self._pred = None
          self._succ = self._ref
          self._finger = [self._ref] * 160

    elif option == UPDATE_FINGER:
      id = int(data[1])
      ip = data[2]
      port = int(data[3])
      
      #si tengo menor id que el nodo que hay que actualizar, actualizo, ya que sale en mi "finger table"
      if self._id < id:
        self._update_finger_queue.put((ip, port, id))
          
  #manejar varias peticiones en el socket UDP
  def _handle_client_udp(self, data_recv: tuple):
    data = data_recv[0].decode().split('|')
    addr = data_recv[1]
    print(f'Recived data in UDP socket: {data} from {addr[0]}')
    option = data[0]
    
    #al recibir la confirmacion del nodo "first", le solicito la union al anillo
    if option == CONFIRM_FIRST:
      ip = data[1]
      port = int(data[2])
      first = NodeReference(ip, port)             
      data_resp = first.join(self._ip, self._tcp_port).decode().split('|')
      self._pred = NodeReference(data_resp[0], int(data_resp[1]))
      self._succ = NodeReference(data_resp[2], int(data_resp[3]))
    
    elif option == UPDATE_PREDECESSOR:
      ip = data[1]
      port = int(data[2])
      self._pred = NodeReference(ip, port)
      
    elif option == UPDATE_SUCC:
      ip = data[1]
      port = int(data[2])
      self._succ = NodeReference(ip, port)
      
    elif option == DATA_PRED:
      data = data[1]
      self._pred_pred = data
      
    elif option == FIX_FINGER:
      self._fix_finger_queue.put((addr[0], TCP_PORT))
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
        client = threading.Thread(target=self._handle_client_tcp, args=(conn, addr))
        client.start()
  
  #iniciar server para escuchar broadcasting
  def _start_broadcast_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
      s.bind(('', self._udp_port))
      print(f'Socket broadcast binded to {self._udp_port}')
  
      while(True):
        data_recv = s.recvfrom(1024)
        thread = threading.Thread(target=self._handle_broadcast, args=(data_recv,))
        thread.start()
              
  #iniciar server udp
  def _start_udp_server(self):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((self._ip, self._udp_port))
      print(f'Socket UDP binded to ({self._ip}, {self._udp_port})')
      
      while(True):
        data_recv = s.recvfrom(1024)
        client = threading.Thread(target=self._handle_client_udp, args=(data_recv,))
        client.start()
  ############################################################################################
