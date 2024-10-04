from google.cloud import secretmanager

import os

from config import environment, gcloud_project_id

# ID of the secret to create.
secret_id = "test-secret" + "-" + environment

# Create the Secret Manager client.
client = secretmanager.SecretManagerServiceClient()

name = f"projects/{gcloud_project_id}/secrets/{secret_id}/versions/latest"

# Access the secret version
response = client.access_secret_version(request={"name": name})

# Decoding the secret payload
payload = response.payload.data.decode("UTF-8")

# WARNING: Do not print the secret in a production environment - this
# snippet is showing how to access the secret material.
print(f"Plaintext: {payload}")
