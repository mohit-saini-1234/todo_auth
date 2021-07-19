from flask import (Flask , Blueprint, g, request, abort, jsonify , Flask)
import base64
import datetime
import json
import re
import requests
import uuid
import smtplib
from threading import Thread
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from random import randint 
import random
from app import mongo
from app import token
from app.token import manager_required 
import jwt
from app.util import serialize_doc
from bson import json_util
from bson.objectid import ObjectId
from flask_jwt_extended import (JWTManager, create_access_token,current_user,
                                get_current_user,  jwt_required)
from passlib.apps import custom_app_context as pwd_context
from passlib.hash import pbkdf2_sha256
from app.config import sender_mail
from app.config import MAIL_PASSWORD ,MAIL_SERVER ,MAIL_USERMAIL , MAIL_PORT
from app.config import url_api
from app.config import app 


app.config['MAIL_SERVER']= MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERMAIL
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

bp = Blueprint('users', __name__, url_prefix='/')


@bp.route('/register', methods=['POST'])
def register():
   role = request.json.get("role", "user")
   name = request.json.get("name", None)
   username = request.json.get("username", None)
   password = request.json.get("password", None)
   Email = request.json.get("email", None)
 
   if not name:
      return jsonify({"msg": "please enter name "}), 400
   if not username:
      return jsonify({"msg":"please enter username"}) , 400
   if not password:
      return jsonify({"msg": "please enter password"}), 400
   if not Email:
      return jsonify({"msg": "please enter email "}), 400
       
   check_email = mongo.db.Users.count({
      "email"  : Email
      
    })
   
   if check_email > 0 :
      return jsonify({"msg": "email already taken"}), 500

   check_username = mongo.db.Users.count({
      "username"  : username
      
    })
   
   if check_username > 0 :
      return jsonify({"msg": "username already taken"}), 500
        
   id = mongo.db.Users.insert_one({
        "role" : role ,
        "name": name,
        "password": pbkdf2_sha256.hash(password),
        "username": username,
        "email" : Email
    }).inserted_id  
   if id is not None :
      msg = Message('Hello', sender = sender_mail , recipients = [Email] )
      msg.body = "Hello, welcome--"+str(name)+"--you are registered successfully"
      mail.send(msg)
   
   
   return jsonify(str(id))




@bp.route('/User_login', methods=['POST'])
def login():
   log_mail = request.json.get("email", None)
   password = request.json.get("password", None)
   if not log_mail:
      return jsonify(msg="Missing email parameter"), 400
   if not password:
      return jsonify(msg="Missing password parameter"), 400

   User_A = mongo.db.Users.find_one({"email": log_mail})
   if User_A is None:
      return jsonify(msg="usermail doesn't exists"), 400
   if not pbkdf2_sha256.verify(password, User_A["password"]):
      return jsonify(msg="password is wrong"), 400
   
   user1 = log_mail
   print("check",user1)
   expires = datetime.timedelta(days=1)
   access_token = create_access_token(identity=user1, expires_delta=expires)
   return jsonify(access_token=access_token), 200



@bp.route('/protected_user', methods=['GET'])
@jwt_required
def protected():
   current_user = get_current_user()
   current_user["_id"] = str(current_user["_id"])
   user = json.dumps(current_user,default=json_util.default)
   return user, 200


@bp.route('/profile_info', methods=['PUT', 'GET'])
@jwt_required
def profile():
   current_user = get_current_user()
   current_user["_id"] = str(current_user["_id"])
   user = current_user["_id"]
   return(str({"login as ": user})), 200

@bp.route('/reset_pass', methods=['PUT'])
@jwt_required
def pass_Reset():
   current_user = get_current_user()
   current_user["username"] = str(current_user["username"])
   current_user["email"] = str(current_user["email"])
   
   user = current_user["username"]
   email = current_user["email"]
   
   old_password = request.json.get("password", None)
   new_password = request.json.get("new_password", None)
   confirm_new_password = request.json.get("confirm_new_password", None)


   hash = pbkdf2_sha256.hash(new_password)
   if not old_password:
      return jsonify(msg="Missing old password parameter"), 400
   if old_password == new_password :
      return jsonify(msg="new password should be diffrent from old password")
   if new_password != confirm_new_password :
      return jsonify(msg="new password dose not match"), 400

   log_user = mongo.db.Users.find_one({"username":user})
   if log_user is None:
      return jsonify(msg = "usernname dose not exist")

   if not pbkdf2_sha256.verify(old_password, log_user["password"]):
      return jsonify(str(msg="password is wrong")), 400


   update_json = {}
   if new_password is not None:
         update_json["password"] = hash
   ret = mongo.db.Users.update({
       "username": user
         }, {
       "$set": update_json
         }, upsert=False)

   if ret is not None:
      msg = Message('Password Change Alert', sender = sender_mail, recipients = [email] )
      msg.body = "Warning - Password Chnage Request Found  " 
      mail.send(msg)  

   return jsonify(str(ret))


@bp.route('/forgot_pass', methods=['GET']) 
def pass_Forgot():  
   email = request.json.get("email", None)
   if not email:
      return jsonify(msg="Missing email parameter"), 400
   
   string_bytes = email.encode("ascii")
   base64_bytes = base64.b64encode(string_bytes)
   base64_string = base64_bytes.decode("ascii")
   
   is_mail= mongo.db.Users.find_one({"email":email})
   if is_mail is not None:
      msg = Message('Password Forgot Request', sender = sender_mail , recipients =[email] )
      msg.body = "Request for New Password Is Accepted - Open The Link And Get A New Random Password "
      msg.html = url_api.replace("{{DATA}}",str(base64_string))
      mail.send(msg)
                            
   return "Password Forgot Mail Send To Your Mail"

@bp.route('/set_pass', methods=['GET']) 
def set_tempPass():
   email = request.args.get("Email")
   base64_bytes = email.encode("ascii")
   sample_string_bytes = base64.b64decode(base64_bytes)
   sample_string = sample_string_bytes.decode("ascii")
   email = sample_string

   if not email:
      return jsonify(msg="Missing email parameter"), 400
    
   E_mail = mongo.db.Users.find_one({"email": email})
   password = uuid.uuid4().hex
   hash = pbkdf2_sha256.hash(password)
   update_json = {}
   if password is not None:
      update_json["password"] = hash
   ret = mongo.db.Users.update({
      "email": email
         }, {
      "$set": update_json
         }, upsert=False)
    
   if ret is not None:
      msg = Message('New Password Set', sender = sender_mail , recipients =[email] )
      msg.body = "your new password is -"+str(password)+"-you can change it as you want"
      mail.send(msg)

   return (str(ret))



@bp.route("/update/<string:id>", methods=['PUT'])
@manager_required
def update_todo(id):

   if not request.json:
      abort(500)

   role = request.json.get("role", "user")
   username = request.json.get("username", "")

   if username is None:
      return jsonify(message="Invalid Request"), 500

   update_json = {}
   if role is not None:
      update_json["role"] = role

   if username is not None:
      update_json["username"] = username


   # match with Object ID
   ret = mongo.db.Users.update({
      "_id": ObjectId(id)
   }, {
        "$set": update_json
   }, upsert=False)
   return jsonify(str(ret))

@bp.route("/del_todo/<string:id>", methods=["DELETE"])
@manager_required
def delete_todo(id):

   ret = mongo.db.tasks.remove({
        "_id" : ObjectId(id)
    })

   return jsonify(str(ret))  
