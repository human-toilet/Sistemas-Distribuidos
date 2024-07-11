import hashlib

def set_id(data: str):
  return str(hashlib.sha1(data.encode()).hexdigest())