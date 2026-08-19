from collections import Counter

import av
import cv2
import mediapipe as mp
from streamlit_webrtc import VideoProcessorBase
from ultralytics import YOLO


# Tutor pattern: load YOLO, pass each frame to it, then use results[0].plot().
model = YOLO("yolo11n.pt")


class VideoAnalyzer:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.hands = mp.solutions.hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.drawing = mp.solutions.drawing_utils

    def detect_expression(self, landmarks):
        left_eye = abs(landmarks[159].y - landmarks[145].y)
        right_eye = abs(landmarks[386].y - landmarks[374].y)
        mouth_open = abs(landmarks[13].y - landmarks[14].y)
        mouth_width = abs(landmarks[61].x - landmarks[291].x)
        if mouth_open > 0.045:
            return "Mouth open"
        if left_eye < 0.012 and right_eye < 0.012:
            return "Blink / eyes closed"
        if mouth_width > 0.38:
            return "Smile"
        return "Neutral / focused"

    def detect_gesture(self, landmarks):
        fingers = []
        for tip, middle in [(8, 6), (12, 10), (16, 14), (20, 18)]:
            fingers.append(landmarks[tip].y < landmarks[middle].y)
        thumb_up = landmarks[4].y < landmarks[3].y and landmarks[4].y < landmarks[6].y
        if fingers == [True, True, True, True]:
            return "Open palm"
        if fingers == [True, True, False, False]:
            return "Peace sign"
        if fingers == [False, False, False, False] and thumb_up:
            return "Thumbs up"
        if fingers == [False, False, False, False]:
            return "Closed fist"
        return "Hand detected"

    def process(self, frame):
        frame = cv2.flip(frame, 1)

        # Same prediction and annotation style as the tutor's notebook.
        results = model(frame, classes=[0], verbose=False)
        annotated_frame = results[0].plot()
        person_detected = len(results[0].boxes) > 0

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)
        result = {"person_detected": person_detected, "face_detected": False, "expression": "No face detected", "gesture": "No hand detected"}

        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            result["face_detected"] = True
            result["expression"] = self.detect_expression(face_landmarks.landmark)
            self.drawing.draw_landmarks(annotated_frame, face_landmarks, mp.solutions.face_mesh.FACEMESH_CONTOURS, landmark_drawing_spec=None, connection_drawing_spec=mp.solutions.drawing_styles.get_default_face_mesh_contours_style())

        if hand_results.multi_hand_landmarks:
            gestures = []
            for hand_landmarks in hand_results.multi_hand_landmarks:
                gestures.append(self.detect_gesture(hand_landmarks.landmark))
                self.drawing.draw_landmarks(annotated_frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            result["gesture"] = ", ".join(gestures)

        cv2.rectangle(annotated_frame, (10, 10), (570, 108), (16, 42, 67), -1)
        cv2.putText(annotated_frame, "YOLO person: " + ("Detected" if person_detected else "Not detected"), (24, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (34, 211, 238), 2)
        cv2.putText(annotated_frame, "Expression: " + result["expression"], (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
        cv2.putText(annotated_frame, "Gesture: " + result["gesture"], (24, 98), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (167, 243, 208), 2)
        return annotated_frame, result


class LiveVideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.analyzer = VideoAnalyzer()
        self.last_result = None

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        checked_frame, self.last_result = self.analyzer.process(image)
        return av.VideoFrame.from_ndarray(checked_frame, format="bgr24")


def analyze_uploaded_video(video_path, output_path, max_frames=900):
    analyzer = VideoAnalyzer()
    capture = cv2.VideoCapture(video_path)
    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 20
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width > 720:
        new_width = 720
        new_height = int(height * new_width / width)
    else:
        new_width = width
        new_height = height
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (new_width, new_height))
    expressions = Counter()
    gestures = Counter()
    person_frames = 0
    face_frames = 0
    frame_count = 0

    while capture.isOpened() and frame_count < max_frames:
        success, frame = capture.read()
        if not success:
            break
        if frame.shape[1] != new_width:
            frame = cv2.resize(frame, (new_width, new_height))
        checked_frame, result = analyzer.process(frame)
        writer.write(checked_frame)
        expressions[result["expression"]] += 1
        gestures[result["gesture"]] += 1
        person_frames += int(result["person_detected"])
        face_frames += int(result["face_detected"])
        frame_count += 1

    capture.release()
    writer.release()
    person_percentage = round(person_frames / frame_count * 100) if frame_count else 0
    face_percentage = round(face_frames / frame_count * 100) if frame_count else 0
    main_expression = expressions.most_common(1)[0][0] if expressions else "Not detected"
    main_gesture = gestures.most_common(1)[0][0] if gestures else "Not detected"
    if face_percentage < 55:
        cue_level = "Camera position needs improvement"
    elif main_expression in ["Mouth open", "Blink / eyes closed"]:
        cue_level = "Some nervous cues"
    else:
        cue_level = "Calm visible delivery"
    cue_score = round(face_percentage * 0.6 + person_percentage * 0.4)
    return {"frames": frame_count, "person_percentage": person_percentage, "face_percentage": face_percentage, "main_expression": main_expression, "main_gesture": main_gesture, "cue_level": cue_level, "cue_score": cue_score}       
