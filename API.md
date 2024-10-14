# API Documentation

## API Servers

Prod: https://backend-prod-263849479020.us-central1.run.app

Dev: https://backend-dev-263849479020.us-east1.run.app

To develop against this backend, you should follow the instructions in the main README to run it on your workstation.
The prod/dev frontend deployments are configured to use the actual endpoints above.

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
    - [api/private/save_trip](#apiprivatesave_tripuser_ididdatadataviewuserseditusers)
    - [api/private/get_trip](#apiprivateget_tripuser_idid)

### `api/public/` endpoints

These endpoints will be used by anyone **without** an account.

### `api/private/` endpoints

These endpoints will be used by anyone **with** an account.

#### `api/private/maps_key`

Method: **GET**

Parameters:

- None

Returns the Maps API Key for the frontend to use.

#### `api/private/save_trip?user_id={id}&data={data}&view={users}&edit={users}`

Method: **POST**

Parameters:

- `user_id`: The ID of the user's account to which the data will be saved.
- `data`: The json structure (blob) being saved.
- `view`: (Optional) The emails of the users who can access the trip to *view*.
- `edit`: (Optional) The emails of the users who can access the trip to *edit*.

Saves the trip data structure to the user's account in the database. The users specified for `edit` and `view` will have
access to the trip.

#### `api/private/get_trip?user_id={id}`

Method: **GET**

Parameters:

- `user_id`: The ID of the user's account to get trip data.

Returns the json structure (blob) to be parsed/used. The `user_id` will be cross-referenced with _Auth0_ to check if the
user's email has access to the trip.
