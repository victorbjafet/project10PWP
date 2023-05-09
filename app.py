#command to run server on network: flask run --host=0.0.0.0
#i over-document my code because i'm a beginner and i want to make sure i understand whats going on, also at times id be lost without the documentation
#shoutout to github copilot




#IMPORTS
import time

#general flask imports
from flask import Flask, render_template, Response, request, redirect, url_for

#authorization related imports
from flask_sqlalchemy import SQLAlchemy #allows interaction with the sqlite database
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user #allows for user authentication and session management
from flask_wtf import FlaskForm #allows for the creation of forms that will import user information into the database or login a user
from wtforms import StringField, PasswordField, SubmitField #allows for the creation of forms that will import user information into the database or login a user
from wtforms.validators import InputRequired, Length, ValidationError #allows for the validation of user input in user registration/login forms
from flask_bcrypt import Bcrypt #allows for the hashing of passwords

#camera imports 
from camera import CameraStream #imports "camerastream" class from 'camera.py' file located in the same dir as this app.py file
import cv2 #opencv import




#OBJECT INSTANCES
app = Flask(__name__) #creates flask app instance
cap = CameraStream().start() #initialize camerastream object instance from camera.py

#auth instances
bcrypt = Bcrypt(app) #creates bcrypt instance for hashing passwords
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' #route to database file (needs to be before sqlalchemy instance)
app.config['SECRET_KEY'] = 'thisisasecretkey' #secret key for session management
db = SQLAlchemy(app) #creates sqlalchemy instance in order to interact with database
login_manager = LoginManager() #creates login manager instance from flask_login (does most of the heavy lifting for auth such as session management and whatnot)
login_manager.init_app(app) #initializes login manager
login_manager.login_view = 'login' #sets login route 




#ROUTES AND CLASSES
@login_manager.user_loader #reload user object from user id stored in session (idk exactly what this does but this what the guy in the tutorial said it does), i think its basically just managing sessions
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin): #creates database table and columns
    id = db.Column(db.Integer, primary_key=True) #primary key, auto increments
    username = db.Column(db.String(20), nullable=False, unique=True) #username column, has to be filled out, has to be unique, max length 20
    password = db.Column(db.String(80), nullable=False) #password column, has to be filled out, max length 80 (will be hashed)

class RegisterForm(FlaskForm): #creates form for registering a user, inherits from FlaskForm class
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"}) #has to be filled out, sets placeholder "username" and length limitations

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"}) #has to be filled out, sets placeholder "password" and length limitations

    submit = SubmitField('Register') #button to submit register form

    def validate_username(self, username): #checks if username already exists in database
        existing_user_username = User.query.filter_by( #queries database for username that matches the one entered in the form to see if it already exists
            username=username.data).first()
        if existing_user_username: #if it does exist, it will throw an error
            raise ValidationError(
                'That username already exists. Please choose a different one.')

class LoginForm(FlaskForm): #creates form for logging in a user, inherits from FlaskForm class
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"}) #has to be filled out, sets placeholder "username" and length limitations

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"}) #has to be filled out, sets placeholder "password" and length limitations

    submit = SubmitField('Login') #button to submit login form




#log server startup
with open("logFile.txt",'at') as logFile:
    logFile.write("Start of Server Session - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + "\n")

#below is the file writing/logging function (just for abstraction)
def logToFile(logItem):
    with open("logFile.txt", "at") as logFile: #'at' stands for "append text file"
        logFile.write(str(logItem))




#ENDPOINTS, just add @login_required to any route you want to protect
@app.route('/log') #endpoint for the stream of log data
@login_required
def log():
    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Set \"log\" Endpoint as Log SSE Source\n")
    def generate(): #generator function
        with open('logFile.txt', 'r') as logFile: #open the log file
            last_pos = logFile.tell() #get the last position of the file (where the last line was)
            while True:
                line = logFile.readline() #read the last line
                if not line: #if there is no new line, wait .1 seconds and try again
                    time.sleep(.1)
                    logFile.seek(last_pos) #go back to the last position
                else:
                    last_pos = logFile.tell() #get the new position
                    yield 'data: {}\n\n'.format(line.strip()) #return the new line
    return Response(generate(), mimetype='text/event-stream') #text/event-stream is a media type that allows a server to send events to the client (sse, server sent events)


#main page that displays all the important stuff, can only be accessed when logged in
@app.route('/dashboard', methods=['GET', 'POST']) 
@login_required
def dashboard(): 
    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Dashboard Page\n")
    return render_template('dashboard.html', username=current_user.username) #gets the username of the current user to pass and display (also passes the html page)


#below endpoints have to do with auth
@app.route('/')
def home(): #home page, if user is logged in, redirect to dashboard, if not, display home page
    if current_user.is_authenticated:
        logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Redirected to Dashboard from Home Page\n")
        return redirect(url_for('dashboard'))
    logToFile("Anonymous User (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Home Page\n")
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login(): #login page, if user is logged in, redirect to dashboard, if not, display login page with login form
    if current_user.is_authenticated:
        logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Redirected to Dashboard from Login Page\n")
        return redirect(url_for('dashboard'))
    logToFile("Anonymous User (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Login Page\n")
    form = LoginForm() #login form instance
    if form.validate_on_submit(): #if form is valid and submitted
        user = User.query.filter_by(username=form.username.data).first() #queries database for username that matches the one entered in the form
        if user: #if user exists
            if bcrypt.check_password_hash(user.password, form.password.data): #checks if password entered in form matches the hashed password in the database
                login_user(user) #logs in user
                logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Login and Redirect\n")
                return redirect(url_for('dashboard')) #redirects to dashboard page after logging in
    return render_template('login.html', form=form) #renders login page with login form

@app.route('/register', methods=['GET', 'POST'])
def register(): #register page, if user is logged in, redirect to dashboard, if not, display register page with register form
    if current_user.is_authenticated:
        logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Redirected to Dashboard from Register Page\n")
        return redirect(url_for('dashboard'))
    logToFile("Anonymous User (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Register Page\n")
    form = RegisterForm() #register form instance
    if form.validate_on_submit(): #if form is valid and submitted
        hashed_password = bcrypt.generate_password_hash(form.password.data) #hashes password that is passed in the form
        new_user = User(username=form.username.data, password=hashed_password) #creates new user object with username and hashed password that can be passed into the database with all the columns
        db.session.add(new_user) #adds new user to database
        db.session.commit() #commits changes to database
        logToFile("Anonymous User (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Account \"" + form.username.data + "\" Registered\n")
        return redirect(url_for('login')) #redirects to login page after registering
    return render_template('register.html', form=form) #renders register page with register form

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Logout\n")
    logout_user() #flask_login function to logout user
    return redirect(url_for('login'))


#endpoints to control what point in the video you want to go to
@app.route("/skipBeginning", methods = ['GET','POST'])
@login_required
def skipBeginning():

    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Forward\n")
    return "<p>forward</p>"

@app.route("/skipMiddle", methods = ['GET','POST'])
@login_required
def skipMiddle():

    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Forward\n")
    return "<p>forward</p>"



#below are video related endpoints and functions
def gen_frame(): #generator function, meaning it runs over and over again and the yield statement at the end instead of being a return it returns a ton over and over looped
    while cap:
        frame = cap.read() #calls class read method
        convert = cv2.imencode('.jpg', frame)[1].tobytes() #sets 'encode' var to a .jpg encoded frame in some fancy byte thing idk its basically encoding the image and yea
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + convert + b'\r\n') # concate frame one by one and show result, idk whats going on here but it seems to just be like sending a frame with a ton of random stuff that i might need to understand later idk

@app.route('/video_feed') #endpoint where raw video feed is streamed
@login_required
def video_feed():
    logToFile(str(current_user.username) + " (" + str(request.environ['REMOTE_ADDR']) + ") - " + time.strftime("%m/%d/%Y") + "@" + time.strftime("%H:%M:%S", time.localtime()) + " | Set \"video_feed\" Endpoint as Video Stream Source\n")
    return Response(gen_frame(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') #returns the running of the gen_frame function alongside some html stuff i guess? idk




if __name__ == '__main__': #some sort of thing that makes it so it always runs threaded and on the network but i dont think it works whatever i still run flask run --host=0.0.0.0
    app.run(host='0.0.0.0', threaded=True)
