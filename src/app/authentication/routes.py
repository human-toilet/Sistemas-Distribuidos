#dependencias
from flask import redirect, url_for, render_template
from src.app.authentication import auth
from src.app.authentication.forms import Register, Login

@auth.route('/', methods=['GET', 'POST'])
def root():
  form = Login()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data
    #return redirect(url_for('whatsapp.home'))
    return 'sex'
  
  return render_template('login.html', **context)
  
@auth.route('/register', methods=['GET', 'POST'])
def register():
  form = Register()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data
    #return redirect(url_for('whatsapp.home'))
    return 'sex'
  
  return render_template('register.html', **context)
