import os
from utils import set_id

def find_user(id: str) -> str:
  for user in os.listdir('db'):
    if set_id(user) == id:
      return f'db/{user}'

class DB:
  @classmethod
  def register(cls, name: str, number: int) -> str:
    #verificar si esta en la db
    if os.path.exists(f'db/{name} - {number}'):
      return('User already exists')
      
    #agregar al nuevo usuario
    os.mkdir(f'db/{name} - {number}')
    
    with open(f'db/{name} - {number}/contacts.txt', 'w') as f:
      f.write('')
      
    return 'Succesful registration'
    
  @classmethod
  def login(cls, name: str, number: int):
    #verificar si esta en la db
    if os.path.exists(f'db/{name} - {number}'):
      with open(f'db/{name} - {number}/contacts.txt') as f:
        return f.read()
    
    return 'User not registred'

  @classmethod
  def add_contact(cls, id: str, name: str, number: int) -> str:
    #referenciar el usuario segun el id
    user = find_user(id)
      
    #validar si el contacto ya existe
    with open(f'{user}/contacts.txt', 'r') as f:
      if f'{name} - {number}\n' in f.readlines():
        return('Contact already exists')
      
    with open(f'{user}/contacts.txt', 'a') as f:
      f.write(f'{name} - {number}\n')
    
    with open(f'{user}/contacts.txt', 'r') as f:
      return(f.read())
      
  @classmethod
  def send_msg(cls, id: str, name: str, number: int, msg: str) -> str:
    user = find_user(id)
    endpoint = f'{name} - {number}'
    
    with open(f'{user}/{endpoint}.txt', 'a') as f:
      f.write(f'[YOU]: {msg}\n')   
      
    with open(f'{user}/{endpoint}.txt', 'r') as f:
      return f.read() 
  
  @classmethod
  def recv_msg(cls, id: str, name: str, number: int, msg: str) -> str:
    #agregar el contacto si no esta
    cls.add_contact(id, name, number)
    user = find_user(id)
    endpoint = f'{name} - {number}'
    
    with open(f'{user}/{endpoint}.txt', 'a') as f:
      f.write(f'[{name}]: {msg}\n')   
      
    with open(f'{user}/{endpoint}.txt', 'r') as f:
      return f.read() 
  
      

  
      
    
  