import uuid
import boto3
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

face_collection_name = "AwesomeTransit"
reko_client = boto3.client('rekognition', region_name="ap-northeast-1")


@app.route("/upload_face", methods=["POST"])
def upload_face():
    image = request.files['file']
    name = request.form['name']

    result = reko_client.index_faces(
            CollectionId=face_collection_name,
            DetectionAttributes=["DEFAULT"],
            ExternalImageId=name,
            Image={'Bytes': image.read()})
    
    return jsonify(dict(reuslt=true))


@app.route('/find_face', methods=["POST"])
def find_face():
    image = request.files['file']

    result = reko_client.search_faces_by_image(
            CollectionId=face_collection_name,
            Image={'Bytes': image.read()},
            FaceMatchThreshold=90,
            MaxFaces=1)

    print(result)
    print(result.keys())

    return 'succeed'




if __name__ == "__main__":
    app.run()
