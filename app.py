from flask import Flask

app = Flask(__name__)

import secrets

# Print out the test secret so we can verify it works in google cloud
@app.route("/")
def hello_world():
    return "Hello, world!"

