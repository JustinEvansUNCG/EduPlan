from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from eduplan import bcrypt
from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm, EventDeleteForm, EventAddForm, EventModifyForm
from eduplan import db
from eduplan.models import study_time, study_event, User
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import re
from eduplan.models import Course
import flask_login

genai.configure(api_key="AIzaSyArG1yXW3d1odahUokxzXgOHejGWrDYxLI")

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/", methods=["GET", "POST"])
def index():
    
    

    if "todo" in request.form:
        todos.append(request.form["todo"])

    return render_template("index.html", todos=todos, template_form=TodoForm())



@main_blueprint.route("/study_planner", methods=["GET", "POST"])
def study_planner():
    form = EventDeleteForm(request.form)

    add_form = EventAddForm(request.form)

    modify_form = EventModifyForm(request.form)

    event_items = db.session.query(study_event).filter_by(user_id=session['user_id']).all()

    event_list = []
    for event in event_items:
        #event_list.append(str({"event_id": event.event_id, "event_title": event.event_title, "event_description": event.event_description}))
        event_list.append((str(event.event_id), event.event_title))

    add_form.existing_events.choices = event_list

    add_form.existing_events.validate_choice = True


    add_form.validate_on_submit()



    if request.method == 'POST' and form.validate():
        print("Plan id")
        print(form.plan_id.data)
        event = db.session.query(study_time).get(form.plan_id.data)


        #plan_event = study_time(form.plan_id)
        db.session.delete(event)
        db.session.commit()

        flash('Event deleted')
        #return redirect(url_for('login'))


    return render_template("study_planner.html", form=form, add_form=add_form, modify_form=modify_form)

@main_blueprint.route("/study_planner/modify", methods=["POST"])
def modify_study_event():

    modify_form = EventModifyForm(request.form)

    if request.method == 'POST' and modify_form.validate():
        
        print("falalalala")
        planned_event = db.session.query(study_time).get(modify_form.plan_id.data)

        planned_event.start_time = modify_form.start_time.data
        planned_event.end_time = modify_form.end_time.data
        planned_event.date = modify_form.date.data

        

        event = db.session.query(study_event).get((session["user_id"], planned_event.event_id))
        event.event_title = modify_form.event_title.data
        event.event_description = modify_form.event_description.data

        db.session.commit()
    return redirect(url_for('main.study_planner'))




@main_blueprint.route("/study_planner/add", methods=["POST"])
def add_study_event():


    add_form = EventAddForm(request.form)




    #EventAddForm.validate_event(add_form, add_form.existing_events)

    
    if request.method == 'POST' and add_form.validate():
        

        print("whats up")
        print(type(add_form.event_creation_type.data))
        if add_form.event_creation_type.data == "0":
            planned_event = study_time(date = add_form.date.data, event_id = add_form.existing_events.data, start_time = add_form.start_time.data, end_time = add_form.end_time.data)
            db.session.add(planned_event)
            db.session.commit()
        elif add_form.event_creation_type.data == "1":


            
            event = study_event(user_id = session["user_id"], event_title = add_form.event_title.data, event_description = add_form.event_description.data)
            db.session.add(event)
            db.session.commit()

            

            planned_event = study_time(date = add_form.date.data, event_id = event.event_id, start_time = add_form.start_time.data, end_time = add_form.end_time.data)
            db.session.add(planned_event)
            db.session.commit()



        #plan_event = study_time(form.plan_id)
        #db.session.delete(event)
        #db.session.commit()

        #flash('Event deleted')
        #return redirect(url_for('login'))

    return redirect(url_for('main.study_planner'))
    #return render_template("study_planner.html", form=form, add_form=add_form)


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

@main_blueprint.route('/api/event_times')
def get_event_times():
    print(session['user_id'])
    event_items = db.session.query(study_event, study_time).filter_by(user_id=session['user_id']).join(study_time).all()

    event_list = []
    for event, event_time in event_items:
        event_list.append(str({"date": str(event_time.date), "event_id": event.event_id, "event_title": event.event_title, "event_description": event.event_description, "start_time": str(event_time.start_time), "end_time": str(event_time.end_time), "plan_id": event_time.plan_id}))
    return jsonify(event_list)
    #return jsonify([dict(event) for event in event_items])


@main_blueprint.route('/api/events')
def get_events():
    print(session['user_id'])
    event_items = db.session.query(study_event).filter_by(user_id=session['user_id']).all()

    event_list = []
    for event in event_items:
        event_list.append(str({"event_id": event.event_id, "event_title": event.event_title, "event_description": event.event_description}))
    return jsonify(event_list)
    #return jsonify([dict(event) for event in event_items])


@main_blueprint.route('/home')
def home():
    return render_template('home.html')
