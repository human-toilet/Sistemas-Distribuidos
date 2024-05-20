#dependencias
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo

#formulario de la vista 'register'
class Register(FlaskForm):
  username = StringField('username', validators=[DataRequired(), Length(4, 16, message='between 4 and 16 characters')])
  email = StringField('email', validators=[DataRequired(), Email()])
  password = PasswordField('password', validators=[DataRequired(), EqualTo('confirm', message='passwords must match')])
  confirms = PasswordField('password', validators=[DataRequired()])
  submit = SubmitField('register')
  
#formulario de la vista 'login'
class Login(FlaskForm):
  username = StringField('username', validators=[DataRequired()])
  password = PasswordField('password', validators=[DataRequired()])
  submit = SubmitField('login')