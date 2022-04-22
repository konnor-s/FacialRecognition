from time import sleep
from turtle import end_fill
import face_recognition
import firebase_admin
from firebase_admin import credentials, firestore, storage, initialize_app
import numpy as np
import os
import smtplib
import imghdr
from email.message import EmailMessage
import json

emailFile = open('email.json')
emailData = json.load(emailFile)
SENDER_EMAIL = emailData['Sender_Email']
RECIEVER_EMAIL = emailData['Reciever_Email']
PASSWORD = emailData['Password']


known_image1 = face_recognition.load_image_file("KnownImages/biden.jpg")
known_image2 = face_recognition.load_image_file("KnownImages/biden2.jpg")
known_image3 = face_recognition.load_image_file("KnownImages/biden4.jpg")
known_encoding1 = face_recognition.face_encodings(known_image1)[0]
known_encoding2 = face_recognition.face_encodings(known_image2)[0]
known_encoding3 = face_recognition.face_encodings(known_image3)[0]

known_encodings = [known_encoding1, known_encoding2, known_encoding3]

cred = credentials.Certificate("credentials.json")
initialize_app(cred, {'storageBucket': 'iotproject-60e4c.appspot.com'})

firestore_db = firestore.client()
bucket = storage.bucket()

# continuously run this program
while (1):
    print(".")
    uncheckedImages = list(bucket.list_blobs(prefix="Unchecked/"))
    if (len(uncheckedImages) > 1):
        print('Checking Image...')
        image = uncheckedImages[1]
        imageName = str(image).split(", Unchecked/")[1]
        imageName = imageName.split(",")[0]
        print(imageName)
        image.download_to_filename("./Unchecked/" + imageName)  # download image
        unknown_image = face_recognition.load_image_file("Unchecked/" + imageName)
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        results = face_recognition.compare_faces(known_encodings, unknown_encoding)

        face_locations = face_recognition.face_locations(unknown_image)

        # delete image from storage
        image.delete()

        # no face
        if (face_locations == []):  
            pass

        # if the person is identified
        elif (True in results):  
            print("Person Recognized")

        # face found but not recognized
        else:  
            print("Intruder Alert!")
            #upload to storage
            imageToUpload = bucket.blob("Intruders/" + imageName)
            imageToUpload.upload_from_filename("Unchecked/" + imageName)


            
            newMessage = EmailMessage()
            newMessage['Subject'] = "Intruder Detected: " + imageName.split(".")[0]
            newMessage['From'] = SENDER_EMAIL
            newMessage['To'] = RECIEVER_EMAIL
            newMessage.set_content('Image attached')

            with open('Unchecked/' + imageName, 'rb') as f:
                image_data = f.read()
                image_type = imghdr.what(f.name)
                image_name = f.name

            newMessage.add_attachment(image_data, maintype='image',
                                    subtype=image_type, filename=image_name)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:

                smtp.login(SENDER_EMAIL, PASSWORD)
                smtp.send_message(newMessage)

        # delete local image
        os.remove("Unchecked/" + imageName)

    sleep(5)
