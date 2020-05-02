from flask import Flask, request, redirect, url_for, session, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer import oauth_authorized
import os

from werkzeug.security import check_password_hash, generate_password_hash


from static import login_required
from scratch50 import main
from pytz import timezone
import pytz

from datetime import datetime
import json


date_format='%m/%d/%Y %H:%M:%S'
date = datetime.now(tz=pytz.utc)
date = date.astimezone(timezone('US/Pacific'))

print(date)
print(type(date))

engine = create_engine("postgres://xoojbkcytmkrzu:57a9d846fb86596fea1df5a39ef8d5305c20640f9b659d95a292fc0c9ae5943c@ec2-54-157-78-113.compute-1.amazonaws.com:5432/da4duicem3h7jd")
db = scoped_session(sessionmaker(bind=engine))
s = db()


ALLOWED_EXTENSIONS = {'sb3', 'sb2'}

app = Flask(__name__, static_url_path='/static')

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "SOMEDUMMYVALUE"
UPLOAD_FOLDER = "static"
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':

    username = str(request.form.get('username'))
    email = request.form.get('email')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    result = s.execute("SELECT * FROM users WHERE email = :email LIMIT 1", {'email': str(email)})
    listT = []
    for row in result:
        row_as_dict = dict(row)
        listT.append(row_as_dict)
        
    if len(listT) != 0:
      flash("Already registered")
      return redirect('/register')
  
    if password != confirm:
      flash('Please double check your password', 'danger')
      
    s.execute('INSERT INTO users (username, password, email, status) VALUES (:username, :password, :email, :status)',  {'username': username, 'password': generate_password_hash(password), 'email': str(email), "status": "student"})
    s.commit()
    
    return redirect("/")

  else:
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  
  if request.method == 'POST':
    username = request.form.get('username')
    
    result = s.execute("SELECT * FROM users WHERE username = :username LIMIT 1", {'username': str(username)})
    listT = []
    for row in result:
        row_as_dict = dict(row)
        listT.append(row_as_dict)
  
    try:
      if listT[0]["password"] == 'Google':
        return redirect('/google')
    
      if check_password_hash(listT[0]['password'], request.form.get("password")):
          session['user_id'] = listT[0]['user_id']
          return redirect("/")

    except IndexError:
      flash('Wrong username', category='danger')
      return redirect('/login')

    flash('Wrong password', category='danger')
    return redirect('/login')
    
  else:
    return render_template('register.html')


@app.route('/assignment/0', methods=['GET', 'POST'])
@login_required
def assignment0():

  if not session.get("user_id"):
    return redirect("/github")
  
  
  if request.method == "POST":
    
    file = request.files["file"]
    
    if file and allowed_file(file.filename):
      s.execute("INSERT INTO assignments (user_id, assignment_id, score, assignment_name) VALUES (:user_id, :assignment_id, :score, :assignment_name)", {"user_id": session.get("user_id"), "assignment_id": 0, "score": 100, "assignment_name": "Scratch 0"})
      tests = {"Scratch file is valid": True}
      
    else:
      s.execute("INSERT INTO assignments (user_id, assignment_id, score, assignment_name) VALUES (:user_id, :assignment_id, :score, :assignment_name)", {"user_id": session.get("user_id"), "assignment_id": 0, "score": 0, "assignment_name": "Scratch 0"})
      tests = {"Scratch file is valid": False}
  
    return render_template("test.html", tests=tests, score=score)

  else:
  
    return render_template("assignment0.html")

  
@app.route("/assignment/1", methods=["GET", "POST"])
@login_required
def assignment1():
  if request.method == 'POST':
    
    file = request.files["file"]
    
    tests = {
             "Scratch file is valid": False, 
             "Contains at least two sprite": False,
             "Contains at least three scripts total": False,
             "Contains at least one condition": False,
             "Contains at least one loop": False,
             "Contains at least one variable": False,
             "Contains at least one sound": False
            }
    
    score = 0
    
    if file and allowed_file(file.filename):

      file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
      results = json.loads(main(os.path.join(app.config['UPLOAD_FOLDER'], file.filename)))
      
      tests["Scratch file is valid"] = True
      
      if results["num_sprites"] >= 2:
        tests["Contains at least two sprite"] = True
        score += 1/7
      
      if results["num_scripts"] >= 3:
        tests["Contains at least two sprite"] = True
        score += 1/7
        
      if results["num_conditionals"] >= 1:
        tests["Contains at least one condition"] = True
        score += 1/7
        
      if results["num_loops"] >= 1:
        tests["Contains at least one loop"] = True
        score += 1/7
      
      if results["num_variables"] >= 1:
        tests["Contains at least one variable"] = True
        score += 1/7
      
      if results["num_sounds"] >= 1:
        tests["Contains at least one sound"] = True
        score += 1/7
        
      os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
      
    else:
      
      tests["Scratch file is valid"] = False
    
    s.execute("INSERT INTO assignments (user_id, assignment_id, score, assignment_name) VALUES (:user_id, :assignment_id, :score, :assignment_name)", {"user_id": session.get("user_id"), "assignment_id": 1, "score": int(score * 100), "assignment_name": "Scratch 1"})
    s.commit()
    
    return render_template("test.html", tests=tests, score=int(score * 100))

  else:
    
    return render_template("assignment1.html")

@app.route('/gradebook')
@login_required
def grade():
  info = s.execute("SELECT * FROM assignments WHERE user_id=:user_id", {"user_id": session.get("user_id")})
  # {"name": [i.score, "bg-danger"]}
    
  infos = {}
  
  for i in info:
    try:
      if infos[i.assignment_name] < i.score:
        if i.score < 70:
          infos[i.assignment_name] = [i.score, "bg-danger"]
        else:
          infos[i.assignment_name] = [i.score, "bg-success"]
    except:
        if i.score < 70:
          infos[i.assignment_name] = [i.score, "bg-danger"]
        else:
          infos[i.assignment_name] = [i.score, "bg-success"]
  
  print(infos)
  return render_template("gradebook.html", infos=infos)

@app.route('/submissions')
@login_required
def submissions():
  info = s.execute("SELECT * FROM assignments WHERE user_id=:user_id", {"user_id": session.get("user_id")})
  return render_template("submission.html", info=info)


@app.route('/')
@login_required
def index():
    return render_template("index.html")

@app.route('/logout')
def logout():
  session.clear()
  return redirect('/')


@app.route("/assignment/3", methods=["GET", "POST"])
def assignment3():
  if request.method == "POST":  

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    
    
    
  else:
    return render_template("assignment3.html")

if __name__ == "__main__":
  app.run()