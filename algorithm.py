import cv2
import os
import numpy as np
import face_recognition
import time
def face_recognition_algorithm(user_id):
    # Path of the dataset
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    dataset = os.path.join(BASE_DIR, "static", "images")

    # Function to resize the image
    def resize_image(image, size=(224, 224)):
        return cv2.resize(image, size)

    # List to store images and names
    images = []
    names = []

    # Loop for searching the dataset
    for person in os.listdir(dataset):
        person_folder = os.path.join(dataset, person)

        # For every person folder, load the images
        if os.path.isdir(person_folder):  # Check whether the path is a folder
            for image in os.listdir(person_folder):
                path_of_image = os.path.join(person_folder, image)
                image_to_load = cv2.imread(path_of_image)
                if image_to_load is not None:
                    image_to_load = resize_image(image_to_load)
                    images.append(image_to_load)
                    names.append(person)

    images = np.array(images)
    names = np.array(names)


    known_face_encodings = []
    known_face_names = []
    # Encode faces from the dataset
    def encode_faces(images, names):
        for image, name in zip(images, names):
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_image)
            known_face_encodings.extend(face_encodings)
            known_face_names.extend([name] * len(face_encodings))

    encode_faces(images, names)

    
    video_capture = cv2.VideoCapture(1)
    if not video_capture.isOpened():
        print("Error: Could not open video source.")
        return False
    start_time = time.time()
    verified = False
    while True:

        ret, frame = video_capture.read()
        if not ret:
            print("Error could not read frame from video.")
            return False

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                if name == user_id:
                    verified = True
            # Draw a rectangle around the face
            #cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Display the name below the face
            #cv2.putText(frame, name, (left + 10, bottom + 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        

        elapsed_time = time.time() - start_time
        
        if verified or elapsed_time > 5:
            break

    
    video_capture.release()
    cv2.destroyAllWindows()
    return verified