#dependencias
from flask import redirect, url_for, render_template, flash, request
from src.app.auth import auth, server
from src.app.auth.forms import *
from src.utils import set_id

ID: str #id del usuario en el anillo
NAME: str #mi nombre de usuario
NUMBER: int #mi numero de telefono

@auth.route('/', methods=['GET', 'POST'])
def login():
  form = Login()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data
    number = form.number.data
    response = server.login(set_id(f'{username} - {number}'), username, number)
    
    if response == 'User not registred':
      flash(response)
      return render_template('login.html', **context)
    
    ID = set_id(f'{username} - {number}')
    NAME = username
    NUMBER = number
    return redirect(url_for('auth.homepage', data=response))
  
  return render_template('login.html', **context)
  
@auth.route('/register', methods=['GET', 'POST'])
def register():
  form = Register()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data
    number = form.number.data
    response = server.register(set_id(f'{username} - {number}'), username, number)
  
    if response == 'User already exists':
      flash(response)
      return render_template('register.html', **context)
    
    ID = set_id(f'{username} - {number}')
    NAME = username
    NUMBER = number
    return redirect(url_for('auth.homepage', data=''))
  
  return render_template('register.html', **context)

@auth.route('/homepage')
def homepage():
  #data = request.args.get('data')
  context = {'contacts': ['Maxi - 55555555555', 'May - 55555555555']} 
  return render_template('homepage.html', **context)

@auth.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
  form = AddContact()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.name.data
    number = form.number.data
    response = server.add_contact(ID, username, number)
  
    if response == 'Contact already exists':
      flash(response)
      return render_template('add_contact.html', **context)
    
    return redirect(url_for('auth.homepage', data=response))
  
  return render_template('add_contact.html', **context)

@auth.route('/chat', methods=['GET', 'POST'])
def chat():
  name = request.args.get('name')
  number = request.args.get('number')
  chat_state = server.send_msg(ID, name, number, '')
  form = SendMSG()
  context = {
    'form': form,
    'name': name,
    'state': chat_state.split('\n')
  }
  
  if form.validate_on_submit():
    msg = form.text.data
    chat_state = server.send_msg(ID, name, number, msg)
    server.recv_msg(set_id(f'{name} - {number}'), NAME, NUMBER)
    
  return render_template('chat.html', **context)
  
  