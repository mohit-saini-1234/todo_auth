
from os import name
from flask import (
    Blueprint, g, request, abort, jsonify , Flask
)
from app.token import manager_required
from app.token import admin_required
from bson.objectid import ObjectId
import datetime
import dateutil.parser
from app import mongo
from app import token
import jwt
from flask_jwt_extended import ( JWTManager,jwt_optional ,
    jwt_required, create_access_token, get_current_user
)
import uuid
from app.util import serialize_doc

bp = Blueprint('tasks', __name__, url_prefix='')

@bp.route('/users_tasks', methods=['POST'])
@manager_required
def users_tasks():
    task = request.json.get("task", None)
    description = request.json.get("description", None)

    if not task or not description :
           return jsonify({"msg": "Invalid Request"}), 400
    check_task = mongo.db.tasks.count({
       "task" : task 
   })
    if check_task > 0 :
       return jsonify({"msg": "task already in collection"}), 500
    id = mongo.db.tasks.insert_one({
       "task": task,
       "description" : description
   }).inserted_id
    return jsonify(str(id))
        


@bp.route('/users_tasks', methods=['POST'])
@admin_required
def users_TasksByadmin():
    task = request.json.get("task", None)
    description = request.json.get("description", None)

    if not task or not description :
           return jsonify({"msg": "Invalid Request"}), 400
    check_task = mongo.db.tasks.count({
       "task" : task 
   })
    if check_task > 0 :
       return jsonify({"msg": "task already in collection"}), 500
    id = mongo.db.tasks.insert_one({
       "task": task,
       "description" : description
   }).inserted_id
    return jsonify(str(id))
#task assign by manager
@bp.route('/assign_tasksbymanager', methods=['POST'])
@manager_required
def tasks_assignBymanager():
    user_id = request.json.get("user_id", None)
    due = request.json.get("due", None)
    task_id = request.json.get("task_id" , None)
    status = request.json.get("status" , None)


    is_user = mongo.db.Users.find_one({"_id":user_id})
    if is_user["role"]=="admin":
        return jsonify({"msg": "manager can't Assign task to admin"})


    if due is not None:
        due = datetime.datetime.strptime(due, "%d-%m-%Y")
    else:
        due = datetime.datetime.now()


    if not user_id or not task_id :
        return jsonify({"msg": "Invalid Request"}), 400
 
    check_task = mongo.db.users_tasks.count({
        "task_id" : task_id 
    })
    if check_task > 0 :
        return jsonify({"msg": "task already assigned to someone "}), 500

    id = mongo.db.users_tasks.insert_one({
       "user_id": user_id,
       "due" : due,
       "task_id" : task_id ,
       "status"  : status
    }).inserted_id
    return jsonify(str(id))


#tasks assign by admin
@bp.route('/assign_tasksbyadmin', methods=['POST'])
@admin_required
def assign_tasks():
    user_id = request.json.get("user_id", None)
    due = request.json.get("due", None)
    task_id = request.json.get("task_id" , None)
    status = request.json.get("status" , None)
    is_user = mongo.db.Users.find_one({"_id":user_id})

    if due is not None:
        due = datetime.datetime.strptime(due, "%d-%m-%Y")
    else:
        due = datetime.datetime.now()


    if not user_id or not task_id :
        return jsonify({"msg": "Invalid Request"}), 400
 
    check_task = mongo.db.users_tasks.count({
        "task_id" : task_id 
    })
    check_date = mongo.db.users_tasks.find_one({"task_id":task_id})
    due_date = check_date["due"]
    day1 = datetime.datetime.now()

    if check_task>0 and day1>due_date :
        del_task= mongo.db.users_tasks.remove({"_id":user_id})
        return jsonify("deadline pass task deleted -" , del_task)
    
    if check_task > 0 :
        return jsonify({"msg": "task already assigned to someone "}), 500

    id = mongo.db.users_tasks.insert_one({
       "user_id": user_id,
       "due" : due,
       "task_id" : task_id ,
       "status"  : status
    }).inserted_id
    return jsonify(str(id))

@bp.route("/add_tasks", methods=['POST'])
@manager_required
def add_Bulktasks():
    ret =[]; 
    tasks = request.json.get("tasks")
    for i in tasks : 
        ret.append(i)
    set = mongo.db.tasks.insert(ret)
    return jsonify(str(set))

#tasks update by manager
@bp.route("/task_Updatebymanager/<string:id>", methods=['PUT'])
@manager_required
def manager_Taskupdate(id):

    if not request.json:
        abort(500)

    task = request.json.get("task", None)
    description = request.json.get("description", None)
    
    update_json = {}
    if task is not None:
        update_json["task"] = task

    if description is not None:
        update_json["description"] = description
    
    ret = mongo.db.tasks.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))


#tasks update by admin
@bp.route("/task_updatebyadmin/<string:id>", methods=['PUT'])
@admin_required
def task_updateAdmin(id):

    if not request.json:
        abort(500)

    task = request.json.get("task", None)
    description = request.json.get("description", None)
    
    update_json = {}
    if task is not None:
        update_json["task"] = task

    if description is not None:
        update_json["description"] = description
    
    
    # match with Object ID
    ret = mongo.db.tasks.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))



#assigned tasks update by manager
@bp.route("/assigned_updatebymanager/<string:id>", methods=['PUT'])
@manager_required
def assigned_update(id):
    if not request.json:
        abort(500)
    user_id = request.json.get("user_id", None)
    due = request.json.get("due", None)
    task_id = request.json.get("task_id" , None)

    if user_id is None or  task_id is None :
        return jsonify(message="Invalid put Request"), 500
    is_user = mongo.db.Users.find_one({"_id":user_id})
    if is_user["role"] == "admin":
        return jsonify("manager can't assign or change admin's task")
    update_json = {}

    if user_id is not None:
        update_json["user_id"] = user_id
    
    if due is not None:
        update_json["due"] = due
    
    if task_id is not None:
        update_json["task_id"] = task_id
    
    ret = mongo.db.users_tasks.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))


#assigned tasks update by admin
@bp.route("/assigned_update/<string:id>", methods=['PUT'])
@admin_required
def assigned_Upbyadmin(id):
    if not request.json:
        abort(500)
    user_id = request.json.get("user_id", None)
    due = request.json.get("due", None)
    task_id = request.json.get("task_id" , None)

    if user_id is None or  task_id is None :
        return jsonify(message="Invalid put Request"), 500
    
    update_json = {}

    if user_id is not None:
        update_json["user_id"] = user_id
    
    if due is not None:
        update_json["due"] = due
    
    if task_id is not None:
        update_json["task_id"] = task_id
    
    ret = mongo.db.users_tasks.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))


@bp.route("/status_update/<string:id>", methods=['PUT'])
@jwt_required
def userStatus_update(id):

    if not request.json:
        abort(500)

    status = request.json.get("status", None)
    
    update_json = {}

    if status is not None:
        update_json["status"] = status
    
    # match with Object ID
    ret = mongo.db.users_tasks.update({
        "_id": ObjectId(id)
    }, {
        "$set": update_json
    }, upsert=False)
    return jsonify(str(ret))


@bp.route("/get_task", methods=["GET"])
@jwt_required
def userGet_task():

    user_id = request.json.get("user_id", None)
    q = mongo.db.users_tasks.find({
        "user_id" : user_id
    })  
    tasks = [serialize_doc(doc) for doc in q]
    return jsonify(tasks) 

@bp.route("/task_info/<string:id>", methods=["GET"])
@jwt_required
def task_info(id):
    q = mongo.db.tasks.find({
        "_id" : ObjectId(id)
    })  
    tasks = [serialize_doc(doc) for doc in q]
    return jsonify(tasks) 

@bp.route("/del_assign-tasks", methods=["DELETE"])
@manager_required
def del_Assigntasks():

    ret =[]; 
    ret= request.json.get("assign_task")
    
    for i in ret :
    
      set = mongo.db.users_tasks.remove({

        "_id" : ObjectId(i)
    })

@bp.route("/del_assignedByadmin", methods=["DELETE"])
@admin_required
def del_Assignbyadmin():

    ret =[]; 
    ret= request.json.get("assign_task")
    
    for i in ret :
    
      set = mongo.db.users_tasks.remove({

        "_id" : ObjectId(i)
    })

    return jsonify(str(set))

@bp.route('/del_tasks', methods=['DELETE'])
@manager_required
def del_Bulktasks():
    ret =[]; 
    ret= request.json.get("task")
    
    for i in ret :
    
      set = mongo.db.tasks.remove({

        "_id" : ObjectId(i)
    })
    

    return jsonify(str(set))