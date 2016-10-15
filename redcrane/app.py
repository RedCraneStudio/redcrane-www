from flask import Flask, Blueprint, render_template
from flask.ext.script import Manager, Server
from flask.ext.mongoengine import MongoEngine
from flask.ext.cache import Cache
from flask.ext.login import LoginManager

# The website requires a secret key! 
# Please place this key in a "secret.key" file in the root folder.
with open('secret.key', 'r') as SECRET_KEY:
	SECRET_KEY = SECRET_KEY.read()

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
	'db':'redcrane'
}
app.config['SECRET_KEY'] = SECRET_KEY

# Database

db = MongoEngine(app)

import models

# Caching

cache = Cache(app, config = {'CACHE_TYPE':'simple'})
cache.init_app(app)

# Routing

import routes
app.register_blueprint(routes.url)

# Login

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return models.User.objects(id=user_id)

# Manager

manager = Manager(app)

manager.add_command('debug', Server(
	use_debugger = True, use_reloader = True,
	host = '127.0.0.1', port = 5000 ))
manager.add_command('prod', Server(
		use_debugger = False, use_reloader = False,
		host = '0.0.0.0', port = 5000 ))

# Error Handlers

@app.errorhandler(404)
def page_not_found(error): 
    return render_template('error.html', error=error), 404

@app.errorhandler(401)
def unauthorized(error):
    return render_template('error.html', error=error), 401

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error=error), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return render_template('error.html', error=error), 405

if __name__ == '__main__':
	manager.run()
