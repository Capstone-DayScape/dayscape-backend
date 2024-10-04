from google.cloud import secretmanager

import os

from config import environment, gcloud_project_id

# Create the Secret Manager client.
client = secretmanager.SecretManagerServiceClient()

def get_secret(name:str) -> str:
    # ID of the secret to create.
    secret_id = name + "-" + environment

    name = f"projects/{gcloud_project_id}/secrets/{secret_id}/versions/latest"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # Decoding the secret payload
    return response.payload.data.decode("UTF-8")
