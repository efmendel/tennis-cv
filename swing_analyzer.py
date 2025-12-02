from utils import (
    calculate_angle,
    calculate_velocity,
    get_body_center_x,
    is_wrist_behind_body,
)


class SwingAnalyzerConfig:
    """
    Configuration class for swing phase detection.

    Attributes:
        velocity_threshold (float): Fixed minimum wrist velocity for swing detection
        contact_angle_min (int): Minimum elbow extension angle at contact (degrees)
        use_adaptive_velocity (bool): Use percentage of max velocity instead of fixed threshold
        adaptive_velocity_percent (float): Percentage of max velocity to use as threshold
        contact_frame_offset (int): Frames to adjust forward after peak velocity for contact
        follow_through_offset (float): Wrist position threshold past body center (normalized 0-1)
        forward_swing_search_window (int): Maximum frames to search for contact point
        min_valid_frames (int): Minimum frames with pose detected required for analysis
        wrist_behind_body_threshold (float): X-position threshold relative to body center
    """

    def __init__(
        self,
        velocity_threshold=0.5,
        contact_angle_min=150,
        use_adaptive_velocity=False,
        adaptive_velocity_percent=0.15,
        contact_frame_offset=3,
        follow_through_offset=0.15,
        forward_swing_search_window=40,
        min_valid_frames=10,
        wrist_behind_body_threshold=0.0,
    ):
        """
        Initialize swing analyzer configuration.

        Args:
            velocity_threshold: Fixed minimum wrist velocity for swing detection (default: 0.5)
                Higher values = require faster motion to detect swing
            contact_angle_min: Minimum elbow extension angle at contact in degrees (default: 150)
                Higher values = require straighter arm at contact
            use_adaptive_velocity: If True, uses percentage of max velocity instead of fixed threshold
                Recommended for videos with varying speeds
            adaptive_velocity_percent: Percentage of max velocity to use as threshold (default: 0.15 = 15%)
                Lower values = detect slower swings, higher values = only fast swings
            contact_frame_offset: Frames to adjust forward after detecting peak velocity (default: 3)
                Accounts for lag between velocity peak and actual contact
            follow_through_offset: Wrist X-position past body center to trigger follow-through (default: 0.15)
                Normalized coordinate offset (0.0-1.0 scale)
            forward_swing_search_window: Maximum frames to search ahead for contact point (default: 40)
                Larger window = more lenient search, smaller = stricter timing
            min_valid_frames: Minimum frames with pose detected required for analysis (default: 10)
                Videos with fewer valid frames will be rejected
            wrist_behind_body_threshold: X-position threshold relative to body center (default: 0.0)
                Currently unused, reserved for future backswing detection refinements
        """
        # Validate parameters
        if velocity_threshold < 0:
            raise ValueError("velocity_threshold must be non-negative")
        if not 0 <= contact_angle_min <= 180:
            raise ValueError("contact_angle_min must be between 0 and 180 degrees")
        if not 0.0 < adaptive_velocity_percent < 1.0:
            raise ValueError("adaptive_velocity_percent must be between 0.0 and 1.0")
        if contact_frame_offset < 0:
            raise ValueError("contact_frame_offset must be non-negative")
        if not 0.0 <= follow_through_offset <= 1.0:
            raise ValueError("follow_through_offset must be between 0.0 and 1.0")
        if forward_swing_search_window < 1:
            raise ValueError("forward_swing_search_window must be at least 1")
        if min_valid_frames < 1:
            raise ValueError("min_valid_frames must be at least 1")

        self.velocity_threshold = velocity_threshold
        self.contact_angle_min = contact_angle_min
        self.use_adaptive_velocity = use_adaptive_velocity
        self.adaptive_velocity_percent = adaptive_velocity_percent
        self.contact_frame_offset = contact_frame_offset
        self.follow_through_offset = follow_through_offset
        self.forward_swing_search_window = forward_swing_search_window
        self.min_valid_frames = min_valid_frames
        self.wrist_behind_body_threshold = wrist_behind_body_threshold

    def __repr__(self):
        return (
            f"SwingAnalyzerConfig("
            f"velocity_threshold={self.velocity_threshold}, "
            f"contact_angle_min={self.contact_angle_min}, "
            f"use_adaptive_velocity={self.use_adaptive_velocity}, "
            f"adaptive_velocity_percent={self.adaptive_velocity_percent}, "
            f"contact_frame_offset={self.contact_frame_offset}, "
            f"follow_through_offset={self.follow_through_offset}, "
            f"forward_swing_search_window={self.forward_swing_search_window}, "
            f"min_valid_frames={self.min_valid_frames})"
        )


# Preset configurations
PRESET_STANDARD = SwingAnalyzerConfig()

PRESET_SENSITIVE = SwingAnalyzerConfig(
    velocity_threshold=0.3,
    contact_angle_min=120,
    use_adaptive_velocity=True,
    adaptive_velocity_percent=0.10,
)

PRESET_STRICT = SwingAnalyzerConfig(
    velocity_threshold=0.7,
    contact_angle_min=160,
    contact_frame_offset=2,
)


class SwingAnalyzer:
    def __init__(self, config=None, **kwargs):
        """
        Initialize swing analyzer with configurable thresholds.

        Args:
            config (SwingAnalyzerConfig, optional): Configuration object.
                If None and kwargs provided, creates config from kwargs.
                If None and no kwargs, uses PRESET_STANDARD.
            **kwargs: Individual config parameters (for backward compatibility).
                Only used if config is None.

        Examples:
            # Using preset
            analyzer = SwingAnalyzer(config=PRESET_SENSITIVE)

            # Using custom config
            config = SwingAnalyzerConfig(velocity_threshold=0.6)
            analyzer = SwingAnalyzer(config=config)

            # Backward compatible (deprecated, but still works)
            analyzer = SwingAnalyzer(velocity_threshold=0.5, contact_angle_min=150)
        """
        # Handle config initialization
        if config is None:
            if kwargs:
                # Backward compatibility: create config from kwargs
                config = SwingAnalyzerConfig(**kwargs)
            else:
                # Use default preset
                config = PRESET_STANDARD

        self.config = config

        # Store config values as instance variables for easy access
        self.velocity_threshold = config.velocity_threshold
        self.contact_angle_min = config.contact_angle_min
        self.use_adaptive_velocity = config.use_adaptive_velocity
        self.adaptive_velocity_percent = config.adaptive_velocity_percent
        self.contact_frame_offset = config.contact_frame_offset
        self.follow_through_offset = config.follow_through_offset
        self.forward_swing_search_window = config.forward_swing_search_window
        self.min_valid_frames = config.min_valid_frames
        self.wrist_behind_body_threshold = config.wrist_behind_body_threshold

        # Print configuration
        print("⚙️  Swing Analyzer Config:")
        print(f"   Velocity threshold: {self.velocity_threshold}")
        print(f"   Contact angle min: {self.contact_angle_min}°")
        print(f"   Adaptive velocity: {self.use_adaptive_velocity}")
        if self.use_adaptive_velocity:
            print(f"   Adaptive percent: {self.adaptive_velocity_percent * 100:.0f}%")
        print(f"   Contact frame offset: {self.contact_frame_offset}")
        print(f"   Follow-through offset: {self.follow_through_offset}")
        print(f"   Search window: {self.forward_swing_search_window} frames")

    def analyze_swing(self, video_data):
        """
        Analyze swing phases from processed video data
        Returns dict with timestamps for each phase
        """
        frames = video_data["frames"]
        fps = video_data["fps"]

        # Filter to only frames with pose detected
        valid_frames = [f for f in frames if f["pose_detected"]]

        if len(valid_frames) < self.min_valid_frames:
            return {
                "error": f"Not enough frames with pose detected (need at least {self.min_valid_frames})",
                "frames_detected": len(valid_frames),
            }

        print(f"Analyzing {len(valid_frames)} valid frames...")

        # Calculate metrics for each frame
        frame_metrics = self._calculate_frame_metrics(valid_frames, fps)

        # If using adaptive velocity, calculate it from the data
        velocity_threshold = self.velocity_threshold
        if self.use_adaptive_velocity:
            velocities = [m["wrist_velocity"] for m in frame_metrics]
            max_velocity = max(velocities)
            velocity_threshold = max_velocity * self.adaptive_velocity_percent
            print("\n📊 Adaptive Velocity Analysis:")
            print(f"   Max velocity: {max_velocity:.4f}")
            print(
                f"   Calculated threshold: {velocity_threshold:.4f} ({self.adaptive_velocity_percent * 100:.0f}% of max)"
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

            # Look ahead from forward swing start with configurable search window
            search_window_end = min(
                forward_idx + self.forward_swing_search_window, len(metrics)
            )

            # Find frames with good arm extension that are moving fast
            contact_candidates = []
            for i in range(forward_idx, search_window_end):
                m = metrics[i]
                if (
                    m["elbow_angle"] > self.contact_angle_min
                    and m["wrist_velocity"] > velocity_threshold
                    and not m["wrist_behind_body"]
                ):
                    contact_candidates.append(m)

            if contact_candidates:
                # Contact is at MAXIMUM velocity (peak of swing)
                contact = max(contact_candidates, key=lambda x: x["wrist_velocity"])

                # Adjust forward by configured offset (contact happens slightly after peak velocity)
                contact_idx = next(
                    i
                    for i, m in enumerate(metrics)
                    if m["frame_number"] == contact["frame_number"]
                )
                adjusted_idx = min(
                    len(metrics) - 1, contact_idx + self.contact_frame_offset
                )
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
                # Wrist significantly past body center on opposite side (using configured offset)
                if m["wrist_x"] > m["body_center_x"] + self.follow_through_offset:
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
