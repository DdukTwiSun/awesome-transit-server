import face_recognition
import cv2


FRAME_SKIP = 1
RESIZE = 0.3

video_capture = cv2.VideoCapture(0)
frame_skip_counter = 0
face_locations = None

while True:
    ret, frame = video_capture.read()

    if frame_skip_counter == 0:
        rgb_frame = cv2.resize(frame, (0, 0), fx=RESIZE, fy=RESIZE)[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        frame_skip_counter = FRAME_SKIP

    for loc in face_locations:
        (top, right, bottom, left) = map(lambda x: int(x / RESIZE),  loc)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

    cv2.imshow('Video', frame)
    
    frame_skip_counter -= 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
