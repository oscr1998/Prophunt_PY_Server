from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug import exceptions

#* Auth & Auth
from flask_login import LoginManager
from .models.user import User

#* Router
from .routes.auth import auth as auth_route

#* Database
from dotenv import load_dotenv
from os import environ
from .database.db import db

#* Email
from flask_mail import Mail
mail = Mail()

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY = environ.get('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI = environ.get('DATABASE_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS = environ.get('SQLALCHEMY_TRACK_MODIFICATIONS'),
        MAIL_SERVER = environ.get('MAIL_SERVER'),
        MAIL_PORT = environ.get('MAIL_PORT'),
        MAIL_USERNAME = environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD = environ.get('MAIL_PASSWORD'),
        MAIL_USE_TLS = True,
        MAIL_USE_SSL = False
    )
        
    CORS(app)
    with app.app_context():
        db.app = app
        db.init_app(app)
        
    @app.route("/")
    def API():
        return "<h1>Welcome to the Revelio API</h1>"
    
    @app.route("/leaderboard/<sort_by>/<int:limit>")
    def leaderboard(sort_by,limit):
        try:
            match sort_by:
                case "wins":
                    item = User.wins
                case "wins_as_hunter":
                    item = User.wins_as_hunter
                case "wins_as_hider":
                    item = User.wins - User.wins_as_hunter
                case "games_played":
                    item = User.games_played
                case _:
                    item = User.username
            res = map(lambda u: { 
                "username": u.username,
                "games_played": u.games_played, 
                "wins": u.wins,
                "wins_as_hunter": u.wins_as_hunter,
                "wins_as_hider": u.wins - u.wins_as_hunter
                }, User.query.order_by(item.desc()).limit(limit))
            output = list(res)
            return jsonify(output)
        except:
            raise exceptions.BadRequest()
    
    #* Route
    app.register_blueprint(auth_route)
    
    #* Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    #* Email
    mail.init_app(app)
    
    #* Error Handlers
    @app.errorhandler(exceptions.BadRequest)
    def handle_400(err):
        return jsonify({"message": f"{err.description}"}), 400
    @app.errorhandler(exceptions.NotFound)
    def handle_404(err):
        return jsonify({"message": f"Fallout 4, I think you are lost."}), 404
    @app.errorhandler(exceptions.InternalServerError)
    def handle_500(err):
        return jsonify({"message": f"Oops, that probably is our fault."}), 500
    @app.errorhandler(exceptions.MethodNotAllowed)
    def handle_405(err):
        return jsonify({"message": f"Naughty method is not allowed"}), 405
    @app.errorhandler(exceptions.Conflict)
    def handle_409(err):
        return jsonify({"message": f"{err.description}"}), 409
    
    return app
