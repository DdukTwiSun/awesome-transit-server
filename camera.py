import face_recognition
import cv2
import os
import requests

FRAME_SKIP = 1
RESIZE = 0.4
API_URL = "https://35z2j7wfmi.execute-api.ap-northeast-1.amazonaws.com/dev/"

video_capture = cv2.VideoCapture(0)
frame_skip_counter = 0
face_locations = None
face_count = 0


def handle_new_face(frame):
    ret, buf = cv2.imencode('.jpg', frame)
    response = requests.post(API_URL + "find_face",
            files=dict(file=buf))
    body = response.json()


while True:
    ret, frame = video_capture.read()

    if frame_skip_counter == 0:
        frame_skip_counter = FRAME_SKIP
        rgb_frame = cv2.resize(frame, (0, 0), fx=RESIZE, fy=RESIZE)[:, :, ::-1]
        face_locations = face_recognition.face_locations(
                rgb_frame)
        new_face_count = len(face_locations)
        
        if face_count < new_face_count:
            handle_new_face(frame)

        face_count = new_face_count


    for loc in face_locations:
        (top, right, bottom, left) = map(lambda x: int(x / RESIZE),  loc)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

    cv2.imshow('Video', frame)
    
    frame_skip_counter -= 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
