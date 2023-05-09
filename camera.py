from threading import Thread, Lock #native python library to allow threading in python programs
import cv2 #opencv import due to camera stuff being used
import time


class CameraStream(object): #camerastream class definition
    def __init__(self, src="trimmed driving video.mp4"): #camerastream class constructor, src = 0 due to camera ports being ordered by number (0 is first cam plugged in, 1 is second, etc and can do external link sources too)
        self.stream = cv2.VideoCapture(src) #self.stream attribute becomes opencv videocapture 

        #set resolution limits of camera
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        #self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 2) #delay, useless tbh (min 1 max 10)
        self.FPS = 1/30 #set fps of camera (doesnt seem to work perfectly but idk better than overworking the pi)

        (self.grabbed, self.frame) = self.stream.read() #self.grabbed is boolean ensuring that reading videocapture worked, self.frame is the actual content of the read call
        self.started = False #when object is instantiated set started to false as to prevent double starting somehow thats possible apparently
        self.read_lock = Lock() #something to do with threading cause look at import statement it imports lock from threading

    def start(self): #runs at start of flask program
        if self.started: #checks if self.started attribute is false and stops start sequence if it somehow is
            print("video already started!!")
            return None
        self.started = True #if not started already, then set started to true
        self.thread = Thread(target=self.update, args=()) #threading stuff that idk tbh it just works but yea cool it outlines stuff for thread i think
        self.thread.start() #starts thread
        return self #idk why it returns self but it "simply means that your method returns a reference to the instance object on which it was called" and yea idk it works so cool

    def update(self): #alright so this function basically runs in a seperate thread and keeps constantly grabbing a frame from the camera because doing that on one thread is slow
        while self.started:
            (grabbed, frame) = self.stream.read()
            self.read_lock.acquire()
            self.grabbed, self.frame = grabbed, frame
            self.read_lock.release()

    def read(self): #runs like every millisecond cause it runs in the generator function in app.py so yea basically updates the frame each time its run
        self.read_lock.acquire() #thread thing again idk maybe hooks function to seperate thread if i had to guess
        frame = self.frame.copy() #IMPORTANT: grabs the frame from the seperate update thread frame stream, not actually reading from camera but grabbing frame from seperate thread of camera readings
        self.read_lock.release() #thread thing again woo maybe end thread idfk
        time.sleep(self.FPS) #limits framerate by limiting the speed at which it grabs new frames from the constant stream of frame readings in the seperate update thread. this is what actually limits the framerate
        return frame #profit (returns frame)

    def stop(self): #sets started to false and i think closes thread too idk too well but likely to prevent process overkill
        self.started = False
        self.thread.join()

    def __exit__(self, exc_type, exc_value, traceback): #runs on program exit
        self.stream.release() #stops stream to prevent it from running in background and hogging processes, opencv thing
