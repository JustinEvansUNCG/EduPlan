from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


todos = ["Learn Flask", "Setup venv", "Build a cool app"]

#basic flask form
class TodoForm(FlaskForm):
    todo = StringField("Todo")
    submit = SubmitField("Add Todo")