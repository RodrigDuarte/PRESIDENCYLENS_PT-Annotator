import jwt
import json

from flask import Flask
from flask import session
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import abort

from functools import wraps
from http import HTTPStatus
from os import environ as env
from urllib.request import urlopen
from authlib.integrations.flask_client import OAuth


class Auth0Service:
    """Perform JSON Web Token (JWT) validation using PyJWT"""

    def __init__(self):
        self.issuer_url = None
        self.audience = None
        self.algorithm = "RS256"
        self.jwks_uri = None

    def initialize(self, auth0_domain, auth0_audience):
        self.issuer_url = f"https://{auth0_domain}/"
        self.jwks_uri = f"{self.issuer_url}.well-known/jwks.json"
        self.audience = auth0_audience

    def get_signing_key(self, token):
        try:
            jwks_client = jwt.PyJWKClient(self.jwks_uri)

            return jwks_client.get_signing_key_from_jwt(token).key
        except Exception as error:
            json_abort(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "error": "signing_key_unavailable",
                    "error_description": error.__str__(),
                    "message": "Unable to verify credentials",
                },
            )

    def validate_jwt(self, token):
        try:
            jwt_signing_key = self.get_signing_key(token)

            payload = jwt.decode(
                token,
                jwt_signing_key,
                algorithms=self.algorithm,
                audience=self.audience,
                issuer=self.issuer_url,
            )
        except Exception as error:
            json_abort(
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "invalid_token",
                    "error_description": error.__str__(),
                    "message": "Bad credentials",
                },
            )
            return

        return payload


auth0_service = Auth0Service()


# Error handler
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


class AuthDecorators:
    def __init__(self):
        pass

    def requires_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return decorated

    def requires_role(role: str):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if "user" not in session:
                    return redirect(url_for("login"))
                user = session["user"]
                if "roles" not in user or role not in user["roles"]:
                    return jsonify({"error": "Unauthorized"}), 403
                return f(*args, **kwargs)

            return decorated

        return decorator


def json_abort(status_code, data=None):
    response = jsonify(data)
    response.status_code = status_code
    abort(response)
