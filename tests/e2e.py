import os
import requests
import pytest

backend_url = os.environ["BACKEND_URL"]

def test_hello_world_response():
    response = requests.get(backend_url)
    assert response.status_code == 200, "Expected status code 200"
    assert "Hello World!" in response.text , "Response does not contain 'Hello World!"
