from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, current_app
from eduplan import bcrypt

from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm, EventDeleteForm, EventAddForm, EventModifyForm, LogoutForm, TranscriptForm, CourseCatalogUploadForm, EditCourseForm, CanvasTokenForm, PreferencesForm

from eduplan import db
from eduplan.models import study_time, study_event, User, CourseContentAssistance, ClassStatus,CourseResource, assignments, ResourceChat, FavoriteCourse, assignments, StudyPreference, SavedStudyPlan
from flask_bcrypt import Bcrypt
import google.generativeai as genai
import re
from eduplan.models import Course
import flask_login
from flask_login import login_required, current_user, logout_user, login_user
import markdown
from functools import wraps
import fitz
from flask import send_file
import json

from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from configs import Config
import os
import requests
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from math import ceil
from sqlalchemy import or_

from flask_mail import Message
from eduplan import mail
import filetype
from sqlalchemy import cast, Date




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(BASE_DIR, 'api_keys.json')


with open(key_path, 'r') as file:
    data = json.load(file)

gemini_key = data["GeminiAPIToken"]
genai.configure(api_key=gemini_key)

canvas_api_token = data["CanvasAPIToken"]
canvas_api_url = "https://uncg.instructure.com"

main_blueprint = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"  # Ensure this directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not flask_login.current_user.is_authenticated or flask_login.current_user.role != 'admin':
            flash('Unauthorized access', 'danger')
            return redirect(url_for('main.home')) 
        return f(*args, **kwargs)
    return decorated_function



@main_blueprint.route('/')
def home():
    return render_template('home.html')
   

@main_blueprint.route('/test-email')
def test_email():
    msg = Message("Hello from Flask", recipients=["regriffin@uncg.edu"])
    msg.body = "This is a test email sent from your Flask app using Gmail SMTP!"
    mail.send(msg)
    return "Email sent!"

@main_blueprint.route("/index", methods=["GET", "POST"])
def index():

    if "todo" in request.form:
        todos.append(request.form["todo"])

    return render_template("index.html", todos=todos, template_form=TodoForm())


#Route brings you to the calendar page
@main_blueprint.route("/study_planner", methods=["GET", "POST"])
@login_required
def study_planner():

    #forms below are all initialized here so they can be displayed
    form = EventDeleteForm(request.form)
    add_form = EventAddForm(request.form)
    modify_form = EventModifyForm(request.form)

    #db query getting all events for a user
    event_items = db.session.query(study_event).filter_by(user_id=session['user_id']).all()


    event_list = []

    #puts all event titles in a list
    for event in event_items:
        event_list.append((str(event.event_id), event.event_title))

    #Stores list of events as the choices in existing events in add form
    add_form.existing_events.choices = event_list

    #validate form now that all changes to its structure have been made
    add_form.existing_events.validate_choice = True
    add_form.validate_on_submit()


    #This POST request handles planned_event removal
    if request.method == 'POST' and form.validate():
        event = db.session.query(study_time).get(form.plan_id.data)
        db.session.delete(event)
        db.session.commit()

        flash('Event deleted')


    return render_template("study_planner.html", form=form, add_form=add_form, modify_form=modify_form)



#Route handles event modification
@main_blueprint.route("/study_planner/modify", methods=["POST"])
def modify_study_event():

    modify_form = EventModifyForm(request.form)

    if request.method == 'POST' and modify_form.validate():
        
        #Lines below update the parameters of an event
        planned_event = db.session.query(study_time).get(modify_form.plan_id.data)
        planned_event.start_time = modify_form.start_time.data
        planned_event.end_time = modify_form.end_time.data
        planned_event.date = modify_form.date.data

        event = db.session.query(study_event).get((session["user_id"], planned_event.event_id))
        event.event_title = modify_form.event_title.data
        event.event_description = modify_form.event_description.data

        db.session.commit()
    return redirect(url_for('main.study_planner'))



#Route deals with Study_event addition
@main_blueprint.route("/study_planner/add", methods=["POST"])
def add_study_event():


    add_form = EventAddForm(request.form)

    
    if request.method == 'POST' and add_form.validate():
        
        #Makes study time with a preexisting event
        if add_form.event_creation_type.data == "0":
            planned_event = study_time(date = add_form.date.data, event_id = add_form.existing_events.data, start_time = add_form.start_time.data, end_time = add_form.end_time.data)
            db.session.add(planned_event)
            db.session.commit()
        #Makes a new study time with a new event
        elif add_form.event_creation_type.data == "1":


            
            event = study_event(user_id = session["user_id"], event_title = add_form.event_title.data, event_description = add_form.event_description.data)
            db.session.add(event)
            db.session.commit()

            planned_event = study_time(date = add_form.date.data, event_id = event.event_id, start_time = add_form.start_time.data, end_time = add_form.end_time.data)
            db.session.add(planned_event)
            db.session.commit()

    return redirect(url_for('main.study_planner'))


from flask_login import login_user

@main_blueprint.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    form = RegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            password_hash=hash_password,
            role='student'
        )
        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            flash('Account associated with that email already exists', 'danger')
            return render_template("signup.html", form=form)

        session["user_id"] = user.id # This is needed to keep track of who is signed in

        login_user(user)  # ✅ Keep user logged in after sign-up
        flash('Your account has been created and you are now logged in.', 'success')
        return redirect(url_for('main.home'))

    # Show form errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'danger')
    return render_template("signup.html", form=form)


@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # Use Flask-Login's login_user()
            login_user(user)
            session["user_id"] = user.id

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
    chat_id = request.args.get("chat_id")
    canvas_courses = []
    current_chat = None
    messages = []

    if chat_id:
        current_chat = ResourceChat.query.filter_by(id=chat_id, user_id=current_user.id).first()
        if current_chat:
            messages = CourseResource.query.filter_by(chat_id=current_chat.id).order_by(CourseResource.created_at).all()

    try:
        headers = {"Authorization": f"Bearer {canvas_api_token}"}
        params = {
            "enrollment_term_id": 467,
            "per_page": 100,
            "include[]": "enrollments"
        }
        res = requests.get(f"{canvas_api_url}/api/v1/courses", headers=headers, params=params)
        if res.status_code == 200:
            canvas_courses = [
                {
                    "id": course["id"],
                    "name": course["name"],
                    "enrollments": course.get("enrollments", [{}])[0].get("enrollment_state", "unknown")
                }
                for course in res.json()
                if not course.get("access_restricted_by_date") and course.get("enrollment_term_id") == 467
            ]
    except Exception as e:
        print(f"Canvas API error: {e}")

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        selected_course = request.form.get("selected_course", "").strip()
        chat_id = request.form.get("chat_id")

        if not current_chat and chat_id:
            current_chat = ResourceChat.query.filter_by(id=chat_id, user_id=current_user.id).first()

        if not current_chat:
            current_chat = ResourceChat(user_id=current_user.id, title="New Chat")
            db.session.add(current_chat)
            db.session.commit()

        previous_chats = (
            CourseResource.query
            .filter_by(user_id=current_user.id, chat_id=current_chat.id)
            .order_by(CourseResource.created_at.desc())
            .limit(5)
            .all()
        )

        context = ""
        for msg in reversed(previous_chats):
            context += f"User: {msg.question}\nAI: {msg.ai_response}\n"

        course_context = f"This question is related to the course: {selected_course}." if selected_course else ""
        study_prompt = (
            f"{course_context}\n"
            f"Here is the previous conversation context:\n{context}\n"
            f"Make sure the question is study-related and respond clearly.\n"
            f"New Question: {question}"
        )

        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(study_prompt)
        clean_text = response.text.strip()

        course_code_match = re.match(r"[A-Z]{3,4} \d{3}", selected_course)
        course_code = course_code_match.group(0) if course_code_match else None
        course_obj = Course.query.filter_by(course_code=course_code).first()
        course_id = course_obj.course_code if course_obj else None

        entry = CourseResource(
            user_id=current_user.id,
            chat_id=current_chat.id,
            course_id=course_id,
            question=question,
            ai_response=clean_text,
            created_at=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()

        messages = CourseResource.query.filter_by(chat_id=current_chat.id).order_by(CourseResource.created_at).all()

    chats = ResourceChat.query.filter_by(user_id=current_user.id).order_by(ResourceChat.created_at.desc()).all()

    for msg in messages:
        msg.ai_response = markdown.markdown(msg.ai_response)

    return render_template("resources.html", canvas_courses=canvas_courses, chats=chats, messages=messages, current_chat=current_chat)


@main_blueprint.route("/resources/chat/<int:chat_id>/rename", methods=["POST"])
@login_required
def rename_resource_chat(chat_id):
    new_title = request.form.get("new_title", "").strip()
    chat = ResourceChat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()

    if new_title:
        chat.title = new_title
        db.session.commit()
        flash("Chat renamed successfully.", "success")
    else:
        flash("Please provide a valid title.", "warning")

    return redirect(url_for("main.resources", chat_id=chat_id))



@main_blueprint.route("/course_content", methods=["GET", "POST"])
@login_required
def course_content():
    from .models import Course
    ai_response = None
    transcript_form = TranscriptForm()
    transcript = ClassStatus.query.filter_by(user_id=current_user.id).order_by(ClassStatus.course_code).all()
    required_classes = []
    single_required = set()
    for status in transcript:
        if status.completed:
            continue
        raw = status.course_code
        exc_set = set()
        if status.course_exceptions:
            for ex in status.course_exceptions.split(','):
                ex = ex.strip()
                m = re.match(r'^([A-Z]{3,4})\s*(\d+):(\d+)$', ex)
                if m:
                    p, lo, hi = m.groups()
                    exc_set |= {(p, n) for n in range(int(lo), int(hi)+1)}
                else:
                    m2 = re.match(r'^([A-Z]{3,4})\s*(\d+)$', ex)
                    if m2:
                        exc_set.add((m2.group(1), int(m2.group(2))))
        m0 = re.match(r'^([A-Z]{3,4})\s*(.+)$', raw)
        if not m0:
            continue
        prefix, spec = m0.groups()
        parts = spec.split('-')
        nums = set()
        for part in parts:
            if ':' in part:
                lo, hi = part.split(':', 1)
                if lo.isdigit() and hi.isdigit():
                    nums |= set(range(int(lo), int(hi)+1))
            elif part.isdigit():
                nums.add(int(part))
        if len(nums) > 1:
            candidates = Course.query.filter(Course.course_code.startswith(prefix + ' ')).all()
            options = []
            for c in candidates:
                mcode = re.search(r'\d+', c.course_code)
                if mcode:
                    n = int(mcode.group())
                    if n in nums and (prefix, n) not in exc_set and c.course_code not in single_required:
                        options.append(c)
            if options:
                cnt = status.credits // 3 if status.credits else len(options)
                if any(c.course_code in ('PSY 311', 'PSY 410') for c in options):
                    cnt += 1
                required_classes.append(("Group", cnt, options))
        else:
            course = Course.query.filter_by(course_code=raw).first()
            if course:
                single_required.add(course.course_code)
                required_classes.append(("Single", 1, [course]))
    if request.method == "POST":
        question = request.form.get("question", "").strip() or "Explain a general study tip."
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        prev = CourseContentAssistance.query.filter_by(user_id=current_user.id).filter(CourseContentAssistance.created_at >= one_day_ago).order_by(CourseContentAssistance.created_at.desc()).limit(5).all()
        chat_context = "".join(f"User: {c.question}\nAI: {c.ai_response}\n" for c in reversed(prev))
        transcript_context = "\n".join(
            f"{i+1}. {c.course_code} - Grade: {c.grade} (Completed)" if c.completed
            else f"{i+1}. {c.course_code} - Required: Not Yet Taken ({c.credits} credits)"
            for i, c in enumerate(transcript)
        )
        study_prompt = (
            f"Here is the student's academic transcript:\n{transcript_context}\n\n"
            f"Here is the student's previous conversation context:\n{chat_context}\n"
            f"Ensure the question is study-related. If it is not, ask the user to rephrase. "
            f"If it is, just answer the question with a short response unless the student asks for more detail\n"
            f"New Question: {question}"
        )
        if any(k in question.lower() for k in ["game", "movie", "politics", "news", "celebrity"]):
            ai_response = "This question doesn't seem related to studies. Please ask about a study-related topic."
        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(study_prompt)
            clean = response.text.strip() if response and response.text else ""
            ai_response = markdown.markdown(clean)
            entry = CourseContentAssistance(user_id=current_user.id, question=question, ai_response=clean)
            db.session.add(entry)
            db.session.commit()
    return render_template("course_content.html", ai_response=ai_response, transcript_form=transcript_form, required_classes=required_classes)




#This route will handle reading a transcript
@main_blueprint.route("/transcript_reader", methods=["POST"])
def transcript_reader():

    valid = False

    transcript_form = TranscriptForm(request.form)


    file = request.files['file']

    print(os.path.isdir(current_app.config['UPLOAD_FOLDER']))
    print(current_app.config['UPLOAD_FOLDER'])

    #Saves file
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    #try block checks if a file is of type pdf, and rejects otherwise
    try:
        if filetype.guess(file_path).extension is "pdf":
            valid = True   
    except Exception:
        valid = False

    if valid:

        reader = PdfReader(file_path)
        page_count = len(reader.pages)
        course_list = list()

    
    
        #Loop parses the pdf, splitting up document by line
        for i in range(page_count):

            page = reader.pages[i]
            text = page.extract_text()
            temp_list = text.split("\n")
            #print(text)
            if i == 0:
                document = text.split(" ")
                if document[0] != "UNCG":
                    valid = False
                    break

            #A pattern checker that makes sure lines are the lines we want
            course_code_pattern = "Except [A-Z][A-Z][A-Z] [0-9][0-9][0-9]|and [A-Z][A-Z][A-Z] [0-9][0-9][0-9]:[0-9][0-9][0-9]|or [A-Z][A-Z][A-Z] [0-9][0-9][0-9]:[0-9][0-9][0-9]|and [A-Z][A-Z][A-Z] [0-9][0-9][0-9]|or [A-Z][A-Z][A-Z] [0-9][0-9][0-9]|[A-Z][A-Z][A-Z] [0-9][0-9][0-9]:[0-9][0-9][0-9]|[A-Z][A-Z][A-Z] [0-9][0-9][0-9]L|[A-Z][A-Z][A-Z] [0-9][0-9][0-9]|and [0-9][0-9][0-9]L|or [0-9][0-9][0-9]L|and [0-9][0-9][0-9]|or [0-9][0-9][0-9]"
            

            #Keeps lines that contain the pattern in course_code_pattern
            for item in temp_list:
                line_check = re.findall(course_code_pattern, item)

                if line_check:
                    
                    item = item.replace("  ", " ")
                    course_list.append(item)



        incomplete_list = dict()
        complete_list = dict()

        if valid:
            #Clears database of old transcript data
            old_data = db.session.query(ClassStatus).filter_by(user_id=session['user_id']).delete()
            db.session.commit()

            #Parses all lines that had the pattern needed, and splits the lines up by complete and incomplete courses
            for item in course_list:
                

                line_check = re.findall(course_code_pattern, item)
                grades_check = re.findall("[A-Z][+] [0-9][A-Z][a-z][a-z]|[A-Z]- [0-9][A-Z][a-z][a-z]|[A-Z] [0-9][A-Z][a-z][a-z]|[A-Z][+] [0-9] [A-Z][a-z][a-z]|[A-Z]- [0-9] [A-Z][a-z][a-z]|[A-Z] [0-9] [A-Z][a-z][a-z]", item)


                completed_check = re.findall("[a-z][a-z][a-z]\s[0-9]", item)
                inc_check = re.findall("[1-9][0-9] Credits|[1-9] Credits| [0-9] Class", item)
                exception_check = re.findall("Except [A-Z][A-Z][A-Z] [0-9][0-9][0-9]", item)
                course_exception = 0

                #if exception_check:
                #    print("foo")
                #    print("Exceptions: ",exception_check)
                #    course_exception = 1
                #grades = list()


                #print(line_check)

                #If a class is incomplete, it is put into an incomplete_list
                if inc_check:
                    credits = inc_check[0][0] + inc_check[0][1]
                    credits = credits.replace(" ", "")

                    temp_check = ""

                    if credits == "1":
                        credits = "3"

                    if len(line_check) > 1:
                        for i in range(len(line_check)):
                            #If statements below checks how you need to take certain courses, and handles them accordingly

                            if i == 0:
                                exception_check = 0

                            if "Except" in line_check[i]:
                                temp_check = line_check[i].replace("Except ", "")
                                print(temp_check)
                                exception_check = 1
                                #incomplete_list[line_check[0]] = ["", 0]


                            if "and" in line_check[i]:
                                if len(line_check[i]) < 9:
                                    line_check[i] = line_check[i].replace("and", line_check[0][0:3])
                                else:
                                    line_check[i] = line_check[i].replace("and ", "")
                                incomplete_list[line_check[i]] = ["", int(credits) / len(line_check)]

                                if i == len(line_check)-1:
                                    incomplete_list[line_check[0]] = ["", int(credits) / len(line_check)]

                            if "or" in line_check[i]:
                                if exception_check == 1:
                                    temp_check = temp_check + "-" + line_check[i][3:6]
                                    print(temp_check)
                                    #incomplete_list[line_check[0]] = ["", credits, ]

                                elif len(line_check[i]) < 8:
                                    line_check[0] = line_check[0] + "-" + line_check[i][3:6]
                                else:
                                    line_check[i] = line_check[i].replace("or ", "")
                                    line_check[0] = line_check[0] + "-" + line_check[i]

                                if i == len(line_check)-1:
                                    incomplete_list[line_check[0]] = ["", credits, temp_check]


                    #This is the case where u have a specific course to take
                    else:
                        incomplete_list[line_check[0]] = ["", credits]

                #This section stores completed courses into a list
                elif line_check and grades_check:
                    grade = grades_check[0][0] + grades_check[0][1]
                    grade = grade.replace(" ", "")
                    complete_list[line_check[0]] = [grade, ""]
            

            #combines classes needed with classes completed
            incomplete_list.update(complete_list)


            #breaks up dictionary, leaving us with the course codes in courses, and grade and credits in grades
            courses = list(incomplete_list.keys())
            grades = list(incomplete_list.values())
            
            #Loop makes sure all courses are added to a students list of courses taken/needed
            for i in range(len(courses)):
                
                #checks if grade is empty or not
                if grades[i][0] != "":
                    course = ClassStatus(user_id = session['user_id'], course_code = courses[i], grade = grades[i][0], completed = True)
                else:
                    if len(grades[i]) == 3:
                        course = ClassStatus(user_id = session['user_id'], course_code = courses[i], grade = grades[i][0], credits=grades[i][1], completed = False, course_exceptions=grades[i][2])
                    else:
                        course = ClassStatus(user_id = session['user_id'], course_code = courses[i], grade = grades[i][0], credits=grades[i][1], completed = False)
                db.session.add(course)
                db.session.commit()
           



    os.remove(file_path)

    
    if valid:
        flash('Transcript Uploaded!')
    else:
        flash('Error processing transcript')

    return redirect(url_for('main.course_content'))


@main_blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = CanvasTokenForm()
    message = None

    if form.validate_on_submit():
        token = form.token.data
        headers = {"Authorization": f"Bearer {token}"}
        test_resp = requests.get("https://uncg.instructure.com/api/v1/users/self/profile", headers=headers)

        if test_resp.status_code == 200:
            current_user.canvas_token = token
            current_user.canvas_user_id = test_resp.json().get("id")
            db.session.commit()
            flash("Canvas token updated successfully!", "success")
            return redirect(url_for('main.profile'))
        else:
            flash("Invalid token. Please try again.", "danger")

    # Pre-fill form with existing token if it exists (optional)
    if current_user.canvas_token:
        message = "You already have a Canvas token on file. You may enter a new one if it was regenerated."

    return render_template("profile.html", form=form, message=message, user=current_user)


#Route turns all of a users planned events into json
@main_blueprint.route('/api/event_times')
def get_event_times():
    print(session['user_id'])
    event_items = db.session.query(study_event, study_time).filter_by(user_id=session['user_id']).join(study_time).all()

    event_list = []
    #creates a list of events
    for event, event_time in event_items:
        event_list.append(str({"date": str(event_time.date), "event_id": event.event_id, "event_title": event.event_title, "event_description": event.event_description, "start_time": str(event_time.start_time), "end_time": str(event_time.end_time), "plan_id": event_time.plan_id}))
    #returns a json of the list
    return jsonify(event_list)

#Route turns all of a users events into json
@main_blueprint.route('/api/events')
def get_events():
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

@main_blueprint.route('/admin/delete_user/<int:user_id>', methods=['POST'])  
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = True
    db.session.commit()
    flash('User account soft deleted', 'success')
    return redirect(url_for('main.admin'))

@main_blueprint.route('/admin/restore_user/<int:user_id>', methods=['POST'])
@admin_required
def restore_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_deleted = False
    db.session.commit()
    flash('User account restored', 'success')
    return redirect(url_for('main.admin'))

@main_blueprint.route('/admin/reset_password/<int:user_id>', methods=['POST']) 
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


#Course Catalog Routes

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}


@main_blueprint.route("/upload_catalog", methods=["GET", "POST"])

def upload_catalog():
    
    form = CourseCatalogUploadForm()

    if form.validate_on_submit():
        file = form.catalog_file.data

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Extract and parse courses from the PDF
            extracted_text = extract_text_from_pdf(filepath)
            courses = parse_courses(extracted_text)

            # Save extracted courses to the database
            save_courses_to_db(courses)

            

            
            return redirect(url_for("main.upload_catalog"))

    return render_template("upload_catalog.html", form=form)



def extract_text_from_pdf(filepath):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text

DEPARTMENT_PREFIX_MAP = {
    "ARS": "Academic Recovery Seminar",
    "ACC": "Accounting",
    "IAA": "Advanced Data Analytics",
    "ADS": "African American and African Diaspora Studies",
    "ASL": "American Sign Language",
    "ATY": "Anthropology",
    "APD": "Apparel Product Design",
    "ARB": "Arabic",
    "ARC": "Archaeology",
    "ART": "Art",
    "ARE": "Art Education",
    "ARH": "Art History",
    "AAD": "Arts Administration",
    "AST": "Astronomy",
    "IAB": "Bioinformatics",
    "BIO": "Biology",
    "BUS": "Business Administration",
    "CHE": "Chemistry and Biochemistry",
    "CHI": "Chinese",
    "CCI": "Classical Civilization",
    "CSD": "Communication Sciences and Disorders",
    "CST": "Communication Studies",
    "CTR": "Community and Therapeutic Recreation",
    "CTP": "Comprehensive Transition and Postsecondary Education",
    "IAC": "Computational Analytics",
    "CSC": "Computer Science",
    "CNS": "Consortium",
    "CRS": "Consumer, Apparel, and Retail Studies",
    "CED": "Counseling and Educational Development",
    "IAL": "Cultural Analytics",
    "DCE": "Dance",
    "ECO": "Economics",
    "ELC": "Educational Leadership and Cultural Foundations",
    "ERM": "Educational Research Methodology",
    "ENG": "English",
    "ENS": "Music Ensemble",
    "ENT": "Entrepreneurship",
    "FIN": "Finance",
    "FYE": "First Year Experience",
    "FFL": "Foundations for Learning",
    "FRE": "French",
    "FMS": "Freshman Seminars Program",
    "GEN": "Genetic Counseling",
    "GES": "Geography, Environment, and Sustainability",
    "IAG": "Geospatial Analytics",
    "GER": "German",
    "GRO": "Gerontology",
    "GRK": "Greek",
    "GRC": "Grogan College",
    "IAH": "Health Informatics",
    "HEA": "Public Health",
    "HED": "Higher Education",
    "HHS": "Health and Human Services",
    "HIS": "History",
    "HSS": "Honors Programs",
    "HTM": "Hospitality and Tourism Management",
    "HDF": "Human Development and Family Studies",
    "BLS": "Humanities",
    "IAF": "Informatics and Analytics Foundations",
    "IST": "Information Science",
    "ISM": "Information Systems and Operations Management",
    "IPS": "Integrated Professional Studies",
    "ISL": "Integrated Studies Lab",
    "IAR": "Interior Architecture",
    "ITL": "Interlink",
    "IGS": "International and Global Studies",
    "ISE": "International Student Exchange",
    "ITA": "Italian",
    "JNS": "Japanese Studies",
    "KIN": "Kinesiology",
    "KOR": "Korean",
    "LLC": "Languages, Literatures, and Cultures",
    "LAT": "Latin",
    "LIS": "Library and Information Science",
    "LIB": "University Libraries",
    "MGT": "Management",
    "MKT": "Marketing",
    "MAS": "Master of Applied Arts and Sciences",
    "MBA": "Master of Business Administration",
    "MAT": "Mathematics",
    "MST": "Media Studies",
    "MCP": "Middle College",
    "MSC": "Military Science",
    "MUE": "Music Education",
    "MUP": "Music Performance",
    "MUS": "Music Studies",
    "NAN": "Nanoscience",
    "NUR": "Nursing",
    "NTR": "Nutrition",
    "ONC": "Online NC Interinstitutional",
    "PCS": "Peace and Conflict Studies",
    "PHI": "Philosophy",
    "PHY": "Physics",
    "PSC": "Political Science",
    "PSY": "Psychology",
    "RCO": "Residential College",
    "RCS": "Retailing and Consumer Studies",
    "REL": "Religious Studies",
    "RUS": "Russian",
    "SCM": "Supply Chain Management",
    "SES": "Specialized Education Services",
    "SOC": "Sociology",
    "SPA": "Spanish",
    "SSC": "Social Sciences",
    "STA": "Statistics",
    "STR": "Strong College",
    "SWK": "Social Work",
    "TED": "Teacher Education",
    "THR": "Theatre",
    "UNCX": "UNC Exchange",
    "VPA": "Visual and Performing Arts",
    "WCV": "Western Civilization",
    "WGS": "Women's, Gender, and Sexuality Studies"
}


def parse_courses(text):
    """Extract course details from text including prerequisites and description."""
    lines = text.split("\n")
    course_data = []

    course_code, course_name, description, department, prerequisites, corequisites, credits = None, None, "", "", [], [], ""

    for line in lines:
        # Detect course code patterns like "CSC 101"
        match = re.match(r"([A-Z]{2,4})\s(\d{3})\s(.+?)\s(\d+)(?:-\d+)?$", line)
        if match:
            # Store previous course before resetting
            if course_code:
                course_data.append({
                    "course_code": course_code,
                    "course_name": course_name,
                    "description": description.strip(),
                    "department": department,
                    "credits": credits,
                    "prerequisites": prerequisites,
                    "corequisites": corequisites
                })
                description, prerequisites, corequisites, credits = "", [], [], ""  # Reset for next course

            prefix = match.group(1)
            number = match.group(2)
            course_code = f"{prefix} {number}"
            course_name = match.group(3).strip()
            credits = match.group(4)


            # Look up department using prefix
            department = DEPARTMENT_PREFIX_MAP.get(prefix, "Unknown Department")

        elif "Prerequisite" in line:
            prerequisites = re.findall(r"[A-Z]{2,4}\s\d{3}", line)
        elif "Corequisite" in line:
            corequisites = re.findall(r"[A-Z]{2,4}\s\d{3}", line)
        else:
            description += " " + line.strip()

    # Store the last course in the list
    if course_code:
        course_data.append({
            "course_code": course_code,
            "course_name": course_name,
            "description": description.strip(),
            "department": department,
            "credits": credits,
            "prerequisites": prerequisites,
            "corequisites": corequisites
        })

    return course_data




def save_courses_to_db(courses):
    """Insert parsed course data into the database."""
    for course in courses:
        existing_course = Course.query.filter_by(course_code=course["course_code"]).first()
        
        if not existing_course:
            new_course = Course(
                course_code=course["course_code"],
                course_name=course["course_name"],
                description=course["description"],
                department=course["department"],
                credits=course["credits"],
                prerequisites=course["prerequisites"],
                corequisites=course["corequisites"]
            )
            db.session.add(new_course)

    db.session.commit()


@main_blueprint.route("/courses", methods=["GET"])
def get_courses():
    """Fetch all courses from the database."""
    courses = Course.query.all()
    return jsonify([{
        "course_code": c.course_code,
        "course_name": c.course_name
    } for c in courses])




@main_blueprint.route("/course_list")
@admin_required
def list_courses():
    search_query = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 50

    query = Course.query

    if search_query:
        query = query.filter(
            Course.course_name.ilike(f"%{search_query}%") |
            Course.course_code.ilike(f"%{search_query}%")
        )

    query = query.order_by(Course.course_code.asc())
    total = query.count()
    courses = query.offset((page - 1) * per_page).limit(per_page).all()

    total_pages = ceil(total / per_page)

    return render_template(
        "course_list.html",
        courses=courses,
        page=page,
        total_pages=total_pages,
        search_query=search_query
    )


@main_blueprint.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = EditCourseForm(obj=course)

    if form.validate_on_submit():
        course.course_name = form.course_name.data
        course.course_code = form.course_code.data
        course.department = form.department.data
        course.description = form.description.data
        course.prerequisites = form.prerequisites.data
        course.credits = form.credits.data
        course.corequisites = form.corequisites.data
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('main.list_courses'))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("edit_course_modal.html", form=form, course=course)

    return redirect(url_for('main.list_courses'))


@main_blueprint.route('/course/<int:course_id>/delete', methods=['POST'])
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('main.list_courses'))

@main_blueprint.route('/course/add', methods=['GET', 'POST'])
@admin_required
def add_course():
    form = EditCourseForm()

    if form.validate_on_submit():
        new_course = Course(
            course_name=form.course_name.data,
            course_code=form.course_code.data,
            department=form.department.data,
            description=form.description.data,
            credits=form.credits.data,
            prerequisites=form.prerequisites.data,
            corequisites=form.corequisites.data
        )
        db.session.add(new_course)
        db.session.commit()
        flash('New course added!', 'success')
        return redirect(url_for('main.list_courses'))

    if request.headers.get("X-Requested-With") =="XMLHttpRequest":
        return render_template("add_course_modal.html", form=form)

    return redirect('main.list_courses')

#canvas routes
@main_blueprint.route('/connect-canvas', methods=['GET', 'POST'])
@login_required
def connect_canvas():
    form = CanvasTokenForm()
    if form.validate_on_submit():
        token = form.token.data
        headers = {"Authorization": f"Bearer {token}"}
        test_resp = requests.get("https://uncg.instructure.com/api/v1/users/self/profile", headers=headers)

        if test_resp.status_code == 200:

            #encrptyion
            #fernet = Fernet(current_app.config["FERNET_KEY"])
            #encrypted_token = fernet.encrypt(token.encode()).decode()

            current_user.canvas_token = token
            current_user.canvas_user_id = test_resp.json().get("id")
            db.session.commit()
            flash("Canvas account connected successfully!", "success")
            return redirect(url_for('main.study_planner'))
        else:
            flash("Invalid token. Please double-check and try again.", "danger")

    return render_template('connect_canvas.html', form=form)

@main_blueprint.route('/regenerate-canvas-token', methods=['GET', 'POST'])
@login_required
def regenerate_canvas_token():
    form = CanvasTokenForm()
    if form.validate_on_submit():
        token = form.token.data
        headers = {"Authorization": f"Bearer {token}"}
        test_resp = requests.get("https://uncg.instructure.com/api/v1/users/self/profile", headers=headers)

        if test_resp.status_code == 200:
            current_user.canvas_token = token
            db.session.commit()
            flash("Canvas token updated successfully!", "success")
            return redirect(url_for('main.canvas_assignments'))
        else:
            flash("The new token is invalid. Please try again.", "danger")

    return render_template('regenerate_canvas_token.html', form=form)

#Refreshes a students assignment list
@main_blueprint.route('/canvas/assignments/refresh')
@login_required
def canvas_assignments_refresh():

    token = current_user.canvas_token

    #exits early if user hasnt entered their canvas api token
    if not token:
       
        flash("You need to connect your Canvas account first.", "warning")
        return jsonify([])
    
    
    db.session.query(assignments).filter_by(user_id=session['user_id']).delete()
    db.session.commit()

    #Sets up api call
    headers = {"Authorization": f"Bearer {token}"}
    params = {"enrollment_state": "active"}  # Only include current enrollments
    courses_resp = requests.get("https://uncg.instructure.com/api/v1/courses", headers=headers, params=params)

    if courses_resp.status_code != 200:
        flash("There was an issue accessing your Canvas courses.", "danger")
        return redirect(url_for('main.connect_canvas'))

    courses = courses_resp.json()


    # Filter and store recent courses
    recent_courses = []
    for course in courses:
        start_at = course.get('start_at')
        if start_at:
            try:
                start_date = datetime.fromisoformat(start_at.replace('Z', ''))
                if start_date.year >= 2025:
                    recent_courses.append(course)
            except ValueError:
                recent_courses.append(course)
        else:
            recent_courses.append(course)

    all_assignments = []
    # Filter and store upcoming assignments
    for course in recent_courses:
        cid = course.get("id")
        assignments_resp = requests.get(
            f"https://uncg.instructure.com/api/v1/courses/{cid}/assignments",
            headers=headers,
            params= {
                "bucket": "future",
                "order_by": "due_at"
            }
        )
        if assignments_resp.ok:
            assignments_item = assignments_resp.json()
            for assignment in assignments_item:
                assignment['course_name'] = course.get('name')
            all_assignments.extend(assignments_item)

    now = datetime.now(timezone.utc)
    upcoming = []
    past_due = []

    #
    for assignment in all_assignments:
        due_str = assignment.get('due_at')
        
        
        if due_str:
            try:
                due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))
                if due_date >= now:
                    upcoming.append(assignment)
                else:
                    past_due.append(assignment)
            except ValueError:
                upcoming.append(assignment)  # fallback if date parsing fails

    # Sort each group
    upcoming.sort(key=lambda a: a.get('due_at') or '')
    past_due.sort(key=lambda a: a.get('due_at') or '')

    #return render_template(
    #    'canvas_assignments.html',
    #    upcoming_assignments=upcoming,
    #    past_due_assignments=past_due,
    #    courses=recent_courses
    #)
    assignment_list = []

    #adds assignments to db
    for assignmentss in upcoming:
        due_date = datetime.fromisoformat(assignmentss["due_at"]) - timedelta(hours=4)
        assignment = assignments(user_id = session['user_id'], due_date = str(due_date), name = assignmentss["name"], course_code = assignmentss["course_name"])
        db.session.add(assignment)
        db.session.commit()

    #adds assignments to a list to be returned as a json
    for assignmentss in upcoming:
        due_date = datetime.fromisoformat(assignmentss["due_at"]) - timedelta(hours=4)
        assignment_list.append(str({"name": assignmentss["name"], "due_at": str(due_date), "course_name": assignmentss["course_name"]}))
        #return jsonify(event_list)
    

    return jsonify(assignment_list)


#route pulls a users assignments from db
@main_blueprint.route('/canvas/assignments')
@login_required
def canvas_assignments():
    
    all_assignments = db.session.query(assignments).filter_by(user_id=session['user_id']).all()

    assignment_list = []

    for assignment in all_assignments:
        assignment_list.append(str({"name": assignment.name, "due_at": assignment.due_date, "course_name": assignment.course_code}))

    print(assignment_list)
    return jsonify(assignment_list)


@main_blueprint.route("/resources/chat/new", methods=["POST"])
@login_required
def new_resource_chat():
    new_chat = ResourceChat(user_id=current_user.id, title="New Chat")
    db.session.add(new_chat)
    db.session.commit()
    return redirect(url_for('main.resources', chat_id=new_chat.id))


@main_blueprint.route("/resources/chat/<int:chat_id>/delete", methods=["POST"])
@login_required
def delete_resource_chat(chat_id):
    chat = ResourceChat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    db.session.delete(chat)
    db.session.commit()
    flash("Chat deleted.")
    return redirect(url_for("main.resources"))

@main_blueprint.route('/favorite_course', methods=['POST'])
@login_required
def favorite_course():
    course_id = request.form.get('course_id')
    semester = request.form.get('semester')

    existing = FavoriteCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if not existing:
        fav = FavoriteCourse(user_id=current_user.id, course_id=course_id, semester=semester)
        db.session.add(fav)
        db.session.commit()
        flash('Course added to favorites!', 'success')
    else:
        flash('Course already favorited.', 'info')

    return redirect(request.referrer or url_for('main.profile'))

@main_blueprint.route('/unfavorite_course/<int:course_id>', methods=['POST'])
@login_required
def unfavorite_course(course_id):
    fav = FavoriteCourse.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Course removed from favorites.", "info")
    else:
        flash("Course not found in your favorites.", "warning")
    return redirect(request.referrer or url_for('main.profile'))


@main_blueprint.route('/browse_courses', methods=['GET'])
@login_required
def browse_courses():
    from .models import Course

    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 100

    if search_query:
        search_pattern = f"%{search_query}%"
        filters = or_(
            Course.course_name.ilike(search_pattern),
            Course.course_code.ilike(search_pattern),
            Course.department.ilike(search_pattern)
        )
        
        pagination = Course.query.filter(filters).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = Course.query.paginate(page=page, per_page=per_page, error_out=False)
    
    courses = pagination.items

    return render_template("browse_courses.html", courses=courses, pagination=pagination)




@main_blueprint.route("/generated-study-plan", methods=["GET", "POST"])
@login_required
def generated_study_plan():
    from google.generativeai import GenerativeModel
    from sqlalchemy import cast, Date
    from eduplan.models import assignments, StudyPreference, SavedStudyPlan

    regenerate = request.args.get("regenerate") == "true"

    # Check if a saved plan exists
    saved = SavedStudyPlan.query.filter_by(user_id=current_user.id).first()
    if saved and not regenerate:
        return render_template("generated_study_plan.html", study_plan=saved.content, last_updated=saved.generated_on)

    # Else: generate a new plan
    now = datetime.utcnow().date()
    assignments_list = assignments.query.filter(
        assignments.user_id == current_user.id,
        cast(assignments.due_date, Date) >= now
    ).all()

    if not assignments_list:
        return render_template("generated_study_plan.html", study_plan="No upcoming assignments found.")

    prefs = StudyPreference.query.filter_by(user_id=current_user.id).first()
    hw_weeks = prefs.homework_weeks if prefs else 1
    proj_weeks = prefs.project_weeks if prefs else 3
    exam_weeks = prefs.exam_weeks if prefs else 2
    quiz_weeks = prefs.quiz_weeks if prefs else 0.43
    no_days = prefs.no_study_days or []
    blocked_start = prefs.no_study_time_start.strftime('%I:%M %p') if prefs.no_study_time_start else None
    blocked_end = prefs.no_study_time_end.strftime('%I:%M %p') if prefs.no_study_time_end else None
    preferred_hours = prefs.preferred_study_hours if prefs else 2
    time_block = prefs.study_time_block if prefs else "afternoon"

    category_keywords = {
        "exam": ["exam", "final", "midterm", "test"],
        "project": ["project", "presentation", "report"],
        "quiz": ["quiz", "pop quiz"],
        "assignment": ["assignment", "homework", "problem set"]
    }

    def categorize(name, description=""):
        name = name.lower()
        description = description.lower()
        for cat, words in category_keywords.items():
            if any(w in name or w in description for w in words):
                return cat
        return "assignment"

    formatted = []
    for a in assignments_list:
        category = categorize(a.name, getattr(a, "description", ""))
        due = datetime.fromisoformat(a.due_date).strftime('%B %d, %Y at %I:%M %p')
        formatted.append(f"- {a.name} ({category}) for {a.course_code}, due on {due}")

    prompt = f"""
You are helping a student create a 30-day study plan.

Preferences:
- Homework: {hw_weeks} weeks
- Projects: {proj_weeks} weeks
- Exams: {exam_weeks} weeks
- Quizzes: {quiz_weeks} weeks
- Avoid days: {', '.join(no_days) if no_days else "none"}
- Avoid time: {blocked_start}–{blocked_end if blocked_end else ''}
- Preferred study time: {time_block}
- Max {preferred_hours} hour(s) per day

Assignments:
{chr(10).join(formatted)}

Generate a daily plan with tasks for each day.
"""

    # Call Gemini
    genai.configure(api_key=gemini_key)
    model = GenerativeModel("gemini-1.5-flash")
    try:
        response = model.generate_content(prompt)
        study_plan = response.text

        if saved:
            saved.content = study_plan
            saved.generated_on = datetime.utcnow()
        else:
            saved = SavedStudyPlan(user_id=current_user.id, content=study_plan)
            db.session.add(saved)

        db.session.commit()
    except Exception as e:
        study_plan = f"Error generating plan: {e}"

    return render_template(
    "generated_study_plan.html",
    study_plan=study_plan,
    last_updated=saved.generated_on if saved else None
)



@main_blueprint.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    prefs = StudyPreference.query.filter_by(user_id=current_user.id).first()
    if not prefs:
        prefs = StudyPreference(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()

    form = PreferencesForm(obj=prefs)

    if form.validate_on_submit():
        prefs.homework_weeks = form.homework_weeks.data
        prefs.project_weeks = form.project_weeks.data
        prefs.exam_weeks = form.exam_weeks.data
        prefs.quiz_weeks = form.quiz_weeks.data

        prefs.no_study_days = form.no_study_days.data
        prefs.no_study_time_start = form.no_study_time_start.data
        prefs.no_study_time_end = form.no_study_time_end.data
        prefs.preferred_study_hours = form.preferred_study_hours.data

        db.session.commit()
        flash("Study preferences updated!", "success")

    return render_template("preferences.html", form=form)


category_keywords = {
    "exam": ["exam", "final", "midterm", "test"],
    "project": ["project", "presentation", "report"],
    "quiz": ["quiz", "pop quiz"],
    "assignment": ["assignment", "homework", "problem set"]
}

def categorize_assignment(name, description=""):
    name = name.lower()
    description = description.lower()
    for category, keywords in category_keywords.items():
        if any(kw in name or kw in description for kw in keywords):
            return category
    return "assignment"
