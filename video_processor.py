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

        # Build video data
        video_data = {
            'fps': fps,
            'frame_count': frame_count,
            'width': width,
            'height': height,
            'frames': frames_data
        }

        # Assess tracking quality
        tracking_quality = self.assess_tracking_quality(video_data)
        video_data['tracking_quality'] = tracking_quality

        # Print tracking quality summary
        print(f"\nTracking Quality Report:")
        print(f"  Detection rate: {tracking_quality['detection_rate']*100:.1f}%")
        print(f"  High confidence rate: {tracking_quality['high_confidence_rate']*100:.1f}%")
        print(f"  Average confidence: {tracking_quality['average_confidence']:.3f}")

        # Add warning if tracking quality is below threshold
        if tracking_quality['detection_rate'] < 0.7:
            print(f"  ⚠️  WARNING: Detection rate below 70% - video may not be suitable for analysis")

        return video_data
    
    def assess_tracking_quality(self, video_data):
        """
        Assess the quality of pose tracking across all frames.

        Args:
            video_data: Dictionary containing processed frame data

        Returns:
            dict: Tracking quality metrics including:
                - detection_rate: Percentage of frames with pose detected (0-1)
                - high_confidence_rate: Percentage of frames with avg confidence > 0.7 (0-1)
                - average_confidence: Mean confidence across all detected frames (0-1)
        """
        frames = video_data['frames']
        total_frames = len(frames)

        if total_frames == 0:
            return {
                'detection_rate': 0.0,
                'high_confidence_rate': 0.0,
                'average_confidence': 0.0
            }

        # Count frames with pose detected
        detected_frames = [f for f in frames if f['pose_detected']]
        detection_rate = len(detected_frames) / total_frames

        # Calculate confidence metrics for detected frames
        if not detected_frames:
            return {
                'detection_rate': 0.0,
                'high_confidence_rate': 0.0,
                'average_confidence': 0.0
            }

        # Calculate average visibility (confidence) for each frame
        frame_confidences = []
        high_confidence_frames = 0

        for frame in detected_frames:
            landmarks = frame['landmarks']
            if landmarks:
                # Get visibility scores for all landmarks
                visibilities = [lm['visibility'] for lm in landmarks.values()]
                avg_visibility = sum(visibilities) / len(visibilities)
                frame_confidences.append(avg_visibility)

                # Count frames with high confidence (>0.7)
                if avg_visibility > 0.7:
                    high_confidence_frames += 1

        # Calculate overall metrics
        average_confidence = sum(frame_confidences) / len(frame_confidences) if frame_confidences else 0.0
        high_confidence_rate = high_confidence_frames / total_frames

        return {
            'detection_rate': detection_rate,
            'high_confidence_rate': high_confidence_rate,
            'average_confidence': average_confidence
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