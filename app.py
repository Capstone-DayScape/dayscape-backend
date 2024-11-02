import google_secrets

import json
from six.moves.urllib.request import urlopen
from functools import wraps

from flask import Flask, request, jsonify
from flask.globals import request_ctx
from flask_cors import cross_origin, CORS
from jose import jwt

import database
import requests

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
            # Also get the user info
            request_ctx.user_info = get_userinfo(token)

            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)

    return decorated

# We can't call the auth0 /userinfo endpoint with each request because
# of a rate limit (something like 5-10/minute). So we just cache the
# response in the database and reuse it. We also prune any cached
# responses older than 10 hours because they're no longer valid.
def get_userinfo(token):
    check = database.db_check_userinfo(token)
    if check: return check
    url = f"https://{auth0_domain}/userinfo"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise AuthError({"code": "userinfo_request_failed", "description": "Failed to fetch user info"}, response.status_code)
    data = response.json()
    database.db_cache_userinfo(token, data)
    return data


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


# Returns the Google Maps API key for the frontend to use
@APP.route("/api/private/maps_key")
@requires_auth
def maps_api_key():
    key = google_secrets.get_secret("maps_api_key")
    return jsonify(message=key)

# Returns a list of trip IDs and names for
# trips owned by the authenticated user.
@APP.route("/api/private/get_owned_trips_list")
@requires_auth
def get_owned_trips_list():
    email = request_ctx.user_info.get("email")
    trips = database.db_get_owned_trips(email)
    objects = [{"uuid": str(uuid), "name": name if name is not None else ""} for uuid, name in trips]
    data = jsonify(objects)
    return data.json

# STUB
# Returns a list of trip IDs and names for trips that have been shared
# with the authenticated user
@APP.route("/api/private/get_shared_trips_list")
@requires_auth
def get_shared_trips_list():
    email = request_ctx.user_info.get("email")
    trips = database.db_get_shared_trips(email)
    objects = [{"uuid": str(uuid), "name": name if name is not None else ""} for uuid, name in trips]
    data = jsonify(objects)
    return data.json

from llm import match_to_places_api_types
# Returns a list of google map "types" based on the preference tag
# argument (using gpt4o-mini). Could be hardcoded in a map in the
# frontend but this gives us a way to demo the LLM
@APP.route("/api/public/preferences_to_types", methods=['POST'])
def preferences_to_types():
    data = request.json
    input_list = data.get('input_list', [])
    matched_list = match_to_places_api_types(input_list)
    return jsonify({'matched_list': matched_list.types})

# Saves the trip data to the database, optionally modifying trip
# permissions. Creates a new trip if no trip_id is supplied. Returns
# trip_id.
@APP.route("/api/private/save_trip", methods=['POST'])
@requires_auth
def save_trip():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    trip_name = request.args.get('trip_name', None)
    trip_data = request.json
    # lists of emails
    view = request.args.get('view', None)
    edit = request.args.get('edit', None)
    if view is not None:
        view = [email.strip() for email in view.split(',')]
    if edit is not None:
        edit = [email.strip() for email in edit.split(',')]

    id = database.db_save_trip(email, trip_id, trip_name, trip_data, view, edit)
    return str(id)

# Returns the JSON trip structure if the authenticated user has
# permissions to view the trip.
@APP.route("/api/private/get_trip", methods=['POST'])
@requires_auth
def get_trip():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    data = jsonify(database.db_get_trip(email, trip_id))
    return data.json

# Returns the JSON preferences stored in the db for the authenticated user.
@APP.route("/api/private/get_preferences")
@requires_auth
def get_preferences():
    email = request_ctx.user_info.get("email")
    data = jsonify(database.db_get_preferences(email))
    print("data")
    print(data)
    return (data.json)

# saves the JSON body of the request as user preferences in the db
@APP.route("/api/private/save_preferences", methods=['POST'])
@requires_auth
def save_preferences():
    email = request_ctx.user_info.get("email")
    data = request.json
    database.db_save_preferences(email, data)
    return "saved preferences"

@APP.route("/api/private/delete_trip", methods=['GET'])
@requires_auth
def delete_trip():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    try:
        database.db_delete_trip(email, trip_id)
        return jsonify({"message": "Trip deleted successfully."}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@APP.route("/api/private/get_trip_name", methods=['GET'])
@requires_auth
def get_trip_name():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    try:
        trip_name = database.db_get_trip_name(email, trip_id)
        return jsonify({"trip_name": trip_name}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@APP.route("/api/private/get_trip_viewers", methods=['GET'])
@requires_auth
def get_trip_viewers():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    try:
        viewers = database.db_get_viewers(email, trip_id)
        return jsonify({"viewers": viewers}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@APP.route("/api/private/get_trip_editors", methods=['GET'])
@requires_auth
def get_trip_editors():
    email = request_ctx.user_info.get("email")
    trip_id = request.args.get('trip_id', None)
    try:
        editors = database.db_get_editors(email, trip_id)
        return jsonify({"editors": editors}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    APP.run(host="0.0.0.0", port=port, debug=True)
