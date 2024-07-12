#dependencias
from flask import redirect, url_for, render_template, flash, request
from src.app.auth import auth, server
from src.app.auth.forms import *
from src.utils import set_id

#ruta del logear un usuario
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
    
    return redirect(url_for('auth.homepage', data=response, id=set_id(f'{username} - {number}'),
                            my_name=username, my_number=number))
  
  return render_template('login.html', **context)
  
#ruta de registrar
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
    
    return redirect(url_for('auth.homepage', data='', id=set_id(f'{username} - {number}'),
                            my_name=username, my_number=number))
  
  return render_template('register.html', **context)

#ruta de la homepage
@auth.route('/homepage')
def homepage():
  id = request.args.get('id')
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  data = request.args.get('data')
  parse_data = data.split('\n')
  context = {
    'contacts': parse_data if not '' in parse_data else [],
    'no_parse_contacts': data,
    'id': id,
    'my_name': my_name,
    'my_number': my_number} 
  return render_template('homepage.html', **context)

#rutar para agregar un contacto
@auth.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
  id = request.args.get('id')
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  data = request.args.get('data')
  form = AddContact()
  context = {
    'form': form,
    'id': id,
    'my_name': my_name, 
    'my_number': my_number,
    'data': data
    }
  
  if form.validate_on_submit():
    username = form.name.data
    number = form.number.data
    server.register(set_id(f'{username} - {number}'), username, number)
    response = server.add_contact(id, username, number)
  
    if response == 'Contact already exists':
      flash(response)
      return render_template('add_contact.html', **context)
    
    return redirect(url_for('auth.homepage', data=response, id=id, my_name=my_name, my_number=my_number))
  
  return render_template('add_contact.html', **context)

#ruta para chatear
@auth.route('/chat', methods=['GET', 'POST'])
def chat():
  name = request.args.get('name')
  number = request.args.get('number')
  id = request.args.get('id')
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  data = request.args.get('data')
  chat_state = server.send_msg(id, name, number, '')
  form = SendMSG()
  
  if form.validate_on_submit():
    msg = form.text.data
    chat_state = server.send_msg(id, name, number, msg)
    server.recv_msg(set_id(f'{name} - {number}'), my_name, my_number, msg)
    
  context = {
    'form': form,
    'name': name,
    'state': chat_state.split('\n'),
    'my_name': my_name, 
    'my_number': my_number,
    'data': data
    }
    
  return render_template('chat.html', **context)
  
  