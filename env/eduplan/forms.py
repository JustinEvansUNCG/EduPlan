from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, HiddenField, TimeField, DateField, SelectField
from wtforms.validators import DataRequired, Length, Email, ValidationError

from eduplan import db
from eduplan.models import study_event
from flask import session


todos = ["Foo"]

#basic flask form
class TodoForm(FlaskForm):
    todo = StringField("Todo")
    submit = SubmitField("Add Todo")

class EventDeleteForm(FlaskForm):
    plan_id = HiddenField('plan_id')
    submit = SubmitField("Delete Event")




class EventAddForm(FlaskForm):
    start_time = TimeField("Start Time")
    end_time = TimeField("End Time")
    date = DateField("date")
    existing_events = SelectField('Events Available', choices=[], validate_choice=False)
    submit = SubmitField("Add Event")


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign up')


        
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')