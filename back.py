from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import ssl
import tensorflow as tf
import tensorflow_hub as hub
import cv2
import numpy as np


app = Flask(__name__)
socketio = SocketIO(app)

ssl._create_default_https_context = ssl._create_unverified_context


model = hub.load('https://tfhub.dev/google/movenet/singlepose/thunder/4')
movenet = model.signatures['serving_default']


# Threshold for keypoint confidence
threshold = 0.3


# Initialize video capture
video_source = 0
cap = cv2.VideoCapture(video_source)
if not cap.isOpened():
    print('Error opening video source')
    exit()


video_processing_started = False


@socketio.on('connect')
def on_connect():
    print('Client connected:', request.sid)
    emit('connection_status', {'message': 'Connected to server'})


@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected:', request.sid)


@socketio.on('start_video_processing')
def start_video_processing_socket():
    if not video_processing_started:
        start_video_processing()
        socketio.emit('video_processing_status', {'message': 'Video processing started'})
    else:
        socketio.emit('video_processing_status', {'message': 'Video processing already running'})


@socketio.on('stop_video_processing')
def stop_video_processing_socket():
    stop_video_processing()
    socketio.emit('video_processing_status', {'message': 'Video processing stopped'})




#video processing logic 
def start_video_processing():
    global cap, video_processing_started
    video_processing_started = True

    while video_processing_started:
        success, img = cap.read()


        if not success:
            print('Error reading frame')
            break


        y, x, _ = img.shape


        # Frame processing and keypoints detection
        tf_img = cv2.resize(img, (256, 256))
        tf_img = cv2.cvtColor(tf_img, cv2.COLOR_BGR2RGB)
        tf_img = np.asarray(tf_img)
        tf_img = np.expand_dims(tf_img, axis=0)
        image = tf.cast(tf_img, dtype=tf.int32)
        outputs = movenet(image)
        keypoints = outputs['output_0']


        feedback_message = assess_form(keypoints)  


        if feedback_message:
            socketio.emit('form_assessment', {'message': feedback_message})


        for k in keypoints[0, 0, :, :]:
            k = k.numpy()


            if k[2] > threshold:
                yc = int(k[0] * y)
                xc = int(k[1] * x)
                img = cv2.circle(img, (xc, yc), 2, (0, 255, 0), 5)


        cv2.imshow('Movenet', img)


        if cv2.waitKey(1) == ord("q"):
            break


        success, img = cap.read()


def stop_video_processing():
    global video_processing_started, cap
    video_processing_started = False
    cap.release()
    print('Video processing has been stopped.')




def calculate_angle(a, b, c):
    a = np.array(a)  # First point
    b = np.array(b)  # Mid point
    c = np.array(c)  # End point
   
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
   
    if angle > 180.0:
        angle = 360-angle
       
    return angle

def assess_form(keypoints):
    # Calculate angles using the provided keypoints
    left_leg_angle = calculate_angle(keypoints, 15, 13, 11)
    right_leg_angle = calculate_angle(keypoints, 16, 14, 12)
    left_arm_angle = calculate_angle(keypoints, 9, 7, 5)
    right_arm_angle = calculate_angle(keypoints, 10, 8, 6)


    feedback_message = ''


    # Assess leg angles for squat
    if not 80 <= left_leg_angle <= 100:  # Assuming ideal squat angle close to 90 degrees
        feedback_message += f'Adjust your left leg; current angle is {left_leg_angle:.2f}. '
    if not 80 <= right_leg_angle <= 100:
        feedback_message += f'Adjust your right leg; current angle is {right_leg_angle:.2f}. '



    if not 160 <= left_arm_angle <= 180:  # Assuming arms should be straight down
        feedback_message += f'Adjust your left arm; current angle is {left_arm_angle:.2f}. '
    if not 160 <= right_arm_angle <= 180:
        feedback_message += f'Adjust your right arm; current angle is {right_arm_angle:.2f}. '


    return feedback_message if feedback_message else 'Your form looks good.'   
   




@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)
