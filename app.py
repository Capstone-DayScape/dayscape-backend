import google_secrets

import json
from six.moves.urllib.request import urlopen
from functools import wraps

from flask import Flask, request, jsonify
from flask.globals import request_ctx
from flask_cors import cross_origin, CORS
from jose import jwt

from config import client_origin_url, auth0_audience, auth0_domain, port

if not (client_origin_url and auth0_audience and auth0_domain):
    raise NameError("The required environment variables are missing. Check README and config.py.")

# Flask code in this file is originally based on
# https://auth0.com/docs/quickstart/backend/python/01-authorization

ALGORITHMS = ["RS256"]

APP = Flask(__name__)

cors = CORS(APP, resources={r"/api/*": {"origins": client_origin_url}})


# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@APP.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must start with"
                             " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                         "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must be"
                             " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_auth(f):
    """Determines if the Access Token is valid
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://" + auth0_domain + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=auth0_audience,
                    issuer="https://" + auth0_domain + "/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                 "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                 "description":
                                     "incorrect claims,"
                                     "please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header",
                                 "description":
                                     "Unable to parse authentication"
                                     " token."}, 401)

            request_ctx.current_user = payload
            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)

    return decorated


def requires_scope(required_scope):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False


# This doesn't need authentication
@APP.route("/api/healthcheck")
@cross_origin(headers=["Content-Type", "Authorization"])
def public():
    response = "Healthcheck endpoint OK! You don't need to be authenticated to see this."
    return response


# This needs authentication
@APP.route("/api/private")
@requires_auth
def private():
    response = "Hello from a private endpoint! You need to be authenticated to see this."
    return jsonify(message=response)


# This needs authentication. It returns the Google Maps API key for
# the frontend to use
@APP.route("/api/private/maps_key")
@requires_auth
def maps_api_key():
    key = google_secrets.get_secret("maps_api_key")
    return jsonify(message=key)

# WIP
# This needs authentication. Saves the trip data to the user. If view or edit are available, those users will have
# access to this trip data.
@APP.route("/api/private/save_trip", methods=["POST"])
@requires_auth
def save_trip():
    user_id = request.args.get("user_id")
    view_users = request.args.get("view")  # Since optional, will return null
    edit_users = request.args.get("edit")  # Since optional, will return null

    if user_id is None:
        return jsonify(message="Missing user_id!")

    request_body = request.json

    # TODO: Remove (This is used to show params in return message)
    parameters = jsonify(user_id=user_id, view_users=view_users, edit_users=edit_users)

    # TODO: Save user_id, body, view, and edit to database

    # TODO: Replace with message (Success)
    return jsonify(parameters=parameters.json, trip_data=request_body)

# WIP
# This needs authentication. Gets the trip data from the database and validates the user_id is of a user with
# view/edit permissions
@APP.route("/api/private/get_trip")
@requires_auth
def get_trip():
    user_id = request.args.get("user_id")

    if user_id is None:
        return jsonify(message="Missing user_id!")

    # TODO: Check if user_id is the owner

    # TODO: If not owner, then check if their email is listed in view/edit

    # TODO: Replace with getting data from database
    data = jsonify(user_id=user_id, sample="Some text")

    # TODO: Return data
    return jsonify(message="Successfully received data!", trip_data=data.json, permission="View")

from llm import match_to_places_api_types
# This needs authentication. It returns a list of google map "types"
# based on the preference tag argument (using gpt4o-mini). Could be
# hardcoded in a map in the frontend but this gives us a way to demo
# the LLM
@APP.route("/api/private/preferences_to_types", methods=['POST'])
@requires_auth
def preferences_to_types():
    data = request.json
    input_list = data.get('input_list', [])
    matched_list = match_to_places_api_types(input_list)
    return jsonify({'matched_list': matched_list.types})


# This needs authorization (we probably won't use this)
@APP.route("/api/private-scoped")
@cross_origin(headers=["Content-Type", "Authorization"])
@requires_auth
def private_scoped():
    if requires_scope("read:messages"):
        response = "Hello from a private endpoint! You need to be authenticated and have a scope of read:messages to see this."
        return jsonify(message=response)
    raise AuthError({
        "code": "Unauthorized",
        "description": "You don't have access to this resource"
    }, 403)


if __name__ == '__main__':
    APP.run(host="0.0.0.0", port=port, debug=True)
