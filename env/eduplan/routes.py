from flask import render_template, request, url_for
from eduplan import app
from eduplan.forms import TodoForm, todos








#basic index page that allows a user to add an item to a list
@app.route('/', methods=["GET", "POST"])
def index():
    if 'todo' in request.form:
        todos.append(request.form['todo'])
    #render_template allows loading of an html file with other data such as lists, and is how we can add its to the todos variable defined above
    return render_template('index.html', todos = todos, template_form = TodoForm())

@app.route('/sign_up', methods=["GET", "POST"])
def sign_up():
    return render_template('signup.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    return render_template('login.html')

@app.route('/resources', methods=["GET", "POST"])
def resources():
    return render_template('resources.html')

@app.route('/study_planner', methods=["GET", "POST"])
def study_planner():
    return render_template('study_planner.html')

@app.route('/course_content', methods=["GET", "POST"])
def course_content():
    return render_template('course_content.html')

@app.route('/admin', methods=["GET", "POST"])
def admin():
    return render_template('admin.html')

@app.route('/temp', methods=["GET", "POST"])
def temp():
    return render_template('temp.html')
