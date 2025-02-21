from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


todos = ["Foo"]

#basic flask form
class TodoForm(FlaskForm):
    todo = StringField("Todo")
    submit = SubmitField("Add Todo")