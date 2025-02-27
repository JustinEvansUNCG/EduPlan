import os
import json
import urllib
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'db_config.json')

with open(CONFIG_PATH, "r") as config_file:
    db_config = json.load(config_file)

encoded_password = urllib.parse.quote_plus(db_config['password'])

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{db_config['user']}:{encoded_password}@"
        f"{db_config['host']}/{db_config['database']}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "some_secret_key")
