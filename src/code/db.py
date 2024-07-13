#dependencias
from src.utils import set_id
import os

#direccion de donde estoy
DIR = os.path.dirname(os.path.abspath(__file__))

#encontrar un usuario segun su id
def find_user(id: int) -> str:
  for user in os.listdir(f'{DIR}/db'):
    if set_id(user) == id:
      return f'{DIR}/db/{user}'

#objeto para encapsular la interaccion del usuario con la db
class DB:
  #registrar un usuario en la db
  @classmethod
  def register(cls, name: str, number: int) -> str:
    #verificar si esta en la db
    if os.path.exists(f'{DIR}/db/{name} - {number}'):
      return 'User already exists'
      
    #agregar al nuevo usuario
    os.mkdir(f'{DIR}/db/{name} - {number}')
    
    with open(f'{DIR}/db/{name} - {number}/contacts.txt', 'w') as f:
      f.write('')
      
    return 'Succesful registration'
    
  #logear un usuario
  @classmethod
  def login(cls, name: str, number: int) -> str:
    #verificar si esta en la db
    if os.path.exists(f'{DIR}/db/{name} - {number}'):
      with open(f'{DIR}/db/{name} - {number}/contacts.txt', 'r') as f:
        return f.read().strip()
    
    return 'User not registred'

  #agregar un contacto
  @classmethod
  def add_contact(cls, id: int, name: str, number: int) -> str:
    #referenciar el usuario segun el id
    user = find_user(id)
      
    #validar si el contacto ya existe
    with open(f'{user}/contacts.txt', 'r') as f:
      if f'{name} - {number}\n' in f.readlines():
        return 'Contact already exists'
      
    with open(f'{user}/contacts.txt', 'a') as f:
      f.write(f'{name} - {number}\n')
    
    with open(f'{user}/contacts.txt', 'r') as f:
      return f.read().strip()
   
  #enviar un sms   
  @classmethod
  def send_msg(cls, id: int, name: str, number: int, msg: str) -> str:
    user = find_user(id)
    endpoint = f'{name} - {number}'
    
    with open(f'{user}/{endpoint}.txt', 'a') as f:
      f.write(f'[YOU]: {msg}\n' if msg.strip() != '' else '')   
      
    with open(f'{user}/{endpoint}.txt', 'r') as f:
      return f.read().strip() 
  
  #recibir un sms
  @classmethod
  def recv_msg(cls, id: int, name: str, number: str, msg: str) -> str:
    #agregar el contacto si no esta
    cls.add_contact(id, name, number)
    user = find_user(id)
    endpoint = f'{name} - {number}'
    
    with open(f'{user}/{endpoint}.txt', 'a') as f:
      f.write(f'[{name}]: {msg}\n')   
      
    with open(f'{user}/{endpoint}.txt', 'r') as f:
      return f.read() 
  
  
      
    
  