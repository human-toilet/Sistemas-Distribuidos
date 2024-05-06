import socket

HEADER = 64
FORMAT = 'utf-8'

class Client:
  def __init__(self, ip: str, port: str, sock=None):
    self.ip = ip
    self.port = port
    self.client = sock if sock != None else socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.addr = (ip, port)
    self.client.connect(self.addr)

  def send(self, msg: str):
    message = msg.encode(FORMAT)
    data_len = str(len(message)).encode(FORMAT)
    data_len += b' ' * (HEADER - len(data_len))
    self.client.send(data_len)
    self.client.send(message)
    print(f'[SERVER] {self.client.recv(2048).decode(FORMAT)}')

  