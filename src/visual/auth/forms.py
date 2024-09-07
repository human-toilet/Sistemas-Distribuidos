#dependencias
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, ValidationError
from wtforms.validators import DataRequired, Length, NumberRange

def _validate_field(form, field):
  if field.data.strip() == '':
    raise ValidationError("field can't be empty")

#formulario de la vista 'register'
class Register(FlaskForm):
  username = StringField('username', validators=[DataRequired(), Length(1, 16, message='max 16 characters'), _validate_field])
  number = IntegerField('number', validators=[DataRequired(), NumberRange(min=10000000, message='invalid number (8 digits required)'), _validate_field])
  submit = SubmitField('sign up')
  
#formulario de la vista 'login'
class Login(FlaskForm):
  username = StringField('username', validators=[DataRequired(), _validate_field])
  number = IntegerField('number', validators=[DataRequired(), _validate_field])
  submit = SubmitField('sign in')
  
#formulario de la vista 'add_contact'
class AddContact(FlaskForm):
  name = StringField('name', validators=[DataRequired(), Length(1, 16, message='max 16 characters'), _validate_field])
  number = IntegerField('number', validators=[DataRequired(), NumberRange(min=10000000, message='invalid number (8 digits required)'), _validate_field])
  submit = SubmitField('add contact')
  
#formulario para enviar mensajes
class SendMSG(FlaskForm):
  text = StringField('text', validators=[DataRequired(), _validate_field])
  submit = SubmitField('send')
  