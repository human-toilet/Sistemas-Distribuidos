from flask import redirect, url_for, render_template
from src.app import auth, whatsapp
from src.app.forms import Register, Login

@auth.route('/', methods=['GET', 'POST'])
def root():
  form = Login()
  context = {'form': form}
  
  if form.validate_on_submit():
    username = form.username.data
    #return redirect(url_for('whatsapp.home'))
    return username
  
  return render_template('auth/login.html', **context)
  

