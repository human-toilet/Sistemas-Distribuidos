import socket

PORT = 5050
IP = socket.gethostbyname(socket.gethostname())
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'
ADDR = (IP, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg: str):
  message = msg.encode(FORMAT)
  data_len = str(len(message)).encode(FORMAT)
  data_len += b' ' * (HEADER - len(data_len))
  client.send(data_len)
  client.send(message)
  print(client.recv(2048).decode(FORMAT))

  