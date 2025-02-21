from flask import Flask


app = Flask(__name__)

# This is needed to use forms, but will be kept in a more secret place at a later date
app.secret_key="anystringhere"




import eduplan.routes



