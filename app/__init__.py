import os

from flask import Flask, make_response, jsonify

from flask_cors import CORS

from app import db

mongo = db.init_db()

from app import token

jwt = token.init_token()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping()

    CORS(app)

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.errorhandler(400)
    def not_found(error):
        return make_response(jsonify(error='Not found'), 400)

    @app.errorhandler(500)
    def error_500(error):
        return make_response({}, 500)

    db.get_db(mongo=mongo, app=app)
    token.get_token(jwt=jwt, app=app)

    from app.api import users
    app.register_blueprint(users.bp)

    from app.api import tasks
    app.register_blueprint(tasks.bp)


    return app
    