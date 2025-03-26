from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from eduplan import bcrypt
from eduplan.forms import TodoForm, todos, RegisterForm, LoginForm, EventDeleteForm, EventAddForm, EventModifyForm, LogoutForm, CourseCatalogUploadForm, EditCourseForm
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
from werkzeug.utils import secure_filename
import os
import fitz  
import csv
from flask import send_file



genai.configure(api_key="AIzaSyArG1yXW3d1odahUokxzXgOHejGWrDYxLI")

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



@main_blueprint.route("/index", methods=["GET", "POST"])
def index():

    if "todo" in request.form:
        todos.append(request.form["todo"])

    return render_template("index.html", todos=todos, template_form=TodoForm())


@login_required
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

            # Use next parameter for redirection
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.study_planner'))

        else:
            flash('Invalid email or password', 'danger')  # Incorrect login
            return render_template("login.html", form=form)
    return render_template("login.html", form=form)




@main_blueprint.route("/resources", methods=["GET", "POST"])
@login_required
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
@login_required
def course_content():
    ai_response = None
    if request.method == "POST":
        question = request.form.get("question", "Explain a general study tip.")

        model = genai.GenerativeModel("gemini-2.0-flash")
        response_text = model.generate_content(question).text

        # Convert AI response from Markdown to HTML (preserves structure)
        formatted_response = markdown.markdown(response_text)

        ai_response = formatted_response.strip()  

    return render_template("course_content.html", ai_response=ai_response)


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


@main_blueprint.route('/')
def home():
    return render_template('home.html')



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
    """Handles file upload from the web form and saves extracted data to a CSV."""
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

            #  Save extracted courses to CSV
            csv_path = save_courses_to_csv(courses)

            flash(f"Uploaded {len(courses)} courses successfully! CSV saved at {csv_path}", "success")
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

    course_code, course_name, description, department, prerequisites, corequisites = None, None, "", "", [], []

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
                    "prerequisites": prerequisites,
                    "corequisites": corequisites
                })
                description, prerequisites, corequisites = "", [], []  # Reset for next course

            prefix = match.group(1)
            number = match.group(2)
            course_code = f"{prefix} {number}"
            course_name = match.group(3).strip()

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



def save_courses_to_csv(courses, filename="extracted_courses.csv"):
    """Save extracted course data to a CSV file."""
    csv_path = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Course Code", "Course Name", "Description", "Department", "Prerequisites", "Corequisites"])
        
        for course in courses:
            writer.writerow([
                course["course_code"],
                course["course_name"],
                course["description"],
                course["department"],
                ", ".join(course["prerequisites"]),
                ", ".join(course["corequisites"])
            ])

    return csv_path  # Return the path of the saved CSV file



@main_blueprint.route("/download_csv")
def download_csv():
    """Route to download the generated CSV file."""
    csv_path = os.path.join(UPLOAD_FOLDER, "extracted_courses.csv")
    return send_file(csv_path, as_attachment=True, download_name="courses.csv")


#@main_blueprint.route("/courses")
#def list_courses():
#    from eduplan.models import Course
#    courses = Course.query.order_by(Course.course_code).all()
#    return render_template("course_list.html", courses=courses)


@main_blueprint.route("/course_list")
def list_courses():
    search_query = request.args.get("search", "").strip()

    if search_query:
        courses = Course.query.filter(
            Course.course_name.ilike(f"%{search_query}%") |
            Course.course_code.ilike(f"%{search_query}%")
        ).all()
    else:
        courses = Course.query.all()

    return render_template("course_list.html", courses=courses)


@main_blueprint.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = EditCourseForm(obj=course)

    if form.validate_on_submit():
        course.course_name = form.course_name.data
        course.course_code = form.course_code.data
        course.department = form.department.data
        course.description = form.description.data
        course.prerequisites = form.prerequisites.data
        course.corequisites = form.corequisites.data
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('main.course_list'))

    return render_template('edit_course.html', form=form, course=course)


@main_blueprint.route('/course/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('course_list'))

@main_blueprint.route('/course/add', methods=['GET', 'POST'])
def add_course():
    form = EditCourseForm()

    if form.validate_on_submit():
        new_course = Course(
            course_name=form.course_name.data,
            course_code=form.course_code.data,
            department=form.department.data,
            description=form.description.data,
            prerequisites=form.prerequisites.data,
            corequisites=form.corequisites.data
        )
        db.session.add(new_course)
        db.session.commit()
        flash('New course added!', 'success')
        return redirect(url_for('main.course_list'))

    return render_template('add_course.html', form=form)