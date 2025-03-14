from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from eduplan import bcrypt
from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm
from eduplan import db 
from eduplan.models import study_time, study_event, User
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import re
from eduplan.models import Course

genai.configure(api_key="AIzaSyArG1yXW3d1odahUokxzXgOHejGWrDYxLI")

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/", methods=["GET", "POST"])
def index():
    
    

    if "todo" in request.form:
        todos.append(request.form["todo"])

    return render_template("index.html", todos=todos, template_form=TodoForm())

@main_blueprint.route("/study_planner", methods=["GET", "POST"])
def study_planner():

    event_items = db.session.query(study_time, study_event).join(study_event).all()
    #study_time.query().all()
    event_list = []
    for event, event_info in event_items:
        event_list.append({"date": str(event.date), "user_id": event.user_id, "event_id": event.event_id, "event_description": event_info.event_description})
    #print(jsonify(event_list))

    return render_template("study_planner.html", events=event_list)

@main_blueprint.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_password= bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data,
            email= form.email.data,
            password_hash=hash_password,
            role= 'student'
            )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created')
        return redirect(url_for ('main.login'))
    return render_template("signup.html", form = form)

@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            session['user_id'] = user.id
            session['name'] = user.name
            return redirect(url_for ('main.resources'))
    return render_template("login.html", form=form)

@main_blueprint.route("/resources", methods=["GET", "POST"])
def resources():
    ai_response = None
    if request.method == "POST":
        question = request.form.get("question", "Explain a general study tip.")

        model = genai.GenerativeModel("gemini-2.0-flash")
        response_text = model.generate_content(question).text

        response_text = re.sub(r"[*_]+", "", response_text)

        ai_response = response_text

    return render_template("resources.html", ai_response=ai_response)

@main_blueprint.route("/course_content", methods=["GET", "POST"])
def course_content():
    ai_response = None
    if request.method == "POST":
        question = request.form.get("question", "Explain a general study tip.")

        model = genai.GenerativeModel("gemini-2.0-flash")
        response_text = model.generate_content(question).text

        response_text = re.sub(r"[*_]+", "", response_text)

        ai_response = response_text
    return render_template("course_content.html", ai_response=ai_response)

@main_blueprint.route("/admin", methods=["GET", "POST"])
def admin():
    return render_template("admin.html")

@main_blueprint.route('/api/events')
def get_events():
    event_items = db.session.query(study_time, study_event).join(study_event).all()
    #study_time.query().all()
    event_list = []
    for event, event_info in event_items:
        
        event_list.append(str({"date": str(event.date), "user_id": event.user_id, "event_id": event.event_id, "event_description": event_info.event_description}))
    return jsonify(event_list)
    #return jsonify([dict(event) for event in event_items])

@main_blueprint.route('/home')
def home():
    return render_template('home.html')
