from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session, current_app
from eduplan import bcrypt

from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm, EventDeleteForm, EventAddForm, EventModifyForm, LogoutForm, TranscriptForm, CourseCatalogUploadForm, EditCourseForm, CanvasTokenForm

from eduplan import db
from eduplan.models import study_time, study_event, User, CourseContentAssistance, ClassStatus
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
from datetime import datetime, timezone




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


from flask_login import login_user

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
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user)  # Use Flask-Login's login_user()
            login_user(user)

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
    canvas_courses = []

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        selected_course = request.form.get("selected_course", "").strip()

        if not question:
            question = "Explain a general study tip."

        course_info = f" This question is related to the course: {selected_course}." if selected_course else ""
        study_prompt = (
            f"Ensure this is a question related to: {course_info} "
            f"If it isn't, ask the user to rephrase. "
            f"If it is, answer the question and don’t say anything about anything before this text {question}"
        )
        print(study_prompt)
        blocked_keywords = ["game", "movie", "politics", "news", "celebrity"]

        if any(keyword in question.lower() for keyword in blocked_keywords):
            ai_response = "This question doesn't seem related to studies. Please ask about a study-related topic."
        else:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(study_prompt)
            if response and response.text:
                ai_response = markdown.markdown(response.text.strip())
            else:
                ai_response = "Error processing AI response."
    try:
        headers = {"Authorization": f"Bearer {canvas_api_token}"}
        res = requests.get(f"{canvas_api_url}/api/v1/courses", headers=headers)
        
        
        if res.status_code == 200:
            #"enrollments": course["enrollements"][0]["enrollment_state"]
            canvas_courses = [
                {"id": course["id"], "name": course["name"], "enrollments": course["enrollments"][0]["enrollment_state"]}
                for course in res.json()
                if not course.get("access_restricted_by_date")
            ]
            
    except Exception as e:
        print(f"Canvas API error: {e}")

    return render_template("Resources.html", ai_response=ai_response, canvas_courses=canvas_courses)


@main_blueprint.route("/course_content", methods=["GET", "POST"])
@login_required
def course_content():
    ai_response = None

    transcript_form = TranscriptForm()

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        
        if not question:
            question = "Explain a general study tip."

        study_prompt = f"Ensure this is a study-related question. If it isn't, ask the user to rephrase, if it is, answer the question and dont say anything about text before this to the user, If the text that follows looks like transcript make sure you consider tailoring your responses based on it {question} "
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
        
        if response and response.text:
                clean_text = response.text.strip()
                ai_response = markdown.markdown(clean_text)
                entry = CourseContentAssistance(
                    user_id=current_user.id,
                    question=question,
                    ai_response=clean_text
                )
                print(entry.question)
                print(entry.question)
                db.session.add(entry)
                db.session.commit()
        else:
                ai_response = "Error processing AI response."

    return render_template("course_content.html", ai_response=ai_response,  transcript_form=transcript_form)



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
    course_list = list()


    old_data = db.session.query(ClassStatus).filter_by(user_id=session['user_id']).delete()
    #db.session.delete(old_data)
    db.session.commit()

    


    for i in range(page_count):

        page = reader.pages[i]
        text = page.extract_text()
        temp_list = text.split("\n")
        print(text)

        course_code_pattern = "[A-Z][A-Z][A-Z] [0-9][0-9][0-9]:[0-9][0-9][0-9]|[A-Z][A-Z][A-Z] [0-9][0-9][0-9]L|[A-Z][A-Z][A-Z] [0-9][0-9][0-9]|and [0-9][0-9][0-9]L|or [0-9][0-9][0-9]L|and [0-9][0-9][0-9]|or [0-9][0-9][0-9]"

        

        for item in temp_list:
            line_check = re.findall(course_code_pattern, item)

            if line_check:

                course_list.append(item)

    print(*course_list, sep="\n")


    incomplete_list = dict()
    complete_list = dict()


    for item in course_list:

        line_check = re.findall(course_code_pattern, item)
        grades_check = re.findall("[A-Z][+] [0-9][A-Z][a-z][a-z]|[A-Z]- [0-9][A-Z][a-z][a-z]|[A-Z] [0-9][A-Z][a-z][a-z]|[A-Z][+] [0-9] [A-Z][a-z][a-z]|[A-Z]- [0-9] [A-Z][a-z][a-z]|[A-Z] [0-9] [A-Z][a-z][a-z]", item)

        #lab_check = re.findall("[A-Z][A-Z][A-Z]\s[0-9][0-9][0-9][L]\s", item)

        completed_check = re.findall("[a-z][a-z][a-z]\s[0-9]", item)
        inc_check = re.findall("[1-9][0-9] Credits|[1-9] Credits", item)
        #grades = list()



    #some issues remain with cases on the transcript that say "or"
        if inc_check:
            if len(line_check) > 1:
                for i in range(len(line_check)):
                    if "and" in line_check[i]:
                        line_check[i] = line_check[i].replace("and", line_check[0][0:3])
                        incomplete_list[line_check[i]] = ""
                        if i == len(line_check)-1:
                            incomplete_list[line_check[0]] = ""

                    if "or" in line_check[i]:
                        line_check[0] = line_check[0] + "-" + line_check[i][3:6]
                        if i == len(line_check)-1:
                            incomplete_list[line_check[0]] = ""


            else:
                incomplete_list[line_check[0]] = ""

            
        elif line_check and grades_check:
            grade = grades_check[0][0] + grades_check[0][1]
            grade = grade.replace(" ", "")
            complete_list[line_check[0]] = grade
           

    incomplete_list.update(complete_list)

    courses = list(incomplete_list.keys())
    grades = list(incomplete_list.values())
    
    for i in range(len(courses)):
        
        if grades[i] is not "":
            course = ClassStatus(user_id = session['user_id'], course_code = courses[i], grade = grades[i], completed = True)
        else:
            course = ClassStatus(user_id = session['user_id'], course_code = courses[i], grade = grades[i], completed = False)
        db.session.add(course)
        db.session.commit()
        #print(courses[i], grades[i])



    os.remove(file_path)


    return redirect(url_for('main.home'))


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

    if search_query:
        courses = Course.query.filter(
            Course.course_name.ilike(f"%{search_query}%") |
            Course.course_code.ilike(f"%{search_query}%")
        ).order_by(Course.course_code.asc()).all()
    else:
        courses = Course.query.order_by(Course.course_code.asc()).all()

    return render_template("course_list.html", courses=courses)


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

    return render_template('edit_course.html', form=form, course=course)


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

    return render_template('add_course.html', form=form)

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
            current_user.canvas_token = token
            current_user.canvas_user_id = test_resp.json().get("id")
            db.session.commit()
            flash("Canvas account connected successfully!", "success")
            return redirect(url_for('main.canvas_assignments'))
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

@main_blueprint.route('/canvas/assignments')
@login_required
def canvas_assignments():
    token = current_user.canvas_token
    if not token:
        flash("You need to connect your Canvas account first.", "warning")
        return redirect(url_for('main.connect_canvas'))

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
    for course in recent_courses:
        cid = course.get("id")
        assignments_resp = requests.get(
            f"https://uncg.instructure.com/api/v1/courses/{cid}/assignments",
            headers=headers
        )
        if assignments_resp.ok:
            assignments = assignments_resp.json()
            for assignment in assignments:
                assignment['course_name'] = course.get('name')
            all_assignments.extend(assignments)

    now = datetime.now(timezone.utc)
    upcoming = []
    past_due = []

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
        else:
            upcoming.append(assignment)

    # Sort each group
    upcoming.sort(key=lambda a: a.get('due_at') or '')
    past_due.sort(key=lambda a: a.get('due_at') or '')

    return render_template(
        'canvas_assignments.html',
        upcoming_assignments=upcoming,
        past_due_assignments=past_due,
        courses=recent_courses
    )
