import datetime
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials, firestore, storage, initialize_app
import numpy as np


cred = credentials.Certificate("credentials.json")
initialize_app(cred, {'storageBucket': 'iotproject-60e4c.appspot.com'})

firestore_db = firestore.client()

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


identifiedData = list() #list of times in seconds after midnight
identifiedCollection = list(firestore_db.collection('Identified').get()) 
for doc in identifiedCollection:
    timeStr = doc.to_dict()['Time']
    dt = datetime.datetime.fromisoformat(timeStr)
    h = dt.hour
    m = dt.minute
    s = dt.second
    t = h*60*60 + m*60 + s
    identifiedData.append(t)

unidentifiedData = list()
unidentifiedCollection = list(firestore_db.collection('Unidentified').get())
for doc in unidentifiedCollection:
    timeStr = doc.to_dict()['Time']
    dt = datetime.datetime.fromisoformat(timeStr)
    h = dt.hour
    m = dt.minute
    s = dt.second
    t = h*60*60 + m*60 + s
    unidentifiedData.append(t)

onesI = ['entry' for x in identifiedData]
onesU = ['intrusion' for x in unidentifiedData]
onesE = ['exit' for x in exitData]
plt.plot(identifiedData, onesI, '.')
plt.plot(exitData, onesE,'.')
plt.plot(unidentifiedData, onesU, '.')


i=0
for x,y in zip(unidentifiedData,onesU):

    label = unidentifiedCollection[i].to_dict()['Time']

    plt.annotate(label, # this is the text
                 (x,y), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=(0,0), # distance from text to points (x,y)
                 ha='center',
                 va='top',
                 rotation=90) # horizontal alignment can be left, right or center
    i += 1
plt.xlabel('Time of Day')

times = [3600*i for i in range(25)]
hours = [i for i in range(25)]
plt.xticks(times, hours)
plt.show()