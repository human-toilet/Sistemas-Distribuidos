import hashlib
import os
import socket

#hashear la data
def set_id(data: str):
  return str(hashlib.sha1(data.encode()).hexdigest())

#optener mi ip
def get_ip() -> str:
  with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    try:
        #usamos una IP arbitraria que no se encuentra en nuestra red
        s.connect(('10.254.254.254', 1))
        ip_local = s.getsockname()[0]
        
    except Exception:
        ip_local = '127.0.0.1'
        
    return str(ip_local)

#crear una carpeta en caso de que no exista
def create_folder(path: str):
  if not os.path.exists(path):
    os.makedirs(path)