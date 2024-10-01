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
      
    return f'Succesfully registrated user: {name}'
    
  #logear un usuario
  @classmethod
  def login(cls, name: str, number: int) -> str:
    #verificar si esta en la db
    if os.path.exists(f'{DIR}/db/{name} - {number}'):
      return f'Succesful login user: {name}'
    
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
      
    with open(f'{user}/{name} - {number}.txt', 'w') as f:
      f.write('')
    
    return f'Succesfully added contact: {name} - {number}'
   
  #enviar un sms   
  @classmethod
  def send_msg(cls, id: int, name: str, number: int, msg: str) -> str:
    user = find_user(id)
    endpoint = f'{name} - {number}'
    
    with open(f'{user}/{endpoint}.txt', 'a') as f:
      f.write(f'[You]: {msg}\n' if msg.strip() != '' else '')
      
    return f'Message sent by {name}: {msg}'    
  
  #recibir un sms
  @classmethod
  def recv_msg(cls, id: int, name: str, number: int, msg: str) -> str:
    user = find_user(id)
    
    if user != None:
      cls.add_contact(id, name, number)
      endpoint = f'{name} - {number}'
    
      with open(f'{user}/{endpoint}.txt', 'a') as f:
        f.write(f'[{name}]: {msg}\n')   

      return f'Message recivied from {name}: {msg}'
    
    return 'User not registred'
  
  #get 
  @classmethod
  def get(cls, id: int, endpoint: str) -> str:
    #referenciar el usuario segun el id
    user = find_user(id)
    
    with open(f'{user}/{endpoint}.txt', 'r') as f:
      return f.read().strip()
