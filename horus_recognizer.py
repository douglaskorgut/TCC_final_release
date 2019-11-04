import face_recognition
import os
from horus_firebase_router import firebase_configs as configs
import horus_firebase_router


class Recognizer:
    def __init__(self):
        self.face_recognition = face_recognition
        self.images_file_names = []
        # Firebase config
        self.fb_manager = horus_firebase_router.FirebaseManager(configs)

        # Download, rename and put images on folder /images
        self.image_keys_and_names = self.fb_manager.download_and_rename_images()

        # If no face registered
        self.images_file_names_buggy = os.listdir('images')
        for image_name in self.images_file_names_buggy:
            self.images_file_names.append(image_name.replace('.jpg', ''))

        if not self.images_file_names:
            raise IOError('No recognizable image found on horus/images folder')

    def do_recognition_and_get_encodings(self):
        known_faces = {}

        # Iterating over all downloaded images
        for image_file_name in self.images_file_names:
            image_file_name = image_file_name + '.jpg'

            # Getting image
            image = face_recognition.load_image_file('images/' + image_file_name)

            # Creating encoding
            encoding = face_recognition.face_encodings(image)[0]

            # Populate known_faces dict
            known_faces[image_file_name.replace('.jpg', '')] = encoding

        return known_faces

    def find_faces_locations(self, rgb_frame):
        return self.face_recognition.face_locations(rgb_frame)

    def find_encodings_on_frame(self, rgb_frame, face_locations):
        return self.face_recognition.face_encodings(rgb_frame, face_locations)

    def compare_faces(self, known_faces, face_encoding):
        match = self.face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.60)
        return match

    def unrecognize_face(self):
        known_faces_to_unrecognize = self.fb_manager.retrieve_known_face_to_unrecognize()
        for known_face_to_unrecognize in known_faces_to_unrecognize:
            for image_file_name in self.images_file_names:
                if image_file_name == known_face_to_unrecognize:
                    try:
                        os.remove('./images/' + image_file_name + '.jpg')
                        print(image_file_name, ' removed from image folder. Doing recog again...')
                    except Exception as e:
                        print("Error trying to remove file: ", image_file_name)


if __name__ == '__main__':
    recognizer = Recognizer()
    recognizer.do_recognition_and_get_encodings()
