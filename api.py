import uuid
import boto3
import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth
import bcrypt
from boto3.s3.transfer import TransferConfig

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)

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
                MaxFaces=1)
    except Exception as e:
        print(e)
        return jsonify(dict(name=None))


    if len(result['FaceMatches']) == 0:
        return jsonify(dict(name=None))
    else:
        name = result['FaceMatches'][0]['Face']['ExternalImageId']
        return jsonify(dict(name=name))




if __name__ == "__main__":
    app.run()
