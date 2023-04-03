
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
from datetime import datetime
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response,  session
import psycopg2
from uuid import uuid4
from collections import defaultdict
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
	
	#Get user's own blogs
	my_blogs = []
	if user_id:
		sql_select = text("SELECT b.* FROM blog b, blog_posts p WHERE b.blog_id=p.blog_id and p.user_id = :user_id;")
		cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
		my_blogs=cursor.fetchall()
		cursor.close()
    	
    	

    # Render the blog page
	return render_template('blog.html', recommended_blogs=recommended_blogs, liked_blogs=liked_blogs, my_blogs=my_blogs)


@app.route('/blog/like', methods=['POST'])
def like_blog():
    user_id = session['user_id']
    blog_id = request.form.get('blog_id')
    
    if not all([user_id, blog_id]):
        return "Error"
    sql_check = text("SELECT COUNT(*) FROM likes WHERE blog_id = :blog_id AND user_id = :user_id;")
    result = g.conn.execute(sql_check.bindparams(blog_id=blog_id, user_id=user_id)).scalar()
    
    if result > 0:
        return "You have already liked this blog."    
    liked_time = datetime.utcnow()
    sql_insert = text("INSERT INTO likes (blog_id, user_id, liked_time) VALUES (:blog_id, :user_id, :liked_time);")
    g.conn.execute(sql_insert.bindparams(blog_id=blog_id, user_id=user_id, liked_time=liked_time))
    g.conn.commit()
    
    return redirect('/blog')

@app.route('/blog/search', methods=['GET'])
def search_blog():
    keyword = request.args.get('keyword').lower()
    
    if not keyword:
        return "Please enter a keyword."
    
    # Perform search
    sql_search = text("SELECT * FROM blog WHERE LOWER(title) LIKE '%' || :keyword || '%' OR LOWER(content) LIKE '%' || :keyword || '%' OR lOWER(keywords) LIKE '%' || :keyword || '%' OR LOWER(author_name) LIKE '%' || :keyword || '%';")
    search_results = g.conn.execute(sql_search.bindparams(keyword=f"%{keyword}%")).fetchall()
    
    # Render search results in a new template
    return render_template("search_blog_results.html", search_results=search_results)




	
@app.route('/blog_post', methods=['GET', 'POST'])
def blog_post():
    if request.method == 'POST':
        title = request.form.get('title')
        keywords = request.form.get('keywords')
        author_name = request.form.get('author_name')
        content = request.form.get('content')

        # Generate a unique blog_id
        blog_id = generate_blog_id()

        # Insert blog into the blog table
        sql_insert_blog = text("INSERT INTO blog (blog_id, title, author_name, keywords, content) VALUES (:blog_id, :title, :author_name, :keywords, :content);")
        g.conn.execute(sql_insert_blog.bindparams(blog_id=blog_id, title=title, author_name=author_name, keywords=keywords, content=content))

        # Insert blog_post into the blog_post table
        user_id = session['user_id']
        post_time = datetime.utcnow()
        sql_insert_blog_post = text("INSERT INTO blog_posts (blog_id, user_id, blog_posted_date) VALUES (:blog_id, :user_id, :post_time);")
        g.conn.execute(sql_insert_blog_post.bindparams(blog_id=blog_id, user_id=user_id, post_time=post_time))

        # Commit the changes to the database
        g.conn.commit()

        # Redirect the user to the blog page
        return redirect('/blog')


@app.route('/people')
def people():
    # Get the user's id
    user_id = session['user_id']

    # Get suggested users
    suggested_users = []
    sql_suggested_users = text("""
        SELECT distinct(u.*) 
		FROM p_user u left join follow f on u.user_id=f.user_id 
		Where f.follower_id in (
			SELECT user_id
			FROM follow 
			Where follower_id = :user_id
			)
		And u.user_id != :user_id
		Union
		SELECT distinct(u.*) 
		FROM p_user u left join follow f on u.user_id=f.follower_id 
		Where f.user_id in(
			SELECT user_id 
			FROM follow 
			Where follower_id = :user_id
			)
		And u.user_id != :user_id
		;

    """)
    result = g.conn.execute(sql_suggested_users.bindparams(user_id=user_id))
    for row in result:
        suggested_users.append(row)
    result.close()
    
	
    # Get followed users
    followed_users = []
    sql_followed_users = text("""
        SELECT *
        FROM p_user
        WHERE user_id IN (
            SELECT user_id
            FROM follow
            WHERE follower_id = :user_id
        );
    """)
    result = g.conn.execute(sql_followed_users.bindparams(user_id=user_id))
    for row in result:
        followed_users.append(row)
    result.close()

    return render_template('people.html', suggested_users=suggested_users,followed_users=followed_users)

@app.route('/people/follow', methods=['POST'])
def follow_people():
    user_id = session['user_id']
    followee_id = request.form.get('user_id')
    
    if not all([user_id, followee_id]):
        return "Error"
    sql_check = text("SELECT COUNT(*) FROM follow WHERE user_id = :followee_id AND follower_id = :user_id;")
    result = g.conn.execute(sql_check.bindparams(followee_id=followee_id, user_id=user_id)).scalar()
    
    if result > 0:
        return "You have already followed this user."    
    liked_time = datetime.utcnow()
    sql_insert = text("INSERT INTO follow (user_id, follower_id, followed_time) VALUES (:followee_id, :user_id, :liked_time);")
    g.conn.execute(sql_insert.bindparams(followee_id=followee_id, user_id=user_id, liked_time=liked_time))
    g.conn.commit()
    return redirect('/people')


@app.route('/people/search', methods=['GET'])
def search_people():
    keyword = request.args.get('keyword').lower()
    
    if not keyword:
        return "Please enter a keyword."
    
    # Perform search
    sql_search = text('''SELECT u.* 
		FROM p_user u left join job_seeker j on u.user_id=j.user_id
			left join employer e on u.user_id=e.user_id
		WHERE LOWER(u.first_name) LIKE '%' || :keyword || '%' OR LOWER(u.last_name) LIKE '%' || :keyword || '%' 
		OR lOWER(j.skills) LIKE '%' || :keyword || '%'
		OR LOWER(e.company_name) LIKE '%' || :keyword || '%'
		OR LOWER(e.Industry) LIKE '%' || :keyword || '%'
		OR u.user_id LIKE '%' || :keyword || '%'
		;
		''')
    search_results = g.conn.execute(sql_search.bindparams(keyword=keyword)).fetchall()
    
    # Render search results in a new template
    return render_template("search_people_results.html", search_results=search_results)

@app.route('/job_seeker_profile')
def job_seeker_profile():
	if session['user_type'] == 'job_seeker':
		user_id = session['user_id']

		# sql experience
		sql_experience=text(
		"SELECT * FROM EXPERIENCE WHERE USER_ID = :user_id;"
		)
		experiences = g.conn.execute(sql_experience.bindparams(user_id=user_id)).fetchall()

		# sql education
		sql_education=text(
		"SELECT * FROM EDUCATION WHERE USER_ID = :user_id;"
		)
		educations = g.conn.execute(sql_education.bindparams(user_id=user_id)).fetchall()

		return render_template('job_seeker_profile.html', experiences=experiences, educations=educations)
	else:
		return "Access denied. You must be a job seeker to view this page.", 403
    
# add experience
@app.route('/add_experience', methods=['POST'])
def add_experience():
	# get experience from form
	print(request.form)
	user_id = session['user_id']
	experience_id = generate_experience_id(user_id)
	date_of_start = request.form['date_of_start']
	date_of_end = request.form['date_of_end']
	months = request.form['months']
	company_name = request.form['company_name']
	city = request.form['city']
	state = request.form['state']
	job_title = request.form['job_title']
	main_skills = request.form['main_skills']
	description = request.form['description']


	# sql insert
	sql_insert ="INSERT INTO EXPERIENCE (USER_ID, EXPERIENCE_ID, DATE_OF_START,date_of_end ,months, company_name, city,state , job_title,main_skills ,description) VALUES (:user_id, :experience_id, :date_of_start, :date_of_end ,:months, :company_name, :city, :state , :job_title, :main_skills ,:description);"
	g.conn.execute(text(sql_insert).bindparams(user_id=user_id, experience_id=experience_id, date_of_start=date_of_start 
			,date_of_end=date_of_end, months=months, company_name=company_name, city=city, state=state, job_title=job_title
			, main_skills=main_skills, description=description))
	g.conn.commit()

	return redirect('/job_seeker_profile')

# add education
@app.route('/add_education', methods=['POST'])
def add_education():
    # get education from form
    user_id = session['user_id']
    education_id = generate_education_id(user_id)
    date_of_start = request.form['date_of_start']
    date_of_end = request.form['date_of_end']
    degree = request.form['degree']
    major = request.form['major']
    city = request.form['city']
    university = request.form['university']
    country = request.form['country']

    

    # sql insert
    sql_insert ="INSERT INTO education (USER_ID, education_id, DATE_OF_START,date_of_end ,degree, major, university, city, country) VALUES (:user_id, :education_id, :date_of_start, :date_of_end ,:degree, :major, :university, :city, :country);"

    g.conn.execute(text(sql_insert).bindparams(user_id=user_id, education_id=education_id, date_of_start=date_of_start 
		   ,date_of_end=date_of_end, degree=degree, major=major, city=city, country=country, university=university))
    g.conn.commit()

    return redirect('/job_seeker_profile')

@app.route('/job')
def job():
	# Get user id from session
	user_id = session['user_id']

	#get major skills
	if user_id:
		sql_select = text('''
			select skills
			from job_seeker
			where user_id= :user_id;
		'''
		)
		cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
		major_skills = cursor.fetchone()[0]
		cursor.close()
	#preprocess the skills
	skills=major_skills.lower().strip().split()
	#get targeted position
	if user_id:
		sql_select = text('''
		select targeted_position
		from job_seeker
		where user_id= :user_id;
		'''
		)
		cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
		targeted_position = cursor.fetchone()[0]
		cursor.close()



	# Get recommended jobs based on user skills and experiences
	recommended_jobs = []
	if user_id:
		sql_select = "SELECT j.* FROM job j, applies a where j.job_id=a.job_id And j.job_id not in (select job_id from applies where user_id = :user_id) And ("
		for skill in skills:
			sql_select += f"LOWER(required_skills) LIKE '%{skill}%' OR LOWER(JOB_DESCRIPTION) LIKE '%{skill}%' OR "
		sql_select += "LOWER(job_title) LIKE '%' || :targeted_position || '%');"
		cursor = g.conn.execute(text(sql_select).bindparams(targeted_position=targeted_position, user_id=user_id))
		recommended_jobs = cursor.fetchall()
		cursor.close()

	# Get user's applied jobs
	applied_jobs = []
	if user_id:
		sql_select = text('''
			SELECT j.*, a.cover_letter
			FROM job j, applies a
			WHERE j.job_id=a.job_id AND a.user_id=:user_id;
		''')
		cursor = g.conn.execute(sql_select.bindparams(user_id=user_id))
		applied_jobs = cursor.fetchall()
		cursor.close()

	# Render the job page
	return render_template('job.html', recommended_jobs=recommended_jobs, applied_jobs=applied_jobs)

@app.route('/job/apply', methods=['POST'])
def apply_job():
    user_id = session['user_id']
    job_id = request.form.get('job_id')
    cover_letter=request.form.get('cover_letter')
    if not all([user_id, job_id, cover_letter]):
        return "Error"
    sql_check = text("SELECT COUNT(*) FROM applies WHERE job_id = :job_id AND user_id = :user_id;")
    result = g.conn.execute(sql_check.bindparams(job_id=job_id, user_id=user_id)).scalar()
    
    if result > 0:
        return "You have already applied this job."    
    applied_date = datetime.utcnow()
    sql_insert = text("INSERT INTO applies (user_id, job_id, applied_date, cover_letter) VALUES (:user_id, :job_id, :applied_date, :cover_letter);")
    g.conn.execute(sql_insert.bindparams(job_id=job_id, user_id=user_id, applied_date=applied_date, cover_letter=cover_letter))
    g.conn.commit()
    return redirect('/job')

@app.route('/job/search', methods=['GET'])
def search_job():
	keyword = request.args.get('keyword').lower()

	if not keyword:
		return "Please enter a keyword."

	# Perform search
	sql_search = text('''SELECT * FROM job 
					WHERE LOWER(job_title) LIKE '%' || :keyword || '%'
					OR LOWER(company_name) LIKE '%' || :keyword || '%'
					OR lOWER(city) LIKE '%' || :keyword || '%' 
					OR lOWER(industry) LIKE '%' || :keyword || '%' 
					OR lOWER(required_skills) LIKE '%' || :keyword || '%' 
					OR lOWER(required_major) LIKE '%' || :keyword || '%'
					OR lOWER(job_description) LIKE '%' || :keyword || '%'
					;
					''')
	search_results = g.conn.execute(sql_search.bindparams(keyword=keyword)).fetchall()

	# Render search results in a new template
	print(sql_search.bindparams(keyword=keyword))
	print(search_results)
	return render_template("search_job_results.html", search_results=search_results)

@app.route('/job_post', methods=['GET', 'POST'])
def job_post():
	user_id=session['user_id']
	if request.method == 'POST':
		company_name = request.form.get('company_name')
		deadline = request.form.get('deadline')
		job_title = request.form.get('job_title')
		is_intern = request.form.get('is_intern')
		city = request.form.get('city')
		state= request.form.get('state')
		salary = request.form.get('salary')
		industry = request.form.get('industry')
		required_skills = request.form.get('required_skills')
		required_degree = request.form.get('required_degree')
		required_major = request.form.get('required_major')
		required_experiences = request.form.get('required_experiences')
		job_description = request.form.get('job_description')
		job_posted_date = datetime.utcnow()

		# Generate a unique job_id
		job_id = generate_job_id()

		# Insert blog into the blog table
		sql_insert_blog = text('''INSERT INTO job (job_id, company_name, deadline, job_title, is_intern, city, 
								state, salary, industry, required_skills, required_degree, required_major, required_experiences, job_description, 
								job_posted_date, user_id) 
								VALUES (:job_id, :company_name, :deadline, :job_title, :is_intern, :city, 
								:state, :salary, :industry, :required_skills, :required_degree, :required_major, :required_experiences, :job_description, 
								:job_posted_date, :user_id);''')
		g.conn.execute(sql_insert_blog.bindparams(job_id=job_id, company_name=company_name, deadline=deadline, job_title=job_title, 
					    		is_intern=is_intern, city=city, 
								state=state, salary=salary, industry=industry, required_skills=required_skills, required_degree=required_degree
								, required_major=required_major, required_experiences=required_experiences, job_description=job_description, 
								job_posted_date=job_posted_date, user_id=user_id))


		# Commit the changes to the database
		g.conn.commit()

		# Redirect the user to the blog page
		return redirect('/another')

@app.route('/view_applicants')
def view_applicants():
    user_id = session['user_id']
    
    # select from job and applies
    sql_select = text('''
        SELECT j.job_id, j.company_name, j.job_title, j.job_posted_date, array_agg(ja.user_id), array_agg(ja.cover_letter)
        FROM job j
        JOIN applies ja ON j.job_id = ja.job_id
        WHERE j.user_id = :user_id
        GROUP BY j.job_id, j.company_name, j.job_title, j.job_posted_date
        ORDER BY j.job_posted_date DESC;
    ''')
    job_applicants = g.conn.execute(sql_select.bindparams(user_id=user_id)).fetchall()
    
    return render_template('view_applicants.html', job_applicants=job_applicants)

@app.route('/user/<user_id>')
def user(user_id):
	#select from p_user
	sql_select=text('''
		select *
		From p_user
		where user_id= :user_id;
	''')
	user_info =  g.conn.execute(sql_select.bindparams(user_id=user_id)).fetchone()
	# select from job_seeker
	sql_select = text('''
		SELECT *
		FROM job_seeker
		WHERE user_id = :user_id;
	''')
	job_seeker = g.conn.execute(sql_select.bindparams(user_id=user_id)).fetchone()


	# select from experiences
	sql_select = text('''
		SELECT *
		FROM experience
		WHERE user_id = :user_id
		ORDER BY date_of_end DESC;
	''')
	experiences = g.conn.execute(sql_select.bindparams(user_id=user_id)).fetchall()

	# select from educations
	sql_select = text('''
		SELECT *
		FROM education
		WHERE user_id = :user_id
		ORDER BY date_of_end DESC;
	''')
	educations = g.conn.execute(sql_select.bindparams(user_id=user_id)).fetchall()

	return render_template('applicant_details.html',user_info=user_info, job_seeker=job_seeker, experiences=experiences, educations=educations)

def generate_blog_id():
    while True:
        unique_id = str(uuid4())[:4]  # Generate a unique 4-character ID
        blog_id = 'b' + unique_id

        # Check if the generated blog_id already exists in the database
        sql_check = text("SELECT COUNT(*) FROM blog WHERE blog_id = :blog_id;")
        result = g.conn.execute(sql_check.bindparams(blog_id=blog_id)).fetchone()

        # If the generated blog_id is not in the database, return it
        if result[0] == 0:
            return blog_id
	
def generate_job_id():
    while True:
        unique_id = str(uuid4())[:4]  # Generate a unique 4-character ID
        job_id = 'j' + unique_id

        # Check if the generated job_id already exists in the database
        sql_check = text("SELECT COUNT(*) FROM job WHERE job_id = :job_id;")
        result = g.conn.execute(sql_check.bindparams(job_id=job_id)).fetchone()

        # If the generated job_id is not in the database, return it
        if result[0] == 0:
            return job_id

def generate_experience_id(user_id):
	while True:
		unique_id = str(uuid4())[:4]  # Generate a unique 4-character ID
		experience_id = 'exp_' + unique_id
		

		# Check if the generated experience_id-user_id combo already exists in the database
		sql_check = text("SELECT COUNT(*) FROM experience WHERE experience_id = :experience_id And user_id = :user_id;")
		result = g.conn.execute(sql_check.bindparams(experience_id=experience_id,user_id=user_id)).fetchone()

		# If the generated experience_id is not in the database, return it
		if result[0] == 0:
			return experience_id
	
def generate_education_id(user_id):
	while True:
		unique_id = str(uuid4())[:3]  # Generate a unique 3-character ID
		education_id = 'ed' + unique_id

		

		# Check if the generated education_id already exists in the database
		sql_check = text("SELECT COUNT(*) FROM education WHERE education_id = :education_id And user_id = :user_id;")
		result = g.conn.execute(sql_check.bindparams(education_id=education_id,user_id=user_id)).fetchone()

		# If the generated education_id is not in the database, return it
		if result[0] == 0:
			return education_id
		


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
