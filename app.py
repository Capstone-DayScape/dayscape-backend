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


# Returns the Google Maps API key for the frontend to use
@APP.route("/api/private/maps_key")
@requires_auth
def maps_api_key():
    key = google_secrets.get_secret("maps_api_key")
    return jsonify(message=key)

# STUB
# Saves the trip data to the database,
# optionally modifying trip permissions. Creates a new trip if no
# trip_id is supplied
@APP.route("/api/private/save_trip", methods=["POST"])
@requires_auth
def save_trip():
    # If trip_id exists:
    # - query database for trip
    # - check that the authenticated user has edit permission or is owner
    # - check that any permission changes are valid
    # - save trip to database

    # Otherwise:
    # - create new trip, set authenticated user as owner

    # If trip to be saved is not valid, return error
    response = "Trip saved:"
    return response

# STUB
# Returns a list of trip IDs and names for
# trips owned by the authenticated user.
@APP.route("/api/private/get_owned_trips_list")
@requires_auth
def get_owned_trips_list():

    # TODO:
    # - get Auth0 user
    # - Query database for owned trips

    # list of trip IDs/names to be displayed on profile page
    example_trips = {
        "60f62fed-df59-4ad0-8e73-677e3fda5d9a": "Summer Family Beach Trip",
        "1336c22f-b80c-4b39-9528-a2bfded82e29": "My mountain trip",
        "936ba739-db01-45c8-ba46-38ec8acc21f7": "London 2026",
        "51c28468-0930-4fcf-b8a7-3c2d58e9ac27": "Example trip name",
    }
    data = jsonify(example_trips)
    return jsonify(data.json)

# STUB
# Returns a list of trip IDs and names for trips that have been shared
# with the authenticated user
@APP.route("/api/private/get_shared_trips_list")
@requires_auth
def get_shared_trips_list():
    # TODO:
    # - get Auth0 user
    # - Query database for trips where user is viewer or editor (not owner)

    # list of trip IDs/names to be displayed on profile page ("Shared with me")
    example_trips = {
        "60f62fed-df59-4ad0-8e73-677e3fda5d9a": "Shared Hiking Trip",
        "1336c22f-b80c-4b39-9528-a2bfded82e29": "Corrie's Wedding Trip",
        "936ba739-db01-45c8-ba46-38ec8acc21f7": "Night City 2077",
        "51c28468-0930-4fcf-b8a7-3c2d58e9ac27": "Example shared trip name",
    }
    data = jsonify(example_trips)
    return jsonify(data.json)

    
# STUB
# Returns the JSON trip structure if the authenticated user has
# permissions to view the trip.
@APP.route("/api/private/get_trip")
@requires_auth
def get_trip():
    # - Query database for trip at the given trip_id
    # - Check that the authenticated user has permissions to view or edit, or is the owner
    # - return trip json

    example_trip = {
        "name": "whatever",
        "other_field": "whatever"}

    data = jsonify(example_trip)
    return jsonify(data.json)

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
