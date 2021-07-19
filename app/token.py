from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_current_user,
    verify_jwt_in_request
)
from functools import wraps
import re
from flask import g, current_app, jsonify

from bson.objectid import ObjectId

from app import mongo
from functools import wraps


def init_token():
   jwt = JWTManager()
   return jwt


def get_token(jwt, app):
   app.config['JWT_SECRET_KEY'] = '11qwe11'  # Change this!
   jwt.init_app(app)

   @jwt.user_identity_loader
   def user_identity_lookup(user):
       print("user_identity_lookup")
       print(user)
       return str(user)

   @jwt.user_loader_callback_loader
   def user_loader_callback(identity):
       print("user_loader_callback")
       user = mongo.db.Users.find_one({
           "email": identity})
       print('load the user by its identity')
       print('load identity by user')
       if user is None or "email" not in user:
           return None
       return user



def manager_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if user["role"] == "manager":
            return fn(*args, **kwargs)
        else:
         return jsonify(msg='access denied'), 403
    return wrapper