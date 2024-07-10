import hashlib

def set_id(data: str):
  return int(hashlib.sha1(data.encode()).hexdigest(),16)

