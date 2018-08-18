import boto3

face_collection_name = "AwesomeTransit"
reko_client = boto3.client('rekognition', region_name="ap-northeast-1")

response = reko_client.list_faces(CollectionId=face_collection_name)

print('list: ', response)
face_ids = list(map(lambda x: x['FaceId'], response['Faces']))
response = reko_client.delete_faces(CollectionId=face_collection_name,
        FaceIds=face_ids)

print('delete: ', response)

