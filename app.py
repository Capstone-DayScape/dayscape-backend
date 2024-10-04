from flask import Flask

app = Flask(__name__)

import secrets

# Leave this route for the healthchecks on Cloud Run. The API will be
# under /api/
@app.route("/")
def hello_world():
    return "Hello, world!"

