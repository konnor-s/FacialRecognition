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
import datetime
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth

emailFile = open('email.json')
emailData = json.load(emailFile)
SENDER_EMAIL = emailData['Sender_Email']
RECIEVER_EMAIL = emailData['Reciever_Email']
PASSWORD = emailData['Password']


known_image1 = face_recognition.load_image_file("KnownImages/a1.jpg")
known_image2 = face_recognition.load_image_file("KnownImages/a2.jpg")
known_image3 = face_recognition.load_image_file("KnownImages/a3.jpg")
known_image5 = face_recognition.load_image_file("KnownImages/a5.jpg")
known_image6 = face_recognition.load_image_file("KnownImages/a6.jpg")

known_encoding1 = face_recognition.face_encodings(known_image1)[0]
known_encoding2 = face_recognition.face_encodings(known_image2)[0]
known_encoding3 = face_recognition.face_encodings(known_image3)[0]
known_encoding5 = face_recognition.face_encodings(known_image5)[0]
known_encoding6 = face_recognition.face_encodings(known_image6)[0]

known_encodings = [known_encoding1, known_encoding2, known_encoding3, known_encoding5, known_encoding6]

cred = credentials.Certificate("credentials.json")
initialize_app(cred, {'storageBucket': 'iotproject-60e4c.appspot.com'})

firestore_db = firestore.client()
bucket = storage.bucket()

exitTimes = list()
dt = datetime.datetime.now()
i = 0
# continuously run this program
while (1):
    
    dt = datetime.datetime.now()
    dt_h = dt.hour
    dt_m = dt.minute
    dt_s = dt.second
    dt_t = dt_h*60*60 + dt_m*60 + dt_s

    #update exits every minute
    if (i%12 == 0):
        exitData = list() #list of times in seconds after midnight 
        exitCollection = list(firestore_db.collection('Exit').get()) 
        for doc in exitCollection:
            timeStr = doc.to_dict()['Time']
            dt = datetime.datetime.fromisoformat(timeStr)
            h = dt.hour
            m = dt.minute
            s = dt.second
            t = h*60*60 + m*60 + s
            exitData.append(t)

        X = np.array(list(zip(exitData,np.zeros(len(exitData)))))
        bandwidth = estimate_bandwidth(X, quantile=.5)
        ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
        ms.fit(X)
        labels = ms.labels_
        cluster_centers = ms.cluster_centers_

        labels_unique = np.unique(labels)
        n_clusters_ = len(labels_unique)
        exitTimes.clear()
        for k in range(n_clusters_):
            my_members = labels == k
            #print("cluster {0}: {1}".format(k, X[my_members, 0]))
            if len(X[my_members, 0]) > 2:
                exitTime = np.mean(X[my_members, 0])
                exitTimes.append(exitTime)
       
    #send an email if they will leave in 10 minutes
    for exitTime in exitTimes:
        if (dt_t + 605 > exitTime) and (dt_t + 600 < exitTime):
            newMessage = EmailMessage()
            newMessage['Subject'] = "Prepare to leave!"
            newMessage['From'] = SENDER_EMAIL
            newMessage['To'] = RECIEVER_EMAIL
            newMessage.set_content("Don't forget to shut off the lights!\nOr I'll shut off yours...")

            with open('robot.jpg', 'rb') as f:
                image_data = f.read()
                image_type = imghdr.what(f.name)
                image_name = f.name

            newMessage.add_attachment(image_data, maintype='image',
                                    subtype=image_type, filename=image_name)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(SENDER_EMAIL, PASSWORD)
                smtp.send_message(newMessage)
            

    uncheckedImages = list(bucket.list_blobs(prefix="Unchecked/"))
    if (len(uncheckedImages) > 1):
        print('Checking Image...')
        
        dt_str = str(dt)
        image = uncheckedImages[1]
        imageName = str(image).split(", Unchecked/")[1]
        imageName = imageName.split(",")[0]
        print(imageName)
        image.download_to_filename("./Unchecked/" + imageName)  # download image
        unknown_image = face_recognition.load_image_file("Unchecked/" + imageName)
        face_locations = face_recognition.face_locations(unknown_image)
        # no face
        if (face_locations == []):  
            print("No face found")
            firestore_db.collection('Exit').document(dt_str).set({
                    'Time':dt_str})
            #set the tenent as gone
            firestore_db.collection('Present').document('Present').set({
                    'Present':False})
        else:
            unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
            results = face_recognition.compare_faces(known_encodings, unknown_encoding)

                # if the person is identified
            if (True in results):  
                print("Person Recognized")
                firestore_db.collection('Identified').document(dt_str).set({
                    'Time':dt_str})
                #set the tenent as present
                firestore_db.collection('Present').document('Present').set({
                    'Present':True})
                

            # face found but not recognized
            else:  
                print("Intruder Alert!")
                #upload to storage

                imageToUpload = bucket.blob("Intruders/" + str(dt))
                imageToUpload.upload_from_filename("Unchecked/image.png")

                firestore_db.collection('Unidentified').document(dt_str).set({
                    'Time':dt_str})

                newMessage = EmailMessage()
                newMessage['Subject'] = "Intruder Detected!"
                newMessage['From'] = SENDER_EMAIL
                newMessage['To'] = RECIEVER_EMAIL
                newMessage.set_content("Intruder Detected at " + str(dt))

                with open('Unchecked/' + imageName, 'rb') as f:
                    image_data = f.read()
                    image_type = imghdr.what(f.name)
                    image_name = "intruder"

                newMessage.add_attachment(image_data, maintype='image',
                                        subtype=image_type, filename=image_name)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(SENDER_EMAIL, PASSWORD)
                    smtp.send_message(newMessage)

        # delete image from storage
        image.delete()
        # delete local image
        os.remove("Unchecked/" + imageName)

    sleep(5)
    i += 1
