from flask import Blueprint, request, jsonify, session, abort, redirect
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
import jwt
import requests
import os
import pathlib
import google.auth.transport.requests
import google.oauth2.id_token
from flask_pymongo import PyMongo
from app import app  # Import app from the main app module

# Define GOOGLE_CLIENT_ID here or import it from your main app module
GOOGLE_CLIENT_ID = '990487476652-dct8v0k5a9l9776ci05g3dq15p8muj33.apps.googleusercontent.com'

# Initialize the Blueprint
auth_bp = Blueprint('auth', __name__)

# Google OAuth flow initialization
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ],
    redirect_uri="http://127.0.0.1:5000/callback",
)

# Initialize PyMongo with the app
mongo = PyMongo(app)

# Login required decorator
def login_required(function):
    def wrapper(*args, **kwargs):
        encoded_jwt = request.headers.get("Authorization").split("Bearer ")[1]  # Extract the actual token
        if not encoded_jwt:  # No JWT was found in the "Authorization" header
            return abort(401)
        else:
            return function()

    return wrapper

# JWT token generation
def generate_jwt(payload):
    encoded_jwt = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return encoded_jwt

# Callback route
@auth_bp.route("/callback")
def callback():
    try:
        # Fetch the access token and credentials using the authorization response
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials

        # Create a requests session and a token request
        request_session = requests.session()
        token_request = google.auth.transport.requests.Request(session=request_session)

        # Verify the ID token obtained from Google
        id_info = id_token.verify_oauth2_token(
            id_token=credentials._id_token,
            request=token_request,
            audience=GOOGLE_CLIENT_ID
        )

        # Store the user's Google ID in the session
        session["google_id"] = id_info.get("sub")

        # Removing the specific audience, as it is throwing an error
        del id_info['aud']

        # Generate a JWT token using the ID token's payload data
        jwt_token = generate_jwt(id_info)

        # Prepare user data for insertion into a MongoDB collection
        data = {
            'name': id_info.get('name'),
            'email': id_info.get('email'),
            'picture': id_info.get('picture')
        }

        # Insert the user data into a MongoDB collection named 'users'
        mongo.db.users.insert_one(data)

        # Redirect the user to a specific URL with the JWT token as a query parameter
        return redirect(f"http://localhost:5173/chat?jwt={jwt_token}")
    except Exception as e:
        # Handle exceptions (e.g., authentication errors)
        return jsonify({'error': str(e)}), 500

# Login route
@auth_bp.route("/auth/google")
def login():
    try:
        # Generate the authorization URL and state
        authorization_url, state = flow.authorization_url()
        # Store the state so the callback can verify the auth server response.
        session["state"] = state
        return jsonify({'auth_url': authorization_url}), 200
    except Exception as e:
        # Handle exceptions (e.g., URL generation errors)
        return jsonify({'error': str(e)}), 500

# Logout route
@auth_bp.route("/logout")
def logout():
    # Clear the local storage from frontend
    session.clear()
    return jsonify({"message": "Logged out"}), 202

# Home page route with login required
@auth_bp.route("/home")
@login_required
def home_page_user():
    try:
        # Extract the JWT token from the "Authorization" header
        encoded_jwt = request.headers.get("Authorization").split("Bearer ")[1]

        # Attempt to decode and verify the JWT token
        decoded_jwt = jwt.decode(encoded_jwt, app.secret_key, algorithms=['HS256'])

        # Return a JSON response containing the decoded JWT payload
        return jsonify(decoded_jwt), 200
    except Exception as e:
        # Return an error response if JWT decoding fails
        return jsonify({"message": "Decoding JWT Failed", "exception": str(e)}), 500

# # Blueprint registration should come after all routes are defined
app.register_blueprint(auth_bp)



if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=5000, debug=True)