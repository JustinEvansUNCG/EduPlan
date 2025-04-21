from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, PasswordField, IntegerField, HiddenField, TimeField, DateField, SelectField, FileField, SelectMultipleField
from wtforms.validators import DataRequired, Length, Email, ValidationError, EqualTo, InputRequired

from eduplan import db
from eduplan.models import study_event
from flask import session

todos = ["Foo"]

#basic flask form
class TodoForm(FlaskForm):
    todo = StringField("Todo")
    submit = SubmitField("Add Todo")


#Sign up form - asks for nam, email, password, must have a valid uncg email

class EventDeleteForm(FlaskForm):
    plan_id = HiddenField('plan_id')
    submit = SubmitField("Delete Event")




class EventAddForm(FlaskForm):
    start_time = TimeField("Start Time")
    end_time = TimeField("End Time")
    date = DateField("date")
    #validate chois is false below as we are adding the choices dynamically
    existing_events = SelectField('Events Available', choices=[], validate_choice=False)
    submit = SubmitField("Add Event")

    event_title = StringField('Event title')
    event_description = StringField('Event description')
    event_creation_type = HiddenField('creation_type')

class EventModifyForm(FlaskForm):
    plan_id = HiddenField("plan_id")
    start_time = TimeField("Start Time")
    end_time = TimeField("End Time")
    date = DateField("date")
    event_title = StringField('Event title')
    event_description = StringField('Event description')

    submit = SubmitField("Modify Event")


    #event_creation_type = HiddenField('creation_type')

    
class EditCourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    description = StringField('Description')
    department = StringField('Department', validators=[DataRequired()])
    course_code = StringField('Course Code', validators=[DataRequired()])
    credits = StringField('Credits', validators=[DataRequired()])
    prerequisites = StringField('Prerequisites')
    corequisites = StringField('Corequisites')
    submit = SubmitField('Update Course')


class RegisterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign up')

    def validate_email(self, email):
        if not email.data.endswith('@uncg.edu'):
            raise ValidationError('Must have a valid uncg email')

#Makes sure email and password are in the database
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class LogoutForm(FlaskForm):
    submit = SubmitField('Logout')


class TranscriptForm(FlaskForm):
    transcript = FileField('Transcript')
    submit = SubmitField('Upload Current Transcript')

class CourseCatalogUploadForm(FlaskForm):
    catalog_file = FileField("Upload Course Catalog (PDF)")
    submit = SubmitField("Upload")

class CanvasTokenForm(FlaskForm):
    token = StringField('Canvas Access Token', validators=[DataRequired()])
    submit = SubmitField('Save Token')



class PreferencesForm(FlaskForm):
    homework_weeks = SelectField("Homework:", choices=[
        (0.29, "2–3 days"),
        (0.71, "5 days–1 week"),
        (1, "1 week"),
        (2, "2 weeks")
    ], coerce=float)

    project_weeks = SelectField("Projects:", choices=[
        (1, "1 week"),
        (2, "2 weeks"),
        (3, "3 weeks"),
        (4, "4 weeks")
    ], coerce=float)

    exam_weeks = SelectField("Exams:", choices=[
        (1, "1 week"),
        (2, "2 weeks"),
        (3, "3 weeks"),
        (4, "4 weeks")
    ], coerce=float)

    quiz_weeks = SelectField("Quizzes:", choices=[
        (0.29, "2–3 days"),
        (0.5, "3–4 days"),
        (0.71, "5 days–1 week")
    ], coerce=float)

    no_study_days = SelectMultipleField("Days You Don’t Want to Study", choices=[
        ("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"), ("Friday", "Friday"),
        ("Saturday", "Saturday"), ("Sunday", "Sunday")
    ])

    no_study_time_start = TimeField("Block Study Start Time")
    no_study_time_end = TimeField("Block Study End Time")

    study_time_block = SelectField("When do you prefer to study?", choices=[
    ("morning", "Morning (6 AM – 12 PM)"),
    ("afternoon", "Afternoon (12 PM – 5 PM)"),
    ("evening", "Evening (5 PM – 9 PM)"),
    ("night", "Night (9 PM – Midnight)")
])


    preferred_study_hours = IntegerField("Preferred Hours of Study per Day", validators=[InputRequired()])
    submit = SubmitField("Save Preferences")