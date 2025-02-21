from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField


app = Flask(__name__)

# This is needed to use forms, but will be kept in a more secret place at a later date
app.secret_key="anystringhere"

todos = ["Learn Flask", "Setup venv", "Build a cool app"]

#basic flask form
class TodoForm(FlaskForm):
    todo = StringField("Todo")
    submit = SubmitField("Add Todo")

#basic index page that allows a user to add an item to a list
@app.route('/', methods=["GET", "POST"])
def index():
    if 'todo' in request.form:
        todos.append(request.form['todo'])
    #render_template allows loading of an html file with other data such as lists, and is how we can add its to the todos variable defined above
    return render_template('index.html', todos = todos, template_form = TodoForm())


