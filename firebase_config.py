import pyrebase

firebase_config = {
    "apiKey": "AIzaSyCrfnkOhn6G_2__qYugAE_yTXIX5BuMTT4",
    "authDomain": "gsheets-424112.firebaseapp.com",
    "databaseURL": "https://gsheets-424112-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "gsheets-424112",
    "storageBucket": "gsheets-424112.appspot.com",
    "messagingSenderId": "961500831744",
    "appId": "1:961500831744:web:bebb23e1ba8b8c167b78e5",
    "measurementId": "G-PS6Q92JV3Q"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()
