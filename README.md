# DayScape backend

Backend application for DayScape <- TODO: add link to frontend website when it's up

[API Documentation](API.md)

# Development

This is a Python [Flask](https://flask.palletsprojects.com/) application that provides an API to be used by [dayscape-frontend](https://github.com/Capstone-DayScape/dayscape-frontend). 

The application is deployed using Google Cloud Run, initially based on [this](https://github.com/GoogleCloudPlatform/python-docs-samples/tree/main/run/helloworld) boilerplate project from Google.

Requirements:
- Service ID credential for `dayscape-backend`
- Python 3.12.

## Secrets Management

Secrets (such as API keys) are either stored in [Secret Manager](https://console.cloud.google.com/security/secret-manager), or eliminated by authenticating with directly to a Google Cloud API using application credentials. On the Cloud Run deployments, the application is automatically authenticated using the `dayscape-backend` service ID. To run locally, you must [create a credential](https://console.cloud.google.com/apis/credentials) for this service ID and save it on your system.

I recommend saving it in `.adc.json` since we have that file in the .gitignore to prevent accidental publishing. Note that if you DO accidentally commit this file, Google will detect it and disable that credential.

Then export the following variable so the Google Cloud client libraries can use the key:

```
export GOOGLE_APPLICATION_CREDENTIALS=adc.json
```


## Using Python Venv

To install the Python package dependencies, you can use `python -m pip install -r requirements.txt`. However, it is recommended to use a [virtual environment](https://docs.python.org/3/library/venv.html) to install the packages.

You can add the following alias to your .bashrc, or just enter the commands locally in your shell when you want to work on this application:

```bash
vactivate () {
    python3.12 -m venv .venv
    source .venv/bin/activate
	python3.12 -m pip install -r requirements.txt
}
```

## Running application

```
gunicorn --bind :5556 --workers 1 --threads 8 --timeout 0 app:app
```

NOTE: the :5556 port does matter for CORS (TODO: set up CORS)

## Tests

Install Pytest:

```bash
python -m pip install pytest
```

Run tests:
```bash
python -m pytest
```

For more info, [this](https://realpython.com/python-testing/) is a good introduction to testing in Python.

## E2E Tests

Set the backend url:

```
export BACKEND_URL=<url for the backend deployment you are testing>
```

Run test:
```
pytest tests/e2e.py 
```

# Container Development and Deployment

The development steps above describe how to build and run the Python application on bare metal on your workstation. In reality the application is deployed as a [container](https://www.redhat.com/en/topics/containers/whats-a-linux-container) to Cloud Run. Each push to a branch will build and deploy to the dev instance, and when you merge a PR with master, the same will happen for prod.

## Building and Running the Container locally
In order to build and test the container, you need the `docker` or `podman` command installed on your system. These instructions use `podman`, but they should be interchangeable.

- Build the container:
```bash
podman build . -t dayscape_backend:latest
```

- Run the container:
```bash
podman run -e PORT=5556 -e GOOGLE_APPLICATION_CREDENTIALS=adc.json -p 5556:5556 dayscape_backend:latest 
```

## TODO: additional development documentation
