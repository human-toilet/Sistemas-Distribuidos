#dependencias
from flask import redirect, url_for, render_template, flash
from src.app.auth import auth, server
from src.app.auth.forms import *
from src.utils import set_id

#id del usuario en el anillo
ID: str

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
    return redirect(url_for('auth.homepage', data=''))
  
  return render_template('register.html', **context)

@auth.route('/homepage')
def homepage(data: str):
  context = {'contacts': data.split('\n')} 
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


