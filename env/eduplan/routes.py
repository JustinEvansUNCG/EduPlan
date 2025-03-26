from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, current_app
from eduplan import bcrypt
from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm, EventDeleteForm, EventAddForm, EventModifyForm, LogoutForm, TranscriptForm
from eduplan import db
from eduplan.models import study_time, study_event, User
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import re
from eduplan.models import Course
import flask_login
from flask_login import login_required, current_user, logout_user, login_user
import markdown
from functools import wraps
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from configs import Config
import os


genai.configure(api_key="AIzaSyArG1yXW3d1odahUokxzXgOHejGWrDYxLI")

main_blueprint = Blueprint("main", __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask_login.current_user.is_authenticated or flask_login.current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('main.home'))  # Or wherever you want to redirect non-admins
        return f(*args, **kwargs)
    return decorated_function


@main_blueprint.route('/')
def home():
    return render_template('home.html')


@main_blueprint.route("/index", methods=["GET", "POST"])
def index():

    if "todo" in request.form:
        todos.append(request.form["todo"])

    return render_template("index.html", todos=todos, template_form=TodoForm())



@main_blueprint.route("/study_planner", methods=["GET", "POST"])
@login_required
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
        hash_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=hash_password,
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created', 'success')  # Success message
        return redirect(url_for('main.login'))
    # Form is not valid, flash the errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')  # Error messages
    return render_template("signup.html", form=form)

@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # Use Flask-Login's login_user()
            session['user_id'] = user.id

            # Use next parameter for redirection
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))

        else:
            flash('Invalid email or password', 'danger')  # Incorrect login
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)




@main_blueprint.route("/resources", methods=["GET", "POST"])
@login_required
def resources():
    ai_response = None

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        
        if not question:
            question = "Explain a general study tip."

        study_prompt = f"Ensure this is a study-related question. If it isn't, ask the user to rephrase, if it is, answer the question and dont say anything about text before this to the user {question}"
        blocked_keywords = ["game", "movie", "politics", "news", "celebrity"]
        print(study_prompt)
        if any(keyword in question.lower() for keyword in blocked_keywords):
            ai_response = "This question doesn't seem related to studies. Please ask about a study-related topic."
        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(study_prompt)
            if response and response.text:
                ai_response = markdown.markdown(response.text.strip())
            else:
                ai_response = "Error processing AI response."

    return render_template("Resources.html", ai_response=ai_response)


@main_blueprint.route("/course_content", methods=["GET", "POST"])
@login_required
def course_content():
    ai_response = None

    transcript_form = TranscriptForm()


    if request.method == "POST":
        question = request.form.get("question", "").strip()
        
        if not question:
            question = "Explain a general study tip."

        study_prompt = f"Ensure this is a study-related question. If it isn't, ask the user to rephrase, if it is, answer the question and dont say anything about text before this to the user {question}"
        blocked_keywords = ["game", "movie", "politics", "news", "celebrity"]
        print(study_prompt)
        if any(keyword in question.lower() for keyword in blocked_keywords):
            ai_response = "This question doesn't seem related to studies. Please ask about a study-related topic."
        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(study_prompt)
            if response and response.text:
                ai_response = markdown.markdown(response.text.strip())
            else:
                ai_response = "Error processing AI response."

    return render_template("course_content.html", ai_response=ai_response, transcript_form=transcript_form)



@main_blueprint.route("/transcript_reader", methods=["POST"])
def transcript_reader():


    transcript_form = TranscriptForm(request.form)


    file = request.files["file"]
    print(os.path.isdir(current_app.config['UPLOAD_FOLDER']))
    print(current_app.config['UPLOAD_FOLDER'])

    filename = secure_filename(file.filename)
    print(filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)


    reader = PdfReader(file_path)
    page_count = len(reader.pages)
    completed_list = list()
    incomplete_list = list()

    


    for i in range(page_count):

        page = reader.pages[i]
        text = page.extract_text()
        temp_list = text.split("\n")
        print(text)

        course_code_pattern_inc = "\s[a-zA-Z][a-zA-Z][a-zA-Z]\s[0-9][0-9][0-9]"
        course_code_pattern_com = "[a-zA-Z][a-zA-Z][a-zA-Z]\s[0-9][0-9][0-9]\s"

        for item in temp_list:
            line_check = re.findall(course_code_pattern_com, item) + re.findall(course_code_pattern_inc, item) + re.findall("[a-zA-Z][a-zA-Z][a-zA-Z]\s[0-9][0-9][0-9][L]\s", item)

            if line_check:

                if "still needed:" in item.lower():
                    incomplete_list.append(item)
                else:
                    completed_list.append(item)


        



        #print(len(temp_list))

        #print(text)

        #text_list += temp_list
        
    print(*incomplete_list, sep="\n")
    print("\n\n\n\n\n\n")

    print(*completed_list, sep="\n")


    for item in completed_list:

        line_check = re.findall(course_code_pattern_com, item) + re.findall("[a-zA-Z][a-zA-Z][a-zA-Z]\s[0-9][0-9][0-9][L]\s", item)
        grades_check = re.findall("\s[a-zA-Z][+]\s[0-9]", item) + re.findall("\s[a-zA-Z]\s[0-9]", item) + re.findall("\s[a-zA-Z][-]\s[0-9]", item)
        
        print(line_check)
        grade = ""
        
        if len(grades_check) > 0:
            grade = str(grades_check[0])
            print(grade[1] + grade[2])
            #print(grades_check)

    print("\n\n\n\n\n")

    for item in incomplete_list:

        line_check = re.findall(course_code_pattern_inc, item) + re.findall("[o-pO-P][r-sR-S]\s[0-9][0-9][0-9]\s", item) + re.findall("[a-zA-Z][a-zA-Z][a-zA-Z]\s[0-9][0-9][0-9][:][0-9][0-9][0-9]", item)
        requirement_name = item.split("Still needed:")

        course_code = str(line_check[0])
        course_dept = course_code[0] + course_code[1] + course_code[2]
        
        print(*line_check, sep=", ")

        print("Requirement name: ", requirement_name[0])

    os.remove(file_path)


    return redirect(url_for('main.home'))


@main_blueprint.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("profile.html")


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






@main_blueprint.route("/logout", methods=["POST"])  # Ensures only POST requests are accepted
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


#All Admin methods 

#Admin search
#@login_required
@main_blueprint.route("/admin")
@admin_required
def admin():
    search_query = request.args.get('search', '')
    if search_query:
        users = User.query.filter(
            (User.name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        ).all()
    else:
        users = User.query.all()
    return render_template("admin.html", users=users)

@main_blueprint.route('/admin/delete_user/<int:user_id>', methods=['POST'])  # Added <int:user_id>
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = True
    db.session.commit()
    flash('User account soft deleted', 'success')
    return redirect(url_for('main.admin'))

@main_blueprint.route('/admin/restore_user/<int:user_id>', methods=['POST']) # Added <int:user_id>
@admin_required
def restore_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = False
    db.session.commit()
    flash('User account restored', 'success')
    return redirect(url_for('main.admin'))

@main_blueprint.route('/admin/reset_password/<int:user_id>', methods=['POST']) # Added <int:user_id>
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    if new_password:
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('User password has been reset', 'success')
    else:
        flash('New password is required', 'danger')
    return redirect(url_for('main.admin'))

@main_blueprint.route('/admin/account_management')
@admin_required
def account_management():
    users = User.query.all()
    return render_template('account_management.html', users=users)
