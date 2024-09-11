#dependencias
from flask import redirect, url_for, render_template, flash, request
from src.visual.auth import auth, server
from src.visual.auth.forms import Register, Login, AddContact, SendMSG
from src.utils import set_id

#ruta del logear un usuario
@auth.route('/', methods=['GET', 'POST'])
def login():
  form = Login()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data.strip()
    number = form.number.data
    response = server.login(set_id(f'{username} - {number}'), username, int(number))
    
    if response == 'User not registred':
      return render_template('login.html', **context)
    
    return redirect(url_for('auth.homepage', id=set_id(f'{username} - {number}'), my_name=username, my_number=number))
  
  return render_template('login.html', **context)
  
#ruta de registrar
@auth.route('/register', methods=['GET', 'POST'])
def register():
  form = Register()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data.strip()
    number = form.number.data
    response = server.register(set_id(f'{username} - {number}'), username, int(number))
  
    if response == 'User already exists':
      flash(response)
      return render_template('register.html', **context)
    
    return redirect(url_for('auth.homepage', id=set_id(f'{username} - {number}'), my_name=username, my_number=number))
  
  return render_template('register.html', **context)

#ruta de la homepage
@auth.route('/homepage')
def homepage():
  id = int(request.args.get('id'))
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  data = server.get(id, 'contacts')
  parse_data = data.split('\n')
  context = {
    'contacts': parse_data if not '' in parse_data else [],
    'id': id,
    'my_name': my_name,
    'my_number': my_number} 
  return render_template('homepage.html', **context)

#rutar para agregar un contacto
@auth.route('/add_contact', methods=['GET', 'POST'])
def add_contact():
  id = int(request.args.get('id'))
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  form = AddContact()
  context = {
    'form': form,
    'id': id,
    'my_name': my_name, 
    'my_number': my_number
    }
  
  if form.validate_on_submit():
    username = form.name.data.strip()
    number = form.number.data
    response = server.add_contact(id, username, int(number))
  
    if response == 'Contact already exists':
      return render_template('add_contact.html', **context)
    
    return redirect(url_for('auth.homepage', id=id, my_name=my_name, my_number=my_number))
  
  return render_template('add_contact.html', **context)

#ruta para chatear
@auth.route('/chat', methods=['GET', 'POST'])
def chat():
  name = request.args.get('name')
  number = request.args.get('number')
  id = int(request.args.get('id'))
  my_name = request.args.get('my_name')
  my_number = request.args.get('my_number')
  chat_state = server.get(id, f'{name} - {number}')
  form = SendMSG()
  
  context = {
    'form': form,
    'id': id,
    'name': name,
    'state': chat_state.split('\n'),
    'my_name': my_name, 
    'my_number': my_number
    }
  
  if form.validate_on_submit():
    msg = form.text.data.strip()
    state = server.send_msg(id, name, int(number), msg)
    server.recv_msg(set_id(f'{name} - {number}'), my_name, int(my_number), msg)
    context['state'] = state.split('\n')
    return render_template('chat.html', **context)
    
  return render_template('chat.html', **context)
