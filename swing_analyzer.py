from utils import (
    calculate_angle,
    calculate_velocity,
    get_body_center_x,
    is_wrist_behind_body,
)


class SwingAnalyzer:
    def __init__(
        self,
        velocity_threshold=0.5,
        contact_angle_min=150,
        use_adaptive_velocity=False,
        adaptive_velocity_percent=0.15,
    ):
        """
        Initialize swing analyzer with configurable thresholds

        Args:
            velocity_threshold: Fixed minimum velocity for swing detection (default: 0.5)
            contact_angle_min: Minimum elbow extension angle at contact in degrees (default: 150)
            use_adaptive_velocity: If True, uses percentage of max velocity instead of fixed threshold
            adaptive_velocity_percent: Percentage of max velocity to use as threshold (default: 0.15 = 15%)
        """
        # Thresholds for phase detection
        self.BACKSWING_THRESHOLD = (
            0.05  # How far back wrist must go (not currently used)
        )
        self.CONTACT_ANGLE_MIN = contact_angle_min
        self.VELOCITY_THRESHOLD = velocity_threshold
        self.USE_ADAPTIVE_VELOCITY = use_adaptive_velocity
        self.ADAPTIVE_VELOCITY_PERCENT = adaptive_velocity_percent

        print("⚙️  Swing Analyzer Config:")
        print(f"   Velocity threshold: {self.VELOCITY_THRESHOLD}")
        print(f"   Contact angle min: {self.CONTACT_ANGLE_MIN}°")
        print(f"   Adaptive velocity: {self.USE_ADAPTIVE_VELOCITY}")
        if self.USE_ADAPTIVE_VELOCITY:
            print(f"   Adaptive percent: {self.ADAPTIVE_VELOCITY_PERCENT * 100:.0f}%")

    def analyze_swing(self, video_data):
        """
        Analyze swing phases from processed video data
        Returns dict with timestamps for each phase
        """
        frames = video_data["frames"]
        fps = video_data["fps"]

        # Filter to only frames with pose detected
        valid_frames = [f for f in frames if f["pose_detected"]]

        if len(valid_frames) < 10:
            return {
                "error": "Not enough frames with pose detected",
                "frames_detected": len(valid_frames),
            }

        print(f"Analyzing {len(valid_frames)} valid frames...")

        # Calculate metrics for each frame
        frame_metrics = self._calculate_frame_metrics(valid_frames, fps)

        # If using adaptive velocity, calculate it from the data
        velocity_threshold = self.VELOCITY_THRESHOLD
        if self.USE_ADAPTIVE_VELOCITY:
            velocities = [m["wrist_velocity"] for m in frame_metrics]
            max_velocity = max(velocities)
            velocity_threshold = max_velocity * self.ADAPTIVE_VELOCITY_PERCENT
            print("\n📊 Adaptive Velocity Analysis:")
            print(f"   Max velocity: {max_velocity:.4f}")
            print(
                f"   Calculated threshold: {velocity_threshold:.4f} ({self.ADAPTIVE_VELOCITY_PERCENT * 100:.0f}% of max)"
            )

        # Detect swing phases
        phases = self._detect_phases(frame_metrics, valid_frames, velocity_threshold)

        return phases

    def _calculate_frame_metrics(self, frames, fps):
        """Calculate angles and velocities for each frame"""
        metrics = []

        for i, frame in enumerate(frames):
            landmarks = frame["landmarks"]

            # Calculate elbow angle (shoulder-elbow-wrist)
            elbow_angle = calculate_angle(
                landmarks["right_shoulder"],
                landmarks["right_elbow"],
                landmarks["right_wrist"],
            )

            # Calculate wrist velocity (if not first frame)
            wrist_velocity = 0
            if i > 0:
                prev_wrist = frames[i - 1]["landmarks"]["right_wrist"]
                curr_wrist = landmarks["right_wrist"]
                time_delta = 1 / fps
                wrist_velocity = calculate_velocity(curr_wrist, prev_wrist, time_delta)

            # Check if wrist is behind body
            wrist_behind = is_wrist_behind_body(
                landmarks["right_wrist"],
                landmarks["left_shoulder"],
                landmarks["right_shoulder"],
            )

            # Get body center for reference
            body_center = get_body_center_x(
                landmarks["left_shoulder"], landmarks["right_shoulder"]
            )

            metrics.append(
                {
                    "frame_number": frame["frame_number"],
                    "timestamp": frame["timestamp"],
                    "elbow_angle": elbow_angle,
                    "wrist_velocity": wrist_velocity,
                    "wrist_x": landmarks["right_wrist"]["x"],
                    "wrist_behind_body": wrist_behind,
                    "body_center_x": body_center,
                }
            )

        return metrics

    def _detect_phases(self, metrics, frames, velocity_threshold):
        """Detect the swing phases based on calculated metrics"""

        # Initialize phase results
        phases = {
            "backswing_start": None,
            "max_backswing": None,
            "forward_swing_start": None,
            "contact": None,
            "follow_through": None,
        }

        # Find backswing start (wrist goes behind body)
        for i, m in enumerate(metrics):
            if m["wrist_behind_body"]:
                phases["backswing_start"] = {
                    "frame": m["frame_number"],
                    "timestamp": m["timestamp"],
                }
                break

        # Find max backswing (furthest back wrist position)
        if phases["backswing_start"]:
            backswing_frames = [m for m in metrics if m["wrist_behind_body"]]
            if backswing_frames:
                max_back = min(backswing_frames, key=lambda x: x["wrist_x"])
                phases["max_backswing"] = {
                    "frame": max_back["frame_number"],
                    "timestamp": max_back["timestamp"],
                    "wrist_x": max_back["wrist_x"],
                }

        # Find forward swing start (velocity increases after max backswing)
        if phases["max_backswing"]:
            max_back_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["max_backswing"]["frame"]
            )

            for i in range(max_back_idx, len(metrics)):
                if metrics[i]["wrist_velocity"] > velocity_threshold:
                    phases["forward_swing_start"] = {
                        "frame": metrics[i]["frame_number"],
                        "timestamp": metrics[i]["timestamp"],
                        "velocity": metrics[i]["wrist_velocity"],
                    }
                    break

        # Find contact point (occurs at PEAK velocity with extended arm)
        if phases["forward_swing_start"]:
            forward_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["forward_swing_start"]["frame"]
            )

            # Look ahead from forward swing start with larger window
            search_window_end = min(forward_idx + 40, len(metrics))

            # Find frames with good arm extension that are moving fast
            contact_candidates = []
            for i in range(forward_idx, search_window_end):
                m = metrics[i]
                if (
                    m["elbow_angle"] > self.CONTACT_ANGLE_MIN
                    and m["wrist_velocity"] > velocity_threshold
                    and not m["wrist_behind_body"]
                ):
                    contact_candidates.append(m)

            if contact_candidates:
                # Contact is at MAXIMUM velocity (peak of swing)
                contact = max(contact_candidates, key=lambda x: x["wrist_velocity"])

                # Adjust 3 frames forward (contact happens slightly after peak velocity)
                contact_idx = next(
                    i
                    for i, m in enumerate(metrics)
                    if m["frame_number"] == contact["frame_number"]
                )
                adjusted_idx = min(
                    len(metrics) - 1, contact_idx + 3
                )  # Go forward 3 frames
                adjusted_contact = metrics[adjusted_idx]

                phases["contact"] = {
                    "frame": adjusted_contact["frame_number"],
                    "timestamp": adjusted_contact["timestamp"],
                    "velocity": adjusted_contact["wrist_velocity"],
                    "elbow_angle": adjusted_contact["elbow_angle"],
                }

        # Find follow through (wrist crosses far past body center)
        if phases["contact"]:
            contact_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["contact"]["frame"]
            )

            for i in range(contact_idx, len(metrics)):
                m = metrics[i]
                # Wrist significantly past body center on opposite side
                if m["wrist_x"] > m["body_center_x"] + 0.15:
                    phases["follow_through"] = {
                        "frame": m["frame_number"],
                        "timestamp": m["timestamp"],
                        "wrist_x": m["wrist_x"],
                    }
                    break

        return phases


# Test the analyzer
if __name__ == "__main__":
    from video_processor import VideoProcessor

    # ========================================
    # CONFIGURATION - CHANGE THESE SETTINGS
    # ========================================

    # Choose your video
    VIDEO_PATH = "uploads/novak_swing.mp4"  # or "uploads/test_swing.mp4"

    # Method 1: Use fixed threshold (original method)
    # analyzer = SwingAnalyzer(velocity_threshold=0.5, contact_angle_min=150)

    # Method 2: Use adaptive threshold (recommended for different videos)
    analyzer = SwingAnalyzer(
        use_adaptive_velocity=True,
        adaptive_velocity_percent=0.15,  # 15% of max velocity
        contact_angle_min=120,  # Lowered from 150 for more relaxed detection
    )

    # ========================================

    print("Processing video...")
    processor = VideoProcessor()
    video_data = processor.process_video(VIDEO_PATH)

    print("\nAnalyzing swing phases...")
    phases = analyzer.analyze_swing(video_data)

    print("\n" + "=" * 60)
    print("SWING ANALYSIS RESULTS")
    print("=" * 60)
    for phase_name, phase_data in phases.items():
        if phase_data:
            print(f"\n{phase_name.upper().replace('_', ' ')}:")
            for key, value in phase_data.items():
                if key == "timestamp":
                    print(f"  {key}: {value:.3f}s")
                elif isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"\n{phase_name.upper().replace('_', ' ')}: Not detected")
