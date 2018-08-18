import face_recognition
import cv2
import os
import requests
from multiprocessing import Pool

FRAME_SKIP = 1
RESIZE = 0.4
API_URL = "https://3putl16z3f.execute-api.ap-northeast-1.amazonaws.com/dev/"
NEW_FACE_DELAY_TICK = 4

video_capture = cv2.VideoCapture(0)
frame_skip_counter = 0
face_locations = None
face_count = 0
new_face_tick = -1
is_boarding_mode = True


def handle_new_face(frame):
    ret, buf = cv2.imencode('.jpg', frame)
    response = requests.post(API_URL + "find_face",
            files=dict(file=buf))
    body = response.json()
    print(body)

pool = Pool(processes=4)


while True:
    ret, frame = video_capture.read()

    if frame_skip_counter == 0:
        frame_skip_counter = FRAME_SKIP
        rgb_frame = cv2.resize(frame, (0, 0), fx=RESIZE, fy=RESIZE)[:, :, ::-1]
        face_locations = face_recognition.face_locations(
                rgb_frame)
        new_face_count = len(face_locations)
        
        if face_count < new_face_count:
            new_face_tick = NEW_FACE_DELAY_TICK

        face_count = new_face_count

    if new_face_tick == 0:
        pool.apply_async(handle_new_face, frame)
        new_face_tick = -1
    elif new_face_tick != -1:
        new_face_tick -= 1


    for loc in face_locations:
        (top, right, bottom, left) = map(lambda x: int(x / RESIZE),  loc)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

    if is_boarding_mode:
        mode = "Boarding Mode"
    else:
        mode = "Get Off Mode"

    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.rectangle(frame, (0, 0), (500, 80), (0, 0, 0), cv2.FILLED)
    cv2.putText(frame, mode, (0, 60), font, 2.0, (255, 255, 255), 1)

    cv2.imshow('Video', frame)
    
    frame_skip_counter -= 1

    key = cv2.waitKey(1)

    if key & 0xFF == ord('q'):
        break

    if key & 0xFF == ord('m'):
        is_boarding_mode = not is_boarding_mode

video_capture.release()
cv2.destroyAllWindows()
