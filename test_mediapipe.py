import cv2
import mediapipe as mp

print("Testing MediaPipe Pose Detection...")
print(f"OpenCV version: {cv2.__version__}")

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Change this to your video filename
video_path = "uploads/test_swing.mp4"

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Could not open video file: {video_path}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Video loaded: {frame_count} frames at {fps} FPS")
print("Press 'q' to quit")

frame_number = 0

while True:
    success, frame = cap.read()
    
    if not success:
        print("End of video")
        break
    
    frame_number += 1
    
    # Convert BGR to RGB for MediaPipe
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process with MediaPipe
    results = pose.process(image_rgb)
    
    # Draw skeleton on frame if pose detected
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
        )
        
        # Print key landmarks for first 5 frames
        if frame_number <= 5:
            right_shoulder = results.pose_landmarks.landmark[12]
            right_elbow = results.pose_landmarks.landmark[14]
            right_wrist = results.pose_landmarks.landmark[16]
            print(f"\nFrame {frame_number}:")
            print(f"  Right Shoulder: ({right_shoulder.x:.3f}, {right_shoulder.y:.3f})")
            print(f"  Right Elbow: ({right_elbow.x:.3f}, {right_elbow.y:.3f})")
            print(f"  Right Wrist: ({right_wrist.x:.3f}, {right_wrist.y:.3f})")
    else:
        print(f"Frame {frame_number}: No pose detected")
    
    # Add frame info
    cv2.putText(frame, f"Frame: {frame_number}/{frame_count}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.imshow('MediaPipe Pose Detection - Press Q to quit', frame)
    
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pose.close()
print("\nTest complete!")