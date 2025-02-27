from eduplan import app
import psycopg2
import json
import os

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('student', 'admin', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

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
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Course {self.course_code} - {self.course_name}>"

class CourseRecommendation(db.Model):
    __tablename__ = 'course_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
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
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    resource_type = db.Column(db.Enum('book', 'video', 'website', 'pdf', name='resource_types'), nullable=False)
    resource_title = db.Column(db.String(255), nullable=False)
    resource_link = db.Column(db.Text, nullable=False)
    recommended_by_ai = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CourseResource {self.resource_title}>"

class StudyPreference(db.Model):
    __tablename__ = 'study_preferences'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    no_study_days = db.Column(db.ARRAY(db.String))  # List of days user doesn't want to study
    no_study_time_start = db.Column(db.Time)
    no_study_time_end = db.Column(db.Time)
    preferred_study_hours = db.Column(db.Integer, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StudyPreference User:{self.user_id}>"
    
class StudyPlan(db.Model):
    __tablename__ = 'study_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    study_date = db.Column(db.Date, nullable=False)
    study_time = db.Column(db.Time, nullable=False)
    study_notes = db.Column(db.Text)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StudyPlan User:{self.user_id} Course:{self.course_id}>"
    
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
#
#
#
#
