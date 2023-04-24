from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from flask_mail import Mail
import os
local_server = True
with open('config.json','r') as f:
    params = json.load(f)["params"]     # loading of json file
                                    #                     |  passwordremoved    |  name of database that we have created
app = Flask(__name__)               #                     "                     "
app.secret_key = 'super-secret-key'      # setting secret key for session
app.config['UPLOAD_FOLDER'] = params['uploader_location']
app.config.update(
    MAIL_SEVER='smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)            # initiate SQLAlchemy

class Contact(db.Model):                                   # creating a class of which attributes are name of column in Table=contact
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), primary_key= True, unique=True, nullable=False)
    phoneno = db.Column(db.String(10), unique=True, nullable=False)
    mssg = db.Column(db.String(120), unique=False, nullable=False)

class Posts(db.Model):     # accessing from database
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    slug = db.Column(db.String(20), unique=True, nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=False)

@app.route("/")
def home():
    posts = Posts.query.filter_by().all()[0:5]
    return render_template("index.html", params = params, posts=posts)

@app.route("/about")
def about():
    return render_template("about.html", params = params)

@app.route("/dashboard/", methods = ['GET','POST'])
def dashboard():
    posts = Posts.query.all()
    if ('user' in session and session['user'] == params['admin_user']): # if user is logged in and that user is admin
        return render_template('dashboard.html', params = params, posts=posts)

    if request.method=='POST':      # if post method is made
        email = request.form.get('email')            # fetching and storing value in email
        password = request.form.get('password')      # fetching and storing value in password
        if (email == params['admin_user'] and password==params['admin_password']): # checkingentered value same as in config.json
            session['user'] = email          # creating session
            return render_template('dashboard.html', params = params, posts=posts)
        else:
            return render_template('newpage.html', params = params, posts = posts)
    return render_template('dashboard.html', params=params, posts = posts)

@app.route("/logout") # for logout there is no need of get or post so / not came after logout
def logout():          # kill session
    session.pop('user')
    return redirect('/dashboard')


@app.route("/contact/", methods = ['GET', 'POST'])     # method list is added to initialize the get and post method to fetch data
def contact():
        if(request.method=='POST'):      #add entry to database
            name = request.form.get('name')          # to fetch the value in name
            email = request.form.get('email')         # to fetch the value in email

            phone = request.form.get('phone')        # to fetch the value in phone
            message = request.form.get('message')    # to fetch the value in message

            entry = Contact(name=name, email=email, phoneno=phone, mssg=message)    # values fed into attributes of table
            db.session.add(entry)        # this will add value to table
            db.session.commit()          # to save data permanently
            mail.send_message('New message from Blog', sender=email, recepients=[params['gmail_user']],
                              body = message + "\n" + phone
                              )   # to send message- (*mssgthatistobe sent, )
        return render_template("contact.html", params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])      # accessing post by its name from database
def post_access(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params ,post=post)

@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if request.method == "POST":    # fetching and storing value from form
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        date = datetime.now()

        if sno=='0':   # approach is if sno come as '0' then add post
            post = Posts(title=title, slug = slug, content = content, date = date)  # dict. is made
            db.session.add(post)    # addition
            db.session.commit()    # storing
        else:               # for editing post
            post = Posts.query.filter_by(sno=sno).first()
            post.title = title   # post.title for the title that is in post table
            post.slug = slug
            post.content = content
            post.date = date
            db.session.commit()
            return redirect('/edit/'+sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, post=post, sno=sno)

@app.route("/uploader", methods = ["GET","POST"])
def uploader():
    if (request.method=='POST'):
        f = request.files['file1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
        return "Uploaded succesfully"



@app.route("/index")
def index():
    return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)