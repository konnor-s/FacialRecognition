from time import sleep
from turtle import end_fill
import face_recognition
import firebase_admin
from firebase_admin import credentials, firestore, storage, initialize_app
import numpy as np


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

#continuously run this program
while (1):
    
    doc = list(firestore_db.collection(u'CurrentIncident').get()) #get this collection
    doc = doc[0].to_dict() #get the document data
    
    if (doc["newData"] == True): # there is a new image
        datetime = doc["datetime"]
        image = bucket.get_blob("Images/" + datetime) # retrieve image
        image.download_to_filename("./Images/" + datetime) # download image

        unknown_image = face_recognition.load_image_file("./Images/" + datetime)
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
        results = face_recognition.compare_faces(known_encodings, unknown_encoding)
        
        if (True in results): # if the person is identified
            print("Person Recognized")
            
            
           
        else:
            print("Intruder Alert!")
            #do something
        firestore_db.collection('CurrentIncident').document("CurrentIncidentDoc").update({'newData': False})
    sleep(5)

