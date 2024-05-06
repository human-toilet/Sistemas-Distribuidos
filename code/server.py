import socket
import threading

PORT = 5050
IP = socket.gethostbyname(socket.gethostname())
ADDR = (IP, PORT)
HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MSG = '!DISCONNECT'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
  print(f'[NEW CONNECTION] {addr} connected')
  connected = True
  
  while(connected):
    msg_length = conn.recv().decode(FORMAT)
    msg_length = int(msg_length)
    msg = conn.recv(msg_length).decode(FORMAT)
    
    if msg == DISCONNECT_MSG:
      connected = False
      
    print(f'[{addr}] {msg}')
  
  conn.close()
    
def start():
  server.listen()
  print(f'[LISTENING] Server is listening on {IP}')
  
  while(True):
    conn, addr = server.accept()
    thraed = threading.Thread(target=handle_client, args=(conn, addr))
    thraed.start()
    print(f'[ACTIVE CONNECTIONS] {threading.activeCount() - 1}')
    
print('[STARTING] Server is starting...')
start()