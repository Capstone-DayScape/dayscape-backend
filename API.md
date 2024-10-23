# API Documentation

## API Servers

Prod: https://backend-prod-263849479020.us-central1.run.app

Dev: https://backend-dev-263849479020.us-east1.run.app

To develop against this backend, you should follow the instructions in the main README to run it on your workstation.
The prod/dev frontend deployments are configured to use the actual endpoints above.

Frontend URLS:
- [prod](https://dayscape.netlify.app/) 
- [dev](https://dayscape-dev.netlify.app/)

## Authentication

Read the [Auth0 documentation](https://auth0.com/docs/quickstart/backend/python/02-using) first. There is also a more
in-depth [document](https://auth0.com/docs/get-started/architecture-scenarios/spa-api) about our setup. To summarize, to
authenticate with this API you must pass a valid access token. To get an access token, you must go through the Auth0
authorization flow by logging in from the Javascript application. The Auth0 Javascript SDK provides
`getAccessTokenSilently()` to use anywhere after this login. Then you can pass the token in the headers to all requests
to this API.

CORS is already configured, so just be aware that if you run the frontend at a nonstandard endpoint (E.g. the netlify
deploy previews, or http://localhost:1234), the API will reject your requests.

In addition, you can obtain an access token for testing in the "Test" tab of the Auth0 settings for the API, which
allows you to bypass the Auth0 login authorization.

## Request Endpoints

> [!TIP]
> Clicking the following links will scroll the page down to the corresponding api call.

- `api/public/` endpoints
- `api/private/` endpoints (require account)
    - [api/private/maps_key](#apiprivatemaps_key)
    - [api/private/save_trip](#apiprivatesave_tripuser_ididviewuserseditusers)
    - [api/private/get_trip](#apiprivateget_tripuser_idid)
    - [api/private/preferences_to_types](#apiprivatepreferences_to_types)

### `api/public/` endpoints

These endpoints will be used by anyone **without** an account.

### `api/private/` endpoints

These endpoints will be used by anyone **with** an account.

#### `api/public/preferences_to_types`

Method: **POST**
Parameters:
- `input_list`: List of preference strings

Returns a JSON list of [Google Places API
"Types"](https://developers.google.com/maps/documentation/places/web-service/supported_types). The
AI could hallucinate, so the output should be checked against a list
of valid types.

Mostly a demo method to test the LLM and explore deeper API
integration from the frontend.


#### `api/private/maps_key`

Method: **GET**

Parameters:

- None

Returns the Maps API Key for the frontend to use.

#### `api/private/save_trip?trip_id={id}&view={users}&edit={users}`

Method: **POST**

Parameters:

- `trip_id`: (Optional) The unique and valid trip ID. If left empty, a
  new trip will be created in the database, with the authenticated
  user as the owner.
- `view`: (Optional) The emails of the users (besides owner) who can
  access the trip to *view*.
- `edit`: (Optional) The emails of the users (besides owner) who can
  access the trip to *edit*.

Saves the trip data structure to the database as long as:

- the authenticated user has permissions to edit the trip
- the permission changes are valid.

The emails specified for `edit` and `view` will have access to the
trip. The authenticated user will be marked as 'owner' of the trip if
it's a new trip. Note that **owner** is an immutable field that is set
by the backend on trip creation. The trip itself should be sent
through the _body_ of the request.

**Valid permission changes**: only the _owner_ can add and remove editors and viewers

#### `api/private/get_owned_trips_list` <!--  -->

Method: **GET**

Parameters: none

Returns a list of trip IDs and names for trips owned by the authenticated user.

#### `api/private/get_shared_trips_list`
Method: **GET**

Parameters: none

Returns a list of trip IDs and names for trips that have been shared
with the authenticated user (I.E, the authenticated user is _editor_
or _viewer_ but not _owner_).

#### `api/private/get_trip?trip_id={id}`

Method: **POST**

Parameters:

- `trip_id`: The ID of the trip.

Returns the JSON trip structure if the authenticated user has
permissions to view the trip.

#### `api/private/get_preferences`

Method: **GET**

Parameters: none

Returns the JSON preferences stored in the db for the authenticated user.

#### `api/private/save_preferences`

Method: **POST**

Parameters: none

Updates the JSON preferences stored in the db for the authenticated
user from the body of the request. The entire json body of the request
will be stored.

