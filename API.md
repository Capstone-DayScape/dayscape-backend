# API Documentation
 
# Endpoints
Prod: https://backend-prod-263849479020.us-central1.run.app

Dev: https://backend-dev-263849479020.us-east1.run.app

NOTE: You can create additional endpoints in [Cloud Run](https://console.cloud.google.com/run/) for testing. Especially if you are trying to test a frontend dev deployment for your branch, because you will need to modify the CORS settings for the backend so that it accepts requests from your frontend deployment.

# TODO: Authentication
CORS settings will allow connections from the prod deployment of the frontend. 

Connections from any frontend deployments other than prod must be cryptographically authenticated  (or authenticated with CORS from a temporary backend deployment)

# TODO api/v1/whatever
# TODO etc.
