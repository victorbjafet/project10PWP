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

#cv imports
import cv2 as cv #opencv import
import numpy as np #numpy import




#OBJECT INSTANCES
app = Flask(__name__) #creates flask app instance

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


# template matching stuff --------------------------------------------------------
template_paths = ['cv_templates/car1.png', 'cv_templates/car1.1.png', 'cv_templates/car1.2.png', 'cv_templates/car2.png','cv_templates/leftArrow.png','cv_templates/rightArrow.png']
templates = []
template_resolutions = []
template_keys = []
for path in template_paths:
    template = cv.imread(path, cv.IMREAD_GRAYSCALE)
    templates.append(template)
    template_resolutions.append(template.shape)
    template_keys.append(path.split('/')[-1])

video_path = 'finalVideo.mov'
video = cv.VideoCapture(video_path)

counter = 0
lastLeftFrame = -180
lastRightFrame = -180
# template matching stuff --------------------------------------------------------



# masked line detection stuff ----------------------------------------------------
region_top_left = (0, 250)  # Example values for top-left coordinate
region_bottom_right = (640, 360)  # Example values for bottom-right coordinate
# masked line detection stuff ----------------------------------------------------


def process_video():
    while True:
        global counter
        global lastLeftFrame
        global lastRightFrame

        success, frame = video.read()
        if not success: #if video ended then go back to beginning to loop the video
            counter = 0
            lastLeftFrame = -180
            lastRightFrame = -180
            video.set(cv.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = cv.resize(frame, (640, 360))
        counter += 1
        

        ##opencv stuff goes here -----------------------------------------------------
        region_of_interest = frame[region_top_left[1]:region_bottom_right[1], region_top_left[0]:region_bottom_right[0]]
        
        for template, resolution, key in zip(templates, template_resolutions, template_keys):
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            heatmap = cv.matchTemplate(gray, template, cv.TM_CCOEFF_NORMED) # does the actual template matching, returns a heatmap of where the template matches
            detectedLocations = np.where(heatmap >= 0.75) # ensures the matches are 75% accurate or more, and gets positions on the heatmap where the threshold is met
            if detectedLocations:
                for location in zip(*detectedLocations[-1::-1]): #for each detected matching location (iterating backwards)
                    cv.rectangle(frame, location, (location[0] + resolution[1], location[1] + resolution[0]), (255, 0, 0), 2) #draws a rectangle around the matched area the size of the template that is being looked for, basically drawing a rectangle around the match
                    if key[:3] == 'car':
                        cv.putText(frame, 'car', location, cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    elif key[:4] == 'left':
                        cv.putText(frame, 'left', location, cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        lastLeftFrame = counter
                    elif key[:5] == 'right':
                        cv.putText(frame, 'right', location, cv.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        lastRightFrame = counter
                    break
        
        if counter - lastLeftFrame <= 180:
            frame = cv.arrowedLine(frame, (90, 45), (10, 45), (255, 0, 0), 4)
        elif counter - lastRightFrame <= 180:
            frame = cv.arrowedLine(frame, (10, 45), (90, 45), (255, 0, 0), 4)
        else:
            frame = cv.arrowedLine(frame, (45, 90) , (45, 10), (255, 0, 0), 4)
        
        gray_roi = cv.cvtColor(region_of_interest, cv.COLOR_BGR2GRAY)
        roi_edges = cv.Canny(gray_roi, 50, 150)
        lines = cv.HoughLinesP(roi_edges, 1, np.pi / 180, 50, minLineLength=30, maxLineGap=30)

        left_lines = []
        right_lines = []
        
        try:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    slope = (y2 - y1) / (x2 - x1)
                if slope > 0.4 or slope < -0.4:
                    # below adds offsets to lines so that it goes in the right position in the original image
                    x1 += region_top_left[0]
                    y1 += region_top_left[1]
                    x2 += region_top_left[0]
                    y2 += region_top_left[1]
                    
                    if slope > 0:
                        left_lines.append(line)
                    elif slope < 0:
                        right_lines.append(line)
                
                    cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), thickness=2)
        except:
            print('no lines at all')
        
        # Calculate the average slope and intercept for left lane lines
        if left_lines:
            left_slope = np.mean([((y2 - y1) / (x2 - x1)) for line in left_lines for x1, y1, x2, y2 in line if (x2 - x1) != 0])
            left_intercept = np.mean([y1 - left_slope * x1 for line in left_lines for x1, y1, x2, y2 in line])
        else:
            # Handle case when no left lane lines are detected
            left_slope = 0
            left_intercept = 0

        # Calculate the average slope and intercept for right lane lines
        if right_lines:
            right_slope = np.mean([((y2 - y1) / (x2 - x1)) for line in right_lines for x1, y1, x2, y2 in line if (x2 - x1) != 0])
            right_intercept = np.mean([y1 - right_slope * x1 for line in right_lines for x1, y1, x2, y2 in line])
        else:
            # Handle case when no right lane lines are detected
            right_slope = 0
            right_intercept = 0
        
        # Define the y-coordinate range for extrapolation
        y1 = region_of_interest.shape[0]
        y2 = int(y1 * 0.3)
        
        # Calculate the x-coordinates for the left and right lane lines
        if left_slope and left_intercept and y1 and y2:
            left_x1 = int((y1 - left_intercept) / left_slope)
            left_x2 = int((y2 - left_intercept) / left_slope)
        if right_slope and right_intercept and y1 and y2:
            right_x1 = int((y1 - right_intercept) / right_slope)
            right_x2 = int((y2 - right_intercept) / right_slope)
        
        # Draw the lane lines on the original image
        line_image = np.zeros_like(region_of_interest)
        if left_slope and left_intercept:
            cv.line(frame, (left_x1, y1 + region_top_left[1]), (left_x2, y2 + region_top_left[1]), (0, 0, 255), 10)
        if right_slope and right_intercept:
            cv.line(frame, (right_x1, y1 + region_top_left[1]), (right_x2, y2 + region_top_left[1]), (0, 0, 255), 10)

        if left_slope and left_intercept and right_slope and right_intercept:
            cv.line(frame, (int((left_x1 + right_x1) / 2), y1 + region_top_left[1]), (int((left_x2 + right_x2) / 2), y2 + region_top_left[1]), (255, 0, 255), 10)
        ##opencv stuff goes here -----------------------------------------------------



        ret, buffer = cv.imencode('.jpg', frame)
        frame_data = buffer.tobytes()
        time.sleep(0.028)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

    video.release()

@app.route('/video_feed') #endpoint where raw video feed is streamed
@login_required
def video_feed():
    # Return the streaming response
    return Response(process_video(), mimetype='multipart/x-mixed-replace; boundary=frame')




if __name__ == '__main__': #some sort of thing that makes it so it always runs threaded and on the network but i dont think it works whatever i still run flask run --host=0.0.0.0
    app.run(host='0.0.0.0', threaded=True)
