from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import json
from datetime import datetime
from flask_mail import Mail
import os
local_server = True
with open('config.json','r') as f:
    params = json.load(f)["params"]    
                                    
app = Flask(__name__)                
app.secret_key = 'super-secret-key'   
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
db = SQLAlchemy(app)           

class Contact(db.Model):                                  
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(20), primary_key= True, unique=True, nullable=False)
    phoneno = db.Column(db.String(10), unique=True, nullable=False)
    mssg = db.Column(db.String(120), unique=False, nullable=False)

class Posts(db.Model):     
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
    if ('user' in session and session['user'] == params['admin_user']): 
        return render_template('dashboard.html', params = params, posts=posts)

    if request.method=='POST':      
        email = request.form.get('email')            
        password = request.form.get('password')      
        if (email == params['admin_user'] and password==params['admin_password']): 
            session['user'] = email          
            return render_template('dashboard.html', params = params, posts=posts)
        else:
            return render_template('newpage.html', params = params, posts = posts)
    return render_template('dashboard.html', params=params, posts = posts)

@app.route("/logout") 
def logout():          
    session.pop('user')
    return redirect('/dashboard')


@app.route("/contact/", methods = ['GET', 'POST'])     
def contact():
        if(request.method=='POST'):      
            name = request.form.get('name')          
            email = request.form.get('email')         

            phone = request.form.get('phone')        
            message = request.form.get('message')    

            entry = Contact(name=name, email=email, phoneno=phone, mssg=message)    
            db.session.add(entry)        
            db.session.commit()          
            mail.send_message('New message from Blog', sender=email, recepients=[params['gmail_user']],
                              body = message + "\n" + phone
                              )   
        return render_template("contact.html", params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])      
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

        if sno=='0':   
            post = Posts(title=title, slug = slug, content = content, date = date)  
            db.session.add(post)    
            db.session.commit()    
        else:              
            post = Posts.query.filter_by(sno=sno).first()
            post.title = title   
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
