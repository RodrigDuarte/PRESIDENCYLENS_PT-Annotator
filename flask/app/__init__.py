from flask import Flask
from os import environ as env
from authlib.jose import JsonWebToken
from dotenv import find_dotenv, load_dotenv
from authlib.integrations.flask_client import OAuth


# CONFIGURE FLASK APP
app = Flask(__name__)
app.secret_key = env.get("AUTH0_APP_SECRET_KEY")
app.config["AUTH0_DOMAIN"] = env.get("AUTH0_DOMAIN")
app.config["AUTH0_CLIENT_ID"] = env.get("AUTH0_CLIENT_ID")
app.config["AUTH0_CLIENT_SECRET"] = env.get("AUTH0_CLIENT_SECRET")
app.config["TEMPLATES_AUTO_RELOAD"] = True

# CONFIGURE OAUTH
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    api_base_url=f"https://{env.get('AUTH0_DOMAIN')}",
    access_token_url=f"https://{env.get('AUTH0_DOMAIN')}/oauth/token",
    authorize_url=f"https://{env.get('AUTH0_DOMAIN')}/authorize",
    client_kwargs={
        "scope": "openid profile email roles",
    },
    server_metadata_url=f"https://{env.get('AUTH0_DOMAIN')}/.well-known/openid-configuration",
)
