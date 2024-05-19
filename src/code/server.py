import socket
import threading

HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'

class Server:
  def __init__(self, ip: str, port: int, sock=None):
    self.ip = ip
    self.port = port
    self.server = sock if sock != None else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.addr = (ip, port)
    self.server.bind(self.addr)
    
  def start(self):
    self.server.listen()
    print(f'[LISTENING] Server is listening on {self.port}')
  
    while(True):
      conn, addr = self.server.accept()
      thraed = threading.Thread(target=self.__handle_client, args=(conn, addr))
      thraed.start()
      print(f'[ACTIVE CONNECTIONS] {threading.activeCount() - 1}')
      
  def __handle_client(self, conn, addr):
    print(f'[NEW CONNECTION] {addr} connected')
    connected = True

    while(connected):
      msg_length = conn.recv(HEADER).decode(FORMAT)
      
      if msg_length:
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)

        if msg == DISCONNECT_MSG:
          connected = False

        print(f'[CLIENT: {addr}] {msg}')
        response = input('[YOU]: ')
        conn.send(response.encode(FORMAT))

    conn.close()