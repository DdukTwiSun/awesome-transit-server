import time
import uuid
import boto3
import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, db
import bcrypt
from boto3.s3.transfer import TransferConfig
from flask_cors import CORS

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://awesome-transit-ea77a.firebaseio.com"
})

app = Flask(__name__)
CORS(app)

face_collection_name = "AwesomeTransit"
s3_bucket_name = "awesome-transit-photo"
reko_client = boto3.client('rekognition', region_name="ap-northeast-1")
s3_client = boto3.client('s3')


@app.route("/signup", methods=["POST"])
def signup():
    photo = request.files['photo']
    email = request.form['email']
    password = request.form['password']
    uid = str(uuid.uuid4())
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf8'), salt)

    upload_config = TransferConfig(use_threads=False)

    image_name = uid + ".jpg"

    result = s3_client.upload_fileobj(
        photo,
        s3_bucket_name,
        image_name,
        ExtraArgs={
            "ACL": "public-read",
            "ContentType": photo.content_type
        },
        Config=upload_config)

    photo_url = "https://s3-ap-northeast-1.amazonaws.com/awesome-transit-photo/" + \
        image_name

    ref = db.reference().child('user').child(uid)
    ref.set({
        "photo_url": photo_url,
        "balance": 10000,
        "email": email
        })

    result = reko_client.index_faces(
            CollectionId=face_collection_name,
            DetectionAttributes=["DEFAULT"],
            ExternalImageId=uid,
            Image=dict(
                S3Object=dict(
                        Bucket=s3_bucket_name,
                        Name=image_name
                    )

            ))

    user = auth.ImportUserRecord(
        uid,
        email=email,
        photo_url=photo_url,
        password_hash=password_hash,
        password_salt=salt)

    result = auth.import_users([user], hash_alg=auth.UserImportHash.bcrypt())

    
    return jsonify(dict(reuslt=True))

    

@app.route("/")
def index():
    print(boto3.DEFAULT_SESSION)
    return jsonify(dict(
        session=str(boto3.DEFAULT_SESSION)
        ))

@app.route("/create_collection")
def create_collection():
    result = reko_client.create_collection(CollectionId=face_collection_name)
    return jsonify(result)

@app.route('/drop_faces')
def drop_faces():
    response = reko_client.list_faces(CollectionId=face_collection_name)
    print('list: ', response)

    face_ids = list(map(lambda x: x['FaceId'], response['Faces']))
    response = reko_client.delete_faces(CollectionId=face_collection_name,
            FaceIds=face_ids)
    print('delete: ', response)

    return jsonify(dict(result=True))


@app.route("/upload_face", methods=["POST"])
def upload_face():
    image = request.files['file']
    name = request.form['name']

    result = reko_client.index_faces(
            CollectionId=face_collection_name,
            DetectionAttributes=["DEFAULT"],
            ExternalImageId=name,
            Image={'Bytes': image.read()})
    
    return jsonify(dict(reuslt=True))


@app.route('/find_face', methods=["POST"])
def find_face():
    image = request.files['file']

    try:
        result = reko_client.search_faces_by_image(
                CollectionId=face_collection_name,
                Image={'Bytes': image.read()},
                FaceMatchThreshold=90,
                MaxFaces=4)
    except Exception as e:
        print(e)
        return jsonify(dict(name=None))


    if len(result['FaceMatches']) == 0:
        return jsonify(dict(name=None))
    else:
        name = result['FaceMatches'][0]['Face']['ExternalImageId']
        return jsonify(dict(name=name))


@app.route('/enter', methods=["POST"])
def enter():
    image = request.files['file']

    try:
        result = reko_client.search_faces_by_image(
                CollectionId=face_collection_name,
                Image={'Bytes': image.read()},
                FaceMatchThreshold=80,
                MaxFaces=4)
    except Exception as e:
        print(e)
        return jsonify(dict(result=False))


    last_enter_faces = db.reference().child('noti_leave').child('last_leave_faces').set([])
    last_enter_faces = db.reference().child('noti_enter').child('last_enter_faces').get()
    if last_enter_faces is None:
        last_enter_faces = []
    enter_faces = map(lambda x: x['Face']['ExternalImageId'], result['FaceMatches'])

    diff = list(set(enter_faces).difference(last_enter_faces))
    
    user_id = None
    if len(diff) == 1:
        user_id = diff[0]
    elif len(diff) > 1:
        user_id = diff[0]
        enter_faces = [user_id] + set(enter_faces).intersection(last_enter_faces)

    if user_id is None:
        return jsonify(user_id=None)


    timestamp = time.time()
    state = "enter"

    state = dict(
        user_id=user_id,
        timestamp=timestamp,
        state=state,
        payment=100,
        last_enter_faces=enter_faces)

    ref = db.reference().child('noti_enter')
    ref.set(state)

    return jsonify(state)


@app.route('/leave', methods=["POST"])
def leave():
    image = request.files['file']

    try:
        result = reko_client.search_faces_by_image(
                CollectionId=face_collection_name,
                Image={'Bytes': image.read()},
                FaceMatchThreshold=80,
                MaxFaces=1)
    except Exception as e:
        print(e)
        return jsonify(dict(result=False))


    last_enter_faces = db.reference().child('noti_enter').child('last_enter_faces').set([])
    last_leave_faces = db.reference().child('noti_leave').child('last_leave_faces').get()
    if last_leave_faces is None:
        last_leave_faces = []
    leave_faces = map(lambda x: x['Face']['ExternalImageId'], result['FaceMatches'])

    diff = list(set(leave_faces).difference(last_leave_faces))
    
    user_id = None
    if len(diff) == 1:
        user_id = diff[0]
    elif len(diff) > 1:
        user_id = diff[0]
        leave_faces = [user_id] + set(leave_faces).intersection(last_leave_faces)

    if user_id is None:
        return jsonify(user_id=None)

    timestamp = time.time()
    state = "leave"


    state = dict(
        user_id=user_id,
        timestamp=timestamp,
        state=state,
        payment=100,
        last_leave_faces=leave_faces)

    ref = db.reference().child('noti_leave')
    ref.set(state)

    return jsonify(state)


if __name__ == "__main__":
    app.run()
