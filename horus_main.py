import cv2
import time
import horus_recognizer
import numpy as np
import horus_firebase_router
from horus_firebase_router import firebase_configs as configs
import horus_mqtt_router
import subprocess
import sys
from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

# TODO: Find why horus_main is not ending when ctrl-c is pressed (it keeps running - htop python to see)
# TODO: Use flask to stream and monitore while streaming
# TODO: Fix new user screen
# TODO: THATS ALLLL


class Main:

    def __init__(self):

        # Numpy instantiation
        self.numpy = np

        # Publisher settings
        self.publish_time_counter = time.time()
        self.publish_interval = 5000  # Seconds
        self.run_monitoring = True

        # Mqtt config
        self.mqtt_client = horus_mqtt_router.MqttRouter('horus_client')
        try:
            self.mqtt_client.initialize()
            self.mqtt_client.run()
        except Exception as e:
            print(e)

        # Firebase config
        self.fb_manager = horus_firebase_router.FirebaseManager(configs)
        self.start_recognition_system()

        self.put_on_storage = False

        # Camera settings
        self.cam = cv2.VideoCapture(0)
        self.cam.set(3, 640)  # set video widht
        self.cam.set(4, 480)  # set video height

        # Video control / Create video writer that writes .h264 videos -> will be transformed to .mp4
        self.fourcc = cv2.VideoWriter_fourcc(*'H264')
        self.video_recorder = cv2.VideoWriter('./captured_videos/output.h264', self.fourcc, 10, (640, 480))

    def start_recognition_system(self):
        # Get all user keys and their recognizable faces
        self.user_keys_and_faces = self.fb_manager.retrieve_all_recognizable_faces_related_by_user()

        # Recognizer settings
        self.recognizer = horus_recognizer.Recognizer()
        self.known_names = []
        self.known_faces_encodings = []

        # Get names and encodings from recognizer
        for recognizable_name, encoding in self.recognizer.do_recognition_and_get_encodings().items():
            self.known_names.append(recognizable_name)
            self.known_faces_encodings.append(encoding)

        # System control
        self.logged_user = self.fb_manager.retrieve_logged_user()
        # self.logger_user_stream = self.fb_manager.start_logged_user_watch()

    def start_monitoring(self):
        while self.run_monitoring:

            # Grab a single frame of video
            ret, frame = self.cam.read()

            # Only publish image if user is logged and a signal has been received
            if self.logged_user is not None:

                # Capture image and publish on Firebase
                if self.mqtt_client.publish_image:
                    self.mqtt_client.publish_image = False
                    try:
                        cv2.imwrite('./captured_pictures/pictureTaken.png', frame)
                    except Exception as e:
                        print("Error capturing image: ", e)
                        break

                    self.fb_manager.publish_taken_picture(self.logged_user)

                # If True record video flag has been received by mqtt client
                if self.mqtt_client.record_video:

                    # Starts to write the images on video
                    self.video_recorder.write(frame)
                    self.put_on_storage = True

                # If stop recording video flag has been received by mqtt client
                if self.put_on_storage and self.mqtt_client.release_video:

                    # Releasing video_recorder
                    self.video_recorder.release()
                    time.sleep(0.1)

                    # Converting from .h264 to .mp4 video
                    command = "MP4Box -add ./captured_videos/output.h264 ./captured_videos/output.mp4"
                    convCommand = [command]

                    # Executing MP4Box
                    subprocess.Popen(convCommand, shell=True)
                    time.sleep(5)

                    # Publishing recorded video
                    self.fb_manager.publish_video(self.logged_user)
                    time.sleep(0.1)

                    # Re-instantiating video_recorder
                    self.video_recorder = cv2.VideoWriter('./captured_videos/output.h264', self.fourcc, 10, (640, 480))
                    self.put_on_storage = False
                    self.mqtt_client.record_video = False
                    self.mqtt_client.release_video = False
                    print('Video has been recorded')

                # Check if system has received restart flag (recognition)
                if self.mqtt_client.restart_system:
                    print('Restarting system')
                    self.mqtt_client.restart_system = False
                    self.start_recognition_system()

                # Check if unrecognition has been activated
                if self.mqtt_client.unrecognize:
                    self.mqtt_client.unrecognize = False
                    self.recognizer.unrecognize_face()
                    print('Unrecognized user ', self.logged_user, ' registered face!')
                    self.start_recognition_system()
                    self.start_monitoring()

                if self.mqtt_client.recognize:
                    print('New recognition activated')
                    self.mqtt_client.recognize = False
                    self.start_recognition_system()
                    self.start_monitoring()

            # Check if video is being record; If True, don't execute recognition
            if self.put_on_storage:
                self.start_monitoring()

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_frame = frame[:, :, ::-1]

            # Find all the faces and face encodings in the current frame of video
            face_locations = self.recognizer.find_faces_locations(rgb_frame)
            face_encodings = self.recognizer.find_encodings_on_frame(rgb_frame, face_locations)

            # See if the face is a match for the known face(s)
            recognized_face_indexes = []
            for face_encoding in face_encodings:
                matches = self.recognizer.compare_faces(self.known_faces_encodings, face_encoding)

                # Get recognized faces indexes
                recognized_face_indexes = self.numpy.where(matches)[0]

            if (time.time() - self.publish_time_counter) > self.publish_interval:

                # Iterate over all recognized faces on current frame
                for recognized_face_index in recognized_face_indexes:

                    # Get recognized name (self.known names come from firebase API)
                    recognized_name = self.known_names[recognized_face_index]

                    # Loop through all users and their recognizable faces
                    for user_key, recognizable_names in self.user_keys_and_faces.items():
                        names_to_publish = []

                        # Iterate through all users recognizable faces
                        for recognizable_name in recognizable_names:

                            # Check if recognized face is registered on firebase
                            if recognizable_name == recognized_name:
                                names_to_publish.append(recognized_name)

                        if names_to_publish:
                                print("Publishing: ", names_to_publish, " on user: ", user_key)
                                cv2.imwrite('./captured_pictures/pictureTaken.png', frame)
                                self.fb_manager.publish_recognized_faces(names_to_publish, user_key)
                        else:
                            print("Publishing UKNOWN on user: ", user_key)
                            cv2.imwrite('./captured_pictures/pictureTaken.png', frame)
                            self.fb_manager.publish_unknown_faces(user_key)

                # Reset publish_time_counter() to wait for 10s until next publish
                self.publish_time_counter = time.time()

    def stop_monitoring(self):
        self.run_monitoring = False




if __name__ == '__main__':
    main = Main()
    try:
        main.start_monitoring()
    except KeyboardInterrupt:
        print("Cleaning references...")
        pass
    finally:
        main.fb_manager.stop_logged_user_watcher()
        main.cam.release()
        print('Done!')
        sys.exit(1)
