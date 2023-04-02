
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,  session
import psycopg2
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'cs4111'

#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.73.36.248/project1
#
# For example, if you had username zy2431 and password 123123, then the following line would be:
#
#     DATABASEURI = "postgresql://zy2431:123123@34.73.36.248/project1"
#
# Modify these with your own credentials you received from TA!
DATABASE_USERNAME = "w.jiahao"
DATABASE_PASSWRD = "6670"
DATABASE_HOST = "34.148.107.47" # change to 34.28.53.86 if you used database 2 for part 2
DATABASEURI = f"postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWRD}@{DATABASE_HOST}/project1"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI,future=True)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
'''with engine.connect() as conn:
	#create_table_command = """
	#CREATE TABLE IF NOT EXISTS test (
	#	id serial,
	#	name text
	#)
	#"""
	#res = conn.execute(text(create_table_command))
	#insert_table_command = """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace')"""
	#res = conn.execute(text(insert_table_command))
	# you need to commit for create, insert, update queries to reflect
	conn.commit()
	'''


@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
	(every time you enter an address in the web browser).
	We use it to setup a database connection that can be used throughout the request.

	The variable g is globally accessible.
	"""
	try:
		g.conn = engine.connect()
	except:
		print("uh oh, problem connecting to database")
		import traceback; traceback.print_exc()
		g.conn = None

@app.teardown_request
def teardown_request(exception):
	"""
	At the end of the web request, this makes sure to close the database connection.
	If you don't, the database could run out of memory!
	"""
	try:
		g.conn.close()
	except Exception as e:
		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/1.1.x/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
'''
	request.method:   "GET" or "POST"
	request.form:     if the browser submitted a form, this contains the data in the form
	request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2
'''
#default login page
@app.route('/')
def login():
    return render_template('login.html')

#register page
@app.route('/regist')
def regist():
    return render_template('register.html')

#test redirect
@app.route('/another')
def another():
	return render_template("another.html")

@app.route('/login', methods=['GET', 'POST'])
def getLoginRequest():
	if request.method == 'POST':
		user_id = request.form['userid']
		password = request.form['password']
		if user_id and password:
			# sql
			sql_select = "SELECT user_id, password FROM p_user WHERE user_id=:user_id AND password=:password;"
			cursor = g.conn.execute(text(sql_select).bindparams(user_id=user_id, password=password))
			results = cursor.fetchall()
			cursor.close()
			if len(results) == 1:
				sql_select_job_seeker = "SELECT user_id FROM job_seeker WHERE user_id=:user_id;"
				cursor = g.conn.execute(text(sql_select_job_seeker).bindparams(user_id=user_id))
				results_job_seeker = cursor.fetchall()
				cursor.close()
				sql_select_employer = "SELECT user_id FROM employer WHERE user_id=:user_id;"
				cursor = g.conn.execute(text(sql_select_employer).bindparams(user_id=user_id))
				results_employer = cursor.fetchall()
				cursor.close()
				if len(results_job_seeker) == 1:
					user_type = 'job_seeker'
				elif len(results_employer) == 1:
					user_type = 'employer'
				session['user_id'] = user_id
				session['user_type'] = user_type
				
				return redirect('/another')
			else:
				return 'Wrong user_id or password'
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		user_id = request.form.get('user_id')
		password = request.form.get('password')
		email = request.form.get('email')
		first_name = request.form.get('first_name')
		last_name = request.form.get('last_name')
		street = request.form.get('street')
		apt_number = request.form.get('apt_number')
		city = request.form.get('city')
		state = request.form.get('state')
		zip = request.form.get('zip')
		phone_number = request.form.get('phone_number')
		date_of_birth = request.form.get('date_of_birth')
		age = request.form.get('age')
		user_type = request.form.get('user_type')
		register_date = request.form.get('register_date')

	# Validate input fields
	if not all([user_id, password, email, first_name, last_name, street, city, state, zip, phone_number, date_of_birth, age, user_type]):
		return "Please Fill All Information"

	# Check if the user_id already exists
	check_user_id = text("SELECT user_id FROM p_user WHERE user_id = :user_id")
	user_id_exists = g.conn.execute(check_user_id.bindparams(user_id=user_id)).fetchone()

	if user_id_exists:
		return "User_id already exist, please change."

	# Save common user information to the 'p_user' table
	insert_p_user =insert_p_user = text("INSERT INTO p_user (user_id, password, email, first_name, last_name, street, apt_number, city, state, zip, phone_number, date_of_birth, age, register_date) VALUES (:user_id, :password, :email, :first_name, :last_name, :street, :apt_number, :city, :state, :zip, :phone_number, :date_of_birth, :age, :register_date)")
	g.conn.execute(insert_p_user.bindparams(user_id=user_id, password=password, email=email, first_name=first_name, last_name=last_name, street=street, apt_number=apt_number, city=city, state=state, zip=zip, phone_number=phone_number, date_of_birth=date_of_birth, age=age, register_date=register_date))
	if user_type == 'employee':
		# Save employee-specific information to the 'employees' table
		# Add your employee-specific fields here and adjust the INSERT statement accordingly
		skills = request.form.get('skills')
		targeted_position = request.form.get('targeted_position')
		expected_salary = request.form.get('expected_salary')
		intern = request.form.get('intern')
		resume = request.form.get('resume')
		if not all([skills, targeted_position, expected_salary, intern, resume]):
			return "Please Fill All Information"
		insert_employee = text("INSERT INTO job_seeker (user_id, skills, targeted_position, expected_salary, looking_for_intern, resume) VALUES (:user_id, :skills, :targeted_position, :expected_salary, :intern, :resume);")
		g.conn.execute(insert_employee.bindparams(user_id=user_id, skills=skills, expected_salary=expected_salary, targeted_position=targeted_position, intern=intern, resume=resume))

	elif user_type == 'employer':
		# Save employer-specific information to the 'employers' table
		# Add your employer-specific fields here and adjust the INSERT statement accordingly
		title = request.form.get('title')
		company_name = request.form.get('company_name')
		industry = request.form.get('industry')
		average_salary = request.form.get('average_salary')
		website = request.form.get('website')
		if not all([title, company_name, industry, average_salary, website]):
			return "Please Fill All Information"
		
		insert_employer = text("INSERT INTO employer (user_id, title, company_name, industry, average_salary, website) VALUES (:user_id, :title, :company_name, :industry, :average_salary, :website);")
		g.conn.execute(insert_employer.bindparams(user_id=user_id, title=title, company_name=company_name, industry=industry, average_salary=average_salary, website=website))

	# Redirect to the login page after successful registration
	g.conn.commit()
	return redirect('/login')

@app.route('/blog')
def blog():
    # Get user id from session
    user_id = session['user_id']
    
    # Get recommended blogs based on user interests
    recommended_blogs = []
    if user_id:
        sql_select = text('''
            SELECT b.* 
            FROM blog b, follow f, blog_posts p
            where b.blog_id=p.blog_id
	    	and f.user_id=p.user_id
            and f.follower_id=:user_id;
        ''')
        cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
        recommended_blogs = cursor.fetchall()
        cursor.close()

    # Get user's liked blogs
    liked_blogs = []
    if user_id:
        sql_select = text('''
            SELECT b.*
            FROM blog b,likes l
            WHERE b.blog_id=l.blog_id
			and l.user_id = :user_id;
        ''')
        cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
        liked_blogs = cursor.fetchall()
        cursor.close()

    # Render the blog page
    return render_template('blog.html', recommended_blogs=recommended_blogs, liked_blogs=liked_blogs)


if __name__ == "__main__":
	import click
	app.debug = True
	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='127.0.0.1')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
		"""
		This function handles command line parameters.
		Run the server using:

			python server.py

		Show the help text using:

			python server.py --help

		"""

		HOST, PORT = host, port
		print("running on %s:%d" % (HOST, PORT))
		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

run()
