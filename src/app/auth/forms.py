#dependencias
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo

#formulario de la vista 'register'
class Register(FlaskForm):
  username = StringField('username', validators=[DataRequired(), Length(4, 16, message='between 4 and 16 characters')])
  number = IntegerField('number', validators=[DataRequired(), Length(min=8, message='invalid number (8 numbers required)')])
  submit = SubmitField('sign up')
  
#formulario de la vista 'login'
class Login(FlaskForm):
  username = StringField('username', validators=[DataRequired()])
  number = IntegerField('number', validators=[DataRequired()])
  submit = SubmitField('sign in')
  
#formulario de la vista 'add_contact'
class AddContact(FlaskForm):
  name = StringField('name', validators=[DataRequired(), Length(4, 16, message='between 4 and 16 characters')])
  number = IntegerField('number', validators=[DataRequired(), Length(min=8, message='invalid number (8 numbers required)')])
  submit = SubmitField('add contact')
  
#formulario para enviar mensajes
class SendMSG(FlaskForm):
  text = StringField('text', validators=[DataRequired()])
  submit = SubmitField('send')
  