import cv2
import mediapipe as mp
import numpy as np

class VideoProcessor:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def process_video(self, video_path):
        """
        Process entire video and extract pose landmarks for each frame
        Returns: list of frame data with landmarks and metadata
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Processing video: {frame_count} frames at {fps} FPS")
        
        frames_data = []
        frame_number = 0
        
        while cap.isOpened():
            success, frame = cap.read()
            
            if not success:
                break
            
            frame_number += 1
            timestamp = frame_number / fps
            
            # Convert to RGB for MediaPipe
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.pose.process(image_rgb)
            
            # Store frame data
            frame_data = {
                'frame_number': frame_number,
                'timestamp': timestamp,
                'landmarks': None,
                'pose_detected': False
            }
            
            if results.pose_landmarks:
                frame_data['pose_detected'] = True
                frame_data['landmarks'] = self._extract_landmarks(results.pose_landmarks)
            
            frames_data.append(frame_data)
            
            # Progress indicator
            if frame_number % 30 == 0:
                print(f"Processed {frame_number}/{frame_count} frames...")
        
        cap.release()
        self.pose.close()
        
        print(f"Processing complete! {frame_number} frames processed.")
        
        return {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'frames': frames_data
        }
    
    def _extract_landmarks(self, pose_landmarks):
        """Extract key landmarks we need for swing analysis"""
        landmarks = {}
        
        # Key landmarks for tennis swing analysis
        landmark_indices = {
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_elbow': 13,
            'right_elbow': 14,
            'left_wrist': 15,
            'right_wrist': 16,
            'left_hip': 23,
            'right_hip': 24
        }
        
        for name, idx in landmark_indices.items():
            landmark = pose_landmarks.landmark[idx]
            landmarks[name] = {
                'x': landmark.x,
                'y': landmark.y,
                'z': landmark.z,
                'visibility': landmark.visibility
            }
        
        return landmarks


# Test the processor
if __name__ == "__main__":
    processor = VideoProcessor()
    video_path = "uploads/test_swing.mp4"
    
    result = processor.process_video(video_path)
    
    print(f"\nVideo Info:")
    print(f"  FPS: {result['fps']}")
    print(f"  Total frames: {result['frame_count']}")
    print(f"  Dimensions: {result['width']}x{result['height']}")
    
    # Check how many frames had pose detected
    detected_count = sum(1 for f in result['frames'] if f['pose_detected'])
    print(f"  Pose detected in: {detected_count}/{result['frame_count']} frames")
    
    # Show first frame with landmarks
    if result['frames'][0]['pose_detected']:
        print(f"\nFirst frame landmarks:")
        landmarks = result['frames'][0]['landmarks']
        print(f"  Right wrist: x={landmarks['right_wrist']['x']:.3f}, y={landmarks['right_wrist']['y']:.3f}")