from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
import os

app = Flask(__name__)
CORS(app)
app.config['Access-Control-Allow-Origin'] = '*'
app.config["Access-Control-Allow-Headers"] = "Content-Type"
app.config["MONGO_URI"] = "mongodb://localhost:27017/openai"
mongo = PyMongo(app)
app.secret_key = "CodeSpecialist.com"
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
GOOGLE_CLIENT_ID = "990487476652-dct8v0k5a9l9776ci05g3dq15p8muj33.apps.googleusercontent.com"
os.environ["OPENAI_API_KEY"] = "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"

if __name__ == '__main__':
    from routes import routes_bp  # Import routes_bp here to avoid circular import
    from auth import auth_bp

    # Register the Blueprints
    app.register_blueprint(routes_bp)
    app.register_blueprint(auth_bp)

    app.run(host='0.0.0.0', port=5000, debug=True)
