import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()



def analyze_pushup(video_path):
    elbow_angles = []
    frame_count = 0
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            shoulder = np.array([landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y])
            elbow = np.array([landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y])
            wrist = np.array([landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y])

            # Calculate angle
            def calculate_angle(a, b, c):
                ba = a - b
                bc = c - b
                cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
                angle = np.arccos(cosine_angle)
                return np.degrees(angle)

            angle = calculate_angle(shoulder, elbow, wrist)
            elbow_angles.append(angle)
            print(f"Push-up angle: {angle:.2f} degrees")
        frame_count += 1

    cap.release()
    return elbow_angles


def detect_pushup_reps(angles, down_threshold=90, up_threshold=160):
    """
    Segments elbow angles into individual push-up reps.
    Returns a list of lists, where each inner list represents the angles for one rep.
    """
    pushup_reps = []  # List of push-up reps
    current_rep = []   # Store angles for the current rep
    going_down = False  # Track push-up movement state

    for angle in angles:
        current_rep.append(angle)  # Always store the angle

        if angle < down_threshold:  
            going_down = True  # Reached bottom
        elif angle > up_threshold and going_down:
            # A full push-up (down + up) is complete
            pushup_reps.append(current_rep)
            current_rep = []  # Reset for next rep
            going_down = False  

    return pushup_reps


def score_pushup(video_angles):
    """
    video_angles: List of lists, where each inner list contains elbow angles for one rep.
    Example: [[160, 140, 100, 80, 40, 80, 120, 160], [165, 130, 90, 45, 90, 130, 165], ...]
    """
    valid_reps = 0
    total_reps = len(video_angles)  # Total detected push-ups
    good_depth = 0
    good_lockout = 0
    jerky_movement = 0

    for rep in video_angles:
        min_angle, max_angle = min(rep), max(rep)  # Find lowest and highest elbow angles

        # Check depth (should go below 90°, ideally around 40°)
        if min_angle <= 90:
            good_depth += 1

        # Check full lockout (should extend close to 180°)
        if max_angle >= 170:
            good_lockout += 1

        # Detect jerky movement (angle changes > 30° between consecutive frames)
        for i in range(1, len(rep)):
            if abs(rep[i] - rep[i-1]) > 30:
                jerky_movement += 1

        valid_reps += 1  # Count all reps

    # Compute weighted score
    form_score = (valid_reps / total_reps) * 40
    form_score += (good_depth / total_reps) * 30
    form_score += (good_lockout / total_reps) * 20
    form_score -= (jerky_movement * 5)

    return max(0, min(100, form_score))  # Keep score between 0-100
