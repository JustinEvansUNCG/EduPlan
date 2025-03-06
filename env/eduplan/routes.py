from flask import Blueprint, render_template, request, jsonify
from eduplan.forms import TodoForm, todos

from eduplan import db 
from eduplan.models import study_time, study_event

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
    return render_template("signup.html")

@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")

@main_blueprint.route("/resources", methods=["GET", "POST"])
def resources():
    return render_template("resources.html")

@main_blueprint.route("/course_content", methods=["GET", "POST"])
def course_content():
    return render_template("course_content.html")

@main_blueprint.route("/admin", methods=["GET", "POST"])
def admin():
    return render_template("admin.html")

