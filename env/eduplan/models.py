from eduplan import db  

import re
from flask_login import UserMixin
from datetime import datetime
from .extensions import bcrypt


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'admin', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    canvas_token = db.Column(db.String(255))
    canvas_user_id = db.Column(db.String(100))

    def __repr__(self):
        return f"<User {self.email}>"
    
    

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(80), nullable=False)
    prerequisites = db.Column(db.ARRAY(db.String), nullable=True)  
    corequisites = db.Column(db.ARRAY(db.String), nullable=True) 
    credits = db.Column(db.String(20), nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Course {self.course_code} - {self.course_name}>"
    

class ClassStatus(db.Model):
    tablename = 'users_classlist'


    #course_id = db.Column(db.Integer, autoincrement=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_code = db.Column(db.String(70), nullable=False)
    grade = db.Column(db.String(3), nullable=True)
    completed = db.Column(db.Boolean)
    credits = db.Column(db.Integer, nullable=True)
    course_exceptions = db.Column(db.String(40), nullable=True)



    table_args = (
    db.PrimaryKeyConstraint(user_id, course_code),


    )
    
    

class CourseRecommendation(db.Model):
    __tablename__ = 'course_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.String(20), db.ForeignKey('courses.course_code'), nullable=False)
    ai_reasoning = db.Column(db.Text) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
       return f"<CourseRecommendation User:{self.user_id} Course:{self.course_id}>"

class CourseContentAssistance(db.Model):
    __tablename__ = 'course_content_assistance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CourseContentAssistance User:{self.user_id} Question:{self.question[:50]}>"

class CourseResource(db.Model):
    __tablename__ = 'course_resources'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('resource_chats.id'), nullable=False)
    course_id = db.Column(db.String(20), db.ForeignKey('courses.course_code'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CourseResourceAssistance User:{self.user_id} Question:{self.question[:50]}>"

class StudyPreference(db.Model):
    __tablename__ = 'study_preferences'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    # Weekly study preferences by assignment type
    homework_weeks = db.Column(db.Float, default=1.0)
    project_weeks = db.Column(db.Float, default=3.0)
    exam_weeks = db.Column(db.Float, default=2.0)
    quiz_weeks = db.Column(db.Float, default=0.43)  # ~3 days

    # Personal schedule preferences
    no_study_days = db.Column(db.ARRAY(db.String))  # e.g., ["Saturday", "Sunday"]
    no_study_time_start = db.Column(db.Time)        # e.g., time(18, 0)
    no_study_time_end = db.Column(db.Time)          # e.g., time(21, 0)
    preferred_study_hours = db.Column(db.Integer, nullable=False, default=2)
    study_time_block = db.Column(db.String, default="afternoon")  # morning, afternoon, evening, night

    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref="study_preferences", uselist=False)



    def __repr__(self):
        return f"<StudyPreference User:{self.user_id}>"
    
#class StudyPlan(db.Model):
#    __tablename__ = 'study_plans'

#    id = db.Column(db.Integer, primary_key=True)
#    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
#    study_date = db.Column(db.Date, nullable=False)
#    study_time = db.Column(db.Time, nullable=False)
#    study_notes = db.Column(db.Text)
#    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

#    def __repr__(self):
#        return f"<StudyPlan User:{self.user_id} Course:{self.course_id}>"


class study_event (db.Model):

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, autoincrement=True, unique=True, nullable=False)
    event_title = db.Column(db.String(100))
    event_description = db.Column(db.String(200))

    __table_args__ = (
        db.PrimaryKeyConstraint(user_id, event_id),


    )

    def __repr__(self):
        return f"{self.event_id}"
    


class study_time (db.Model):
    plan_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('study_event.event_id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    



    def __repr__(self):
        return f"{self.date}"
    
class assignments (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.String(100), nullable = False)
    name = db.Column(db.String(150), nullable = False)
    course_code = db.Column(db.String(150), nullable = False)

    def __repr__(self):
        return f"{self.name}"


class AdminActivity(db.Model):
    __tablename__ = 'admin_activity'

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_taken = db.Column(db.Text, nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    target_course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AdminActivity Admin:{self.admin_id} Action:{self.action_taken}>"


class Transcript(db.Model):
    __tablename__ = 'transcripts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ResourceChat(db.Model):
    __tablename__ = 'resource_chats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False, default="Untitled Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    messages = db.relationship('CourseResource', backref='chat', cascade='all, delete-orphan')



class FavoriteCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    semester = db.Column(db.String(20), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='favorite_courses')
    course = db.relationship('Course')

class SavedStudyPlan(db.Model):
    __tablename__ = 'saved_study_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    generated_on = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="study_plan", uselist=False)



