from code.client import Client

client = Client('127.0.0.1', 5050)

while True:
  message = input('[YOU]: ')
  
  if message == '!DISCONNECT':
    client.send(message)
    break
  
  client.send(message)