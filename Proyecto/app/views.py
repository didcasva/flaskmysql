from flask import render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField,TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from data import Articles
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask,jsonify,send_from_directory
from marshmallow import Schema, fields
from datetime import date
from app import app


Articles = Articles()

app.secret_key='secrect123'

# Config MySQL

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] ='Autonoma123*'

app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


mysql = MySQL(app)

class RegisterForm(Form):

	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Password do not match')
		])
	confirm = PasswordField('Confirm Password')

@app.route('/')
def index():
        return render_template("index.html")

@app.route('/about')
def about():
        return render_template("about.html")

@app.route('/articles')
def articles():
        return render_template("articles.html",articles = Articles)

@app.route('/article/<string:id>')
def article(id):
        return render_template("article.html",id=id)

@app.route('/register', methods=['GET','POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create Cursor
		cur = mysql.connection.cursor()

		# Execute Query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username,password))
        # Commit to DB

		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('You are now registered and can log in','success')

		return redirect(url_for('index'))

	return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']
		
		# Create cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username =%s",[username])

		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):

				# Passed
				session['logged_in'] = True
				session['username'] = username
				flash('You are logged in', 'success')
				app.logger.info('PASSWORD MATCHED')
				return redirect(url_for('dashboard'))

		else:

				app.logger.info('PASSWORD NO MATCHED')
				error = 'Invalid login'
				return render_template('login.html', error=error)

			# Close connection
		cur.close()

	else:

			app.logger.info('NO USER')
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')







def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)

		else:

			flash('Unauthorized, Plese login','danger')
			return redirect(url_for('login'))
	return wrap




# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	return render_template('dashboard.html')

# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))


spec = APISpec(
    title='Flask-api-swagger-doc',
    version='1.0.0.',
    openapi_version='3.0.2',
    plugins=[FlaskPlugin(),MarshmallowPlugin()]
)

@app.route('/api/swagger.json')
def create_swagger_spec():
        return jsonify(spec.to_dict())

class ArticleResponseSchema(Schema):
        id = fields.Int()
        title = fields.Str()
        body = fields.Str()
        author = fields.Str()
        create_date = fields.Date()

class ArticleListResponseSchema(Schema):
        article_list = fields.List(fields.Nested(ArticleResponseSchema))

@app.route('/api/articles')
def articleAPI():
    """Get List of Articles
        ---
        get:
            description: Get List of Articles
            responses:
                200:
                    description: Return an article list
                    content:
                        application/json:
                            schema: ArticleListResponseSchema
    """

    articles = [{
            'id': 1,
            'title': 'Article one',
            'body': 'Lorem ipsum',
            'author': 'Gabo',
            'create_date': date(2021,10,4)
        },

{
            'id': 2,
            'title': 'Article two',
            'body': 'Lorem ipsum',
            'author': 'Perez',
            'create_date': date(2021,10,12)
        }
    ]

    return ArticleListResponseSchema().dump({'article_list':articles})

with app.test_request_context():
    spec.path(view=articleAPI)
@app.route('/docs')
@app.route('/docs/<path:path>')
def swagger_docs(path=None):
    if not path or path == 'docs.html':
        return render_template('docs.html',base_url='/docs')
    else:
        return send_from_directory('static',path)
