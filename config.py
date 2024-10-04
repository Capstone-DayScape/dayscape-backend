# Set up configuration for the deployment, with default values
import os

# set to "prod" to use production environment
environment = os.environ.get("DAYSCAPE_ENVIRONMENT", "dev")

# GCP project in which to store secrets in Secret Manager.
gcloud_project_id = os.environ.get("PROJECT_ID", "263849479020")
