import face_recognition
import cv2
import os


FRAME_SKIP = 1
RESIZE = 0.5

video_capture = cv2.VideoCapture(0)
frame_skip_counter = 0
face_locations = None
detected_face_names = []

known_face_encodings = []
known_face_names = []

for filename in os.listdir('./peoples'):
    name, ext = filename.split(".")
    fullpath = os.path.join('./peoples', filename)
    image = face_recognition.load_image_file(fullpath)
    encoding = face_recognition.face_encodings(image)[0]

    known_face_names.append(name)
    known_face_encodings.append(encoding)


while True:
    ret, frame = video_capture.read()

    if frame_skip_counter == 0:
        frame_skip_counter = FRAME_SKIP
        rgb_frame = cv2.resize(frame, (0, 0), fx=RESIZE, fy=RESIZE)[:, :, ::-1]
        face_locations = face_recognition.face_locations(
                rgb_frame)
        face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

        new_detected_face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(
                    known_face_encodings, face_encoding)


            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                new_detected_face_names.append(name)

        for face_name in new_detected_face_names:
            if face_name not in detected_face_names:
                print("{0} is detected", face_name)
        
        detected_face_names = new_detected_face_names


    for loc in face_locations:
        (top, right, bottom, left) = map(lambda x: int(x / RESIZE),  loc)

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

    cv2.imshow('Video', frame)
    
    frame_skip_counter -= 1

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
