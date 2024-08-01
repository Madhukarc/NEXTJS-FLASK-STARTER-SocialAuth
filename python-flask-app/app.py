from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import bcrypt
import jwt
import os
from functools import wraps
import requests
from dotenv import load_dotenv
# from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow as GoogleFlow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


load_dotenv()

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient(os.getenv('MONGO_URI'))
db = client['user_management']
users_collection = db['users']

SECRET_KEY = 'AZ9IFxR1OhWk4QksexFe2Chdwv7Eaiebv9z35LLlBVY'
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
FRONTEND_URL = os.getenv('FRONTEND_URL')
GOOGLE_SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
# # Google OAuth flow
# flow = Flow.from_client_secrets_file(
#     'client_secret.json',
#     #scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
#     scopes= GOOGLE_SCOPES,
#     redirect_uri='http://localhost:5000/api/auth/google/callback'
# )

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token.split()[1], SECRET_KEY, algorithms=["HS256"])
            current_user = users_collection.find_one({'_id': ObjectId(data['user_id'])})
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/signup', methods=['POST'])
def signup():
    user_data = request.json
    existing_user = users_collection.find_one({'email': user_data['email']})
    if existing_user:
        return jsonify({'message': 'User already exists'}), 400
    
    hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
    new_user = {
        'name': user_data['name'],
        'email': user_data['email'],
        'password': hashed_password,
        'provider': 'local',
        'createdAt': datetime.utcnow(),
        'updatedAt': datetime.utcnow()
    }
    result = users_collection.insert_one(new_user)
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    auth = request.json
    user = users_collection.find_one({'email': auth['email']})
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if bcrypt.checkpw(auth['password'].encode('utf-8'), user['password']):
        token_expiration = datetime.utcnow() + timedelta(days=30 if auth.get('stay_signed_in') else 1)
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': token_expiration
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

# Google OAuth setup
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # For development only
GOOGLE_SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
google_flow = GoogleFlow.from_client_secrets_file(
    'client_secret.json',
    scopes=GOOGLE_SCOPES,
    redirect_uri='http://localhost:5000/api/auth/google/callback'
)

# Facebook OAuth setup
FACEBOOK_APP_ID = '1169934434131676'
FACEBOOK_APP_SECRET = '693fc00815ca6dff2be62e8b9b9ef4ae'

@app.route('/api/auth/google')
def google_auth():
    authorization_url, state = google_flow.authorization_url()
    return redirect(authorization_url)

@app.route('/api/auth/google/callback')
def google_auth_callback():
    google_flow.fetch_token(code=request.args.get('code'))
    credentials = google_flow.credentials
    
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    
    email = user_info.get('email')
    name = user_info.get('name')
    
    user = users_collection.find_one({'email': email})
    if not user:
        user = {
            'email': email,
            'name': name,
            'provider': 'google',
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
    else:
        users_collection.update_one({'_id': user['_id']}, {'$set': {'updatedAt': datetime.utcnow()}})

    token = jwt.encode({
        'user_id': str(user['_id']),
        'exp': datetime.utcnow() + timedelta(days=30)
    }, SECRET_KEY, algorithm="HS256")

    return redirect(f'http://localhost:3000/login?token={token}')

@app.route('/api/auth/facebook')
def facebook_auth():
    redirect_uri = url_for('facebook_auth_callback', _external=True)
    return redirect(f'https://www.facebook.com/v12.0/dialog/oauth?client_id={FACEBOOK_APP_ID}&redirect_uri={redirect_uri}&scope=email')

@app.route('/api/auth/facebook/callback')
def facebook_auth_callback():
    if 'error' in request.args:
        return jsonify({'error': request.args['error_description']}), 400

    code = request.args.get('code')
    redirect_uri = url_for('facebook_auth_callback', _external=True)
    
    # Exchange code for access token
    token_url = f'https://graph.facebook.com/v12.0/oauth/access_token'
    token_payload = {
        'client_id': FACEBOOK_APP_ID,
        'redirect_uri': redirect_uri,
        'client_secret': FACEBOOK_APP_SECRET,
        'code': code
    }
    token_response = requests.get(token_url, params=token_payload)
    access_token = token_response.json().get('access_token')

    if not access_token:
        return jsonify({'error': 'Failed to obtain access token'}), 400

    # Get user info
    user_info_url = 'https://graph.facebook.com/me'
    user_info_payload = {
        'fields': 'id,name,email',
        'access_token': access_token
    }
    user_info = requests.get(user_info_url, params=user_info_payload).json()

    facebook_id = user_info['id']
    email = user_info.get('email', f"{facebook_id}@facebook.com")
    name = user_info.get('name', '')
    
    user = users_collection.find_one({'email': email})
    if not user:
        user = {
            'email': email,
            'name': name,
            'provider': 'facebook',
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow()
        }
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
    else:
        users_collection.update_one({'_id': user['_id']}, {'$set': {'updatedAt': datetime.utcnow()}})

    token = jwt.encode({
        'user_id': str(user['_id']),
        'exp': datetime.utcnow() + timedelta(days=30)
    }, SECRET_KEY, algorithm="HS256")

    return redirect(f'http://localhost:3000//login?token={token}')

# ... (keep other existing routes) ...
def serialize_user(user):
    user['_id'] = str(user['_id'])
    user['createdAt'] = user['createdAt'].isoformat() if 'createdAt' in user else None
    user['updatedAt'] = user['updatedAt'].isoformat() if 'updatedAt' in user else None
    if 'password' in user:
        del user['password']
    return user

@app.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    users = list(users_collection.find())
    return jsonify([serialize_user(user) for user in users])

@app.route('/api/users', methods=['POST'])
@token_required
def add_user(current_user):
    user = request.json
    user['createdAt'] = datetime.utcnow()
    user['updatedAt'] = user['createdAt']
    result = users_collection.insert_one(user)
    user['_id'] = str(result.inserted_id)
    return jsonify(serialize_user(user)), 201

@app.route('/api/users/<id>', methods=['GET'])
@token_required
def get_user(current_user, id):
    user = users_collection.find_one({'_id': ObjectId(id)})
    if user:
        return jsonify(serialize_user(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/users/<id>', methods=['PUT'])
@token_required
def update_user(current_user, id):
    user_data = request.json
    user_data['updatedAt'] = datetime.utcnow()
    result = users_collection.update_one(
        {'_id': ObjectId(id)}, 
        {'$set': user_data}
    )
    if result.modified_count:
        updated_user = users_collection.find_one({'_id': ObjectId(id)})
        return jsonify(serialize_user(updated_user))
    return jsonify({'error': 'User not found or no changes made'}), 404

@app.route('/api/users/<id>', methods=['DELETE'])
@token_required
def delete_user(current_user, id):
    result = users_collection.delete_one({'_id': ObjectId(id)})
    if result.deleted_count:
        return '', 204
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)