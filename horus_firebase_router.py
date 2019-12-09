import pyrebase as pyr
import sys
import os
import datetime
import time

db_url = 'https://tccfirstattempt.firebaseio.com'
storage_url = 'gs://tccfirstattempt.appspot.com'
firebase_configs = {
    "apiKey": "AIzaSyCp0RIPqODI_Zxsrfu48Yt087XD8orxXWg",
    "authDomain": "tccfirstattempt.firebaseapp.com",
    "databaseURL": "https://tccfirstattempt.firebaseio.com",
    "projectId": "tccfirstattempt",
    "storageBucket": "tccfirstattempt.appspot.com",
    "messagingSenderId": "994487973781",
    "serviceAccount": "./cred.json"
}


class FirebaseManager:
    def __init__(self, configs):

        try:

            self.firebase_conn = pyr.initialize_app(configs)
            self.firebase_storage = self.firebase_conn.storage()
            self.firebase_db = self.firebase_conn.database()
            # self.user_watcher = self.firebase_db.child('last_user_logged').child('userLogged').stream(self.logged_user_watcher)

        except Exception:
            print("Error connecting to Firebase: " + Exception)
            sys.exit(1)

    # def stop_logged_user_watcher(self):
    #     self.user_watcher.close()

    # def logged_user_watcher(self, message):
    #     print(message["event"])  # put
    #     print(message["path"])  # /-K7yGTTEp7O549EzTYtI
    #     print(message["data"])  # {'title': 'Pyrebase', "body": "etc..."}

    def retrieve_recognizable_name_related_by_image_key(self):
        # Creates dict that has all users that have faces to recognize
        users_keys = self.firebase_db.child("perfil_publicacoes").get()

        image_keys_and_names = {}

        # Iterates over all user_keys
        for user_key in users_keys.val():
            keys = self.firebase_db.child("perfil_publicacoes").child(user_key).get()

            # Iterate over all recognizable faces and get their names
            for key in keys.each():
                face_name = self.firebase_db.child("perfil_publicacoes").child(user_key).child(key.key()).child("titulo").get()

                image_keys_and_names[key.key()] = face_name.val()

        return image_keys_and_names

    def retrieve_all_recognizable_faces_related_by_user(self):
        # Creates dict that has all users that have faces to recognize
        users_keys = self.firebase_db.child("perfil_publicacoes").get()

        names = []
        users_and_faces = {}

        # Iterates over all user_keys
        for user_key in users_keys.val():
            keys = self.firebase_db.child("perfil_publicacoes").child(user_key).get()

            # Iterate over all recognizable faces and get their names
            for key in keys.each():
                face_names = self.firebase_db.child("perfil_publicacoes").child(user_key).child(key.key()).child("titulo").get()

                if face_names.val() not in names:
                    names.append(face_names.val())

            # Create result dict
            users_and_faces[user_key] = names

            # Clear recognizable faces
            names = []
        return users_and_faces

    def download_and_rename_images(self):
        image_keys_and_names = self.retrieve_recognizable_name_related_by_image_key()
        # Download and rename images
        for key in image_keys_and_names:
            try:
                self.firebase_storage.download("perfil_images/" + key, "./images/" + image_keys_and_names[key] + ".jpg", None)
                print("Image downloaded!")
            except Exception:
                print("Error downloading image")

        return image_keys_and_names

    def retrieve_logged_user(self):
        logged_user = self.firebase_db.child("last_user_logged").child("userLogged").get()
        if logged_user.val() == 'none':
            return None

        return logged_user.val()

    def retrieve_known_face_to_unrecognize(self):
        known_faces_keys_to_unrecognize = self.firebase_db.child('reiniciar_sistema').get().val()
        known_names_to_unrecognize = []
        for known_face_to_unrecognize in known_faces_keys_to_unrecognize:
            known_names_to_unrecognize.append(known_faces_keys_to_unrecognize[known_face_to_unrecognize]['flag'])

        return known_names_to_unrecognize

    def publish_video(self, logged_user):
        self.firebase_db.child("video_publicacoes").child(logged_user).push({"titulo": str(datetime.datetime.now())})
        data = self.firebase_db.child("video_publicacoes/" + logged_user).order_by_key().limit_to_last(1).get()

        for x in data.each():
            imageName = x.key()

        print("Storing video on Firebase")

        self.firebase_storage.child("videos/"+imageName).put("./captured_videos/output.mp4")

        if os.path.exists("./captured_videos/output.mp4"):
            os.remove("./captured_videos/output.mp4")
        else:
            print("The file does not exist")
        if os.path.exists("./captured_videos/output.h264"):
            os.remove("./captured_videos/output.h264")
        else:
            print("The file does not exist")

    def publish_taken_picture(self, user_key):
        time.sleep(0.5)
        print("Publishing image!")
        try:
            self.firebase_db.child("publicacoes").child(user_key).push({"titulo": "Captura da camera", "data": str(datetime.datetime.now())})
            data = self.firebase_db.child("publicacoes").child(user_key).order_by_key().limit_to_last(1).get()
            for x in data.each():
                imageName = x.key()

            self.firebase_storage.child("imagens/"+str(imageName)).put("./captured_pictures/pictureTaken.png")
            if os.path.exists("./captured_pictures/pictureTaken.png"):
                os.remove("./captured_pictures/pictureTaken.png")
            else:
                print("The file does not exist")
        except Exception as e:
            print(e)

    def publish_recognized_faces(self, names_to_publish, user_key):
        time.sleep(0.05)
        self.firebase_db.child("publicacoes").child(user_key).push(
            {"titulo": ",".join(names_to_publish), "data": str(datetime.datetime.now())})
        data = self.firebase_db.child("publicacoes").child(user_key).order_by_key().limit_to_last(1).get()
        for x in data.each():
            imageName = x.key()

        self.firebase_storage.child("imagens/" + str(imageName)).put("./captured_pictures/pictureTaken.png")
        if os.path.exists("./captured_pictures/pictureTaken.png"):
            os.remove("./captured_pictures/pictureTaken.png")
        else:
            print("The file does not exist")

    def publish_unknown_faces(self, user_key):
        time.sleep(0.05)
        self.firebase_db.child("publicacoes").child(user_key).push({"titulo": "Desconhecido", "data": str(datetime.datetime.now())})
        data = self.firebase_db.child("publicacoes").child(user_key).order_by_key().limit_to_last(1).get()
        for x in data.each():
            imageName = x.key()

        self.firebase_storage.child("imagens/"+str(imageName)).put("./captured_pictures/pictureTaken.png")
        if os.path.exists("./captured_pictures/pictureTaken.png"):
            os.remove("./captured_pictures/pictureTaken.png")
        else:
            print("The file does not exist")

# If it's executed like a script (not imported)
if __name__ == '__main__':
    fb = FirebaseManager(configs=firebase_configs)
    # users_and_recognizable_faces = fb.retrieve_all_recognizable_faces_related_by_user()
    # recognizable_faces_related_by_key = fb.retrieve_recognizable_name_related_by_image_key()
    # print(recognizable_faces_related_by_key)
    # fb.download_and_rename_images()
    # print(fb.publish_video('ZG91Z2xhc2tvcmd1dHRAZ21haWwuY29t'))


