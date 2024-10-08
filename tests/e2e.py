import os
import requests
import pytest

from config import DEV_URL

backend_url = os.environ.get("BACKEND_URL", DEV_URL)

def test_healthcheck():
    response = requests.get(backend_url + "/api/healthcheck")
    assert response.status_code == 200, "Expected status code 200"
    assert "Healthcheck endpoint OK" in response.text , "Response does not contain 'Healthcheck endpoint OK"
