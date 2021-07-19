from flask_pymongo import PyMongo


def init_db():
    mongo = PyMongo()
    return mongo


def get_db(app, mongo):
    app.config["MONGO_URI"] = "mongodb+srv://1111111111:1111111111@cluster0.tzzym.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    mongo.init_app(app)