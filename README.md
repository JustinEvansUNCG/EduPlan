# EduPlan
CSC 490 Capstone Project

How to run:
upon opening the application folder go to ./EDUPLAN/EduPlan/env in terminal
then type Scripts\activate to enter the virtual environment. 

Now, type the following to initialize the db on your end:

set FLASK_APP=run.py
flask run
flask db init
flask db migrate -m "Reinitialize migrations"
flask db upgrade

Lastly, type: python run.py



Calendar and Modal template links
These templates were used at the start, with many changes applied from there. Please check these templates out if you want to learn more how the calendar was made
Modal template:
https://www.w3schools.com/howto/howto_css_modals.asp

Calendar template:
https://www.geeksforgeeks.org/how-to-design-a-simple-calendar-using-javascript/

Bootstrap template was used for alerts:
Bootstrap template: https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css

