from flask import redirect, url_for, render_template
from app import authentication
from app.forms import Register, Login

@authentication.route('/register', method=['GET'])
def register():
  form = Register()
  
  context = {
    'form': form
  }
  
  if form.validate_on_submit():
    return redirect(url_for('authentication.homepage'))
  
  return render_template('register.html', **context)

@authentication.route('/', method=['GET'])
def root():
  form = Login()
  
  if form.validate_on_submit():
    return redirect(url_for('authentication.homepage'))
  
  return render_template('login.html')
  
  

