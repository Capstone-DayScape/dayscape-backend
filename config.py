# Set up configuration for the deployment, with default values
import os
import pprint

# GCP project in which to store secrets in Secret Manager.
gcloud_project_id = os.environ.get("PROJECT_ID", "263849479020")

port = os.environ.get("PORT", 5556)

# As mentioned in the README, default values assume you are deploying
# both frontend and backend on your workstation

# Static endpoints for prod and dev deployments of this API. These
# endpoints are also the Auth0 "Audience", which is just the name of
# the Auth0 APIs for our dev and prod environments
PROD_URL = "https://backend-prod-263849479020.us-central1.run.app"
DEV_URL = "https://backend-dev-263849479020.us-east1.run.app"

# Set to "prod" to use production environment. This string is appended
# to all secret names in each environment. It also changes the Auth0
# audience below ↓↓↓
environment = os.environ.get("DAYSCAPE_ENVIRONMENT", "dev")
auth0_audience = os.environ.get("AUTH0_AUDIENCE", DEV_URL if environment == "dev" else PROD_URL)

# Database connection string; prod and dev databases are both in the
# same pg instance called dayscape-dev
db_connector = "moonlit-mesh-437320-t8:us-east1:dayscape-dev"
# Database name
db_name = "dayscape-dev-db" if environment == "dev" else "dayscape-prod-db"

# Deployments on Cloud Run must change the following variables to
# match the corresponding frontend deployment URL
client_origin_url = os.environ.get("CLIENT_ORIGIN_URL", "http://localhost:3000")

# This is the name of our Auth0 Tenant, you shouldn't need to change it.
auth0_domain = os.environ.get("AUTH0_DOMAIN", "dev-dvzptx3ol842v42i.us.auth0.com")

print("Attempting to start server with the following configuration:")
pprint.pprint(list(locals().items())[-8:])
