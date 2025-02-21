from flask import render_template, request
from eduplan import app
from eduplan.forms import TodoForm, todos








#basic index page that allows a user to add an item to a list
@app.route('/', methods=["GET", "POST"])
def index():
    if 'todo' in request.form:
        todos.append(request.form['todo'])
    #render_template allows loading of an html file with other data such as lists, and is how we can add its to the todos variable defined above
    return render_template('index.html', todos = todos, template_form = TodoForm())
