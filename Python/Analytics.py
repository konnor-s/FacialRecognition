import datetime
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials, firestore, storage, initialize_app
import numpy as np
from sklearn.cluster import MeanShift, estimate_bandwidth

x = [1,1,5,6,1,5,10,22,23,23,50,51,51,52,100,112,130,500,512,600,12000,12230]

X = np.array(list(zip(x,np.zeros(len(x)))))
bandwidth = estimate_bandwidth(X, quantile=.2)
ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
ms.fit(X)
labels = ms.labels_
cluster_centers = ms.cluster_centers_

labels_unique = np.unique(labels)
n_clusters_ = len(labels_unique)

for k in range(n_clusters_):
    my_members = labels == k
    print("cluster {0}: {1}".format(k, X[my_members, 0]))


cred = credentials.Certificate("credentials.json")
initialize_app(cred, {'storageBucket': 'iotproject-60e4c.appspot.com'})

firestore_db = firestore.client()


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

exitData = list()
exitCollection = list(firestore_db.collection('Exits').get())
for doc in exitCollection:
    timeStr = doc.to_dict()['Time']
    dt = datetime.datetime.fromisoformat(timeStr)
    h = dt.hour
    m = dt.minute
    s = dt.second
    t = h*60*60 + m*60 + s
    exitData.append(t)

onesI = ['entry' for x in identifiedData]
onesU = ['intrusion' for x in unidentifiedData]
onesE = ['exit' for x in exitData]
plt.plot(identifiedData, onesI, '.')
plt.plot(exitData, onesE)
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

plt.xlabel('Time of Day')

times = [3600*i for i in range(25)]
hours = [i for i in range(25)]
plt.xticks(times, hours)
plt.show()