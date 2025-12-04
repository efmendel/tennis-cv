from utils import (
    calculate_angle,
    calculate_velocity,
    get_body_center_x,
    is_wrist_behind_body,
)
from kinematic_chain_utils import (
    calculate_hip_rotation,
    calculate_shoulder_rotation,
    calculate_knee_bend,
    calculate_trunk_lean,
)
from analysis_results import SwingAnalysisResults


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
        kinematic_chain_mode (bool): Enable multi-joint kinematic chain analysis for phase detection
        contact_detection_method (str): Method for detecting contact point:
            'velocity_peak' - Traditional method using wrist velocity peak
            'kinematic_chain' - Biomechanical method using shoulder→elbow→wrist sequencing
            'hybrid' - Try both methods and use voting/best confidence
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
        kinematic_chain_mode=False,
        contact_detection_method='velocity_peak',
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
            kinematic_chain_mode: Enable multi-joint kinematic chain analysis (default: False)
                If True, uses hip rotation, shoulder rotation, and proximal-to-distal sequencing
                If False, uses traditional single-point wrist tracking (backward compatible)
            contact_detection_method: Method for detecting contact (default: 'velocity_peak')
                'velocity_peak' - Traditional wrist velocity peak detection
                'kinematic_chain' - Shoulder→elbow→wrist sequencing detection
                'hybrid' - Try both and use best confidence
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
        if not isinstance(kinematic_chain_mode, bool):
            raise ValueError("kinematic_chain_mode must be a boolean")
        if contact_detection_method not in ['velocity_peak', 'kinematic_chain', 'hybrid']:
            raise ValueError("contact_detection_method must be 'velocity_peak', 'kinematic_chain', or 'hybrid'")

        self.velocity_threshold = velocity_threshold
        self.contact_angle_min = contact_angle_min
        self.use_adaptive_velocity = use_adaptive_velocity
        self.adaptive_velocity_percent = adaptive_velocity_percent
        self.contact_frame_offset = contact_frame_offset
        self.follow_through_offset = follow_through_offset
        self.forward_swing_search_window = forward_swing_search_window
        self.min_valid_frames = min_valid_frames
        self.wrist_behind_body_threshold = wrist_behind_body_threshold
        self.kinematic_chain_mode = kinematic_chain_mode
        self.contact_detection_method = contact_detection_method

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
            f"min_valid_frames={self.min_valid_frames}, "
            f"kinematic_chain_mode={self.kinematic_chain_mode}, "
            f"contact_detection_method={self.contact_detection_method})"
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
        self.kinematic_chain_mode = config.kinematic_chain_mode
        self.contact_detection_method = config.contact_detection_method

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
        print(f"   Kinematic chain mode: {self.kinematic_chain_mode}")
        print(f"   Contact detection method: {self.contact_detection_method}")

    def analyze_swing(self, video_data):
        """
        Analyze swing phases from processed video data

        Returns:
            SwingAnalysisResults: Comprehensive analysis results object containing:
                - phases: All detected swing phases with metrics
                - engine: Hip-shoulder separation and rotation metrics
                - tempo: Timing and rhythm metrics
                - kinetic_chain: Velocity sequencing metrics
                - video_quality: Video quality assessment
                - tracking_quality: Pose tracking quality
        """
        frames = video_data["frames"]
        fps = video_data["fps"]

        # Create results object
        results = SwingAnalysisResults()

        # Set tracking quality from video_data
        if 'tracking_quality' in video_data:
            results.set_tracking_quality(video_data['tracking_quality'])

        # Filter to only frames with pose detected
        valid_frames = [f for f in frames if f["pose_detected"]]

        if len(valid_frames) < self.min_valid_frames:
            # Return empty results with error information
            print(f"❌ Error: Not enough frames with pose detected (need at least {self.min_valid_frames})")
            print(f"   Frames detected: {len(valid_frames)}")
            return results

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

        # Detect swing phases (legacy method returns dict)
        phases_dict = self._detect_phases(frame_metrics, valid_frames, velocity_threshold, self.kinematic_chain_mode)

        # Populate SwingAnalysisResults from phases_dict
        self._populate_results_from_phases(results, phases_dict, frame_metrics, fps)

        return results

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

            # ===== KINEMATIC CHAIN METRICS =====
            # Calculate kinematic chain angles
            hip_rotation = calculate_hip_rotation(landmarks)
            shoulder_rotation = calculate_shoulder_rotation(landmarks)
            knee_bend = calculate_knee_bend(landmarks, side='right')
            trunk_lean = calculate_trunk_lean(landmarks)

            # Calculate velocities for kinematic chain (if not first frame)
            hip_velocity = 0
            shoulder_velocity = 0
            elbow_velocity = 0
            if i > 0:
                prev_landmarks = frames[i - 1]["landmarks"]
                prev_hip_rotation = calculate_hip_rotation(prev_landmarks)
                prev_shoulder_rotation = calculate_shoulder_rotation(prev_landmarks)
                prev_elbow = prev_landmarks["right_elbow"]
                curr_elbow = landmarks["right_elbow"]

                time_delta = 1 / fps
                # Angular velocity = change in angle / time
                hip_velocity = abs(hip_rotation - prev_hip_rotation) / time_delta
                shoulder_velocity = abs(shoulder_rotation - prev_shoulder_rotation) / time_delta
                # Linear velocity for elbow (similar to wrist)
                elbow_velocity = calculate_velocity(curr_elbow, prev_elbow, time_delta)

            metrics.append(
                {
                    "frame_number": frame["frame_number"],
                    "timestamp": frame["timestamp"],
                    # Existing fields
                    "elbow_angle": elbow_angle,
                    "wrist_velocity": wrist_velocity,
                    "wrist_x": landmarks["right_wrist"]["x"],
                    "wrist_behind_body": wrist_behind,
                    "body_center_x": body_center,
                    # Kinematic chain fields
                    "hip_rotation": hip_rotation,
                    "shoulder_rotation": shoulder_rotation,
                    "knee_bend": knee_bend,
                    "trunk_lean": trunk_lean,
                    "hip_velocity": hip_velocity,
                    "shoulder_velocity": shoulder_velocity,
                    "elbow_velocity": elbow_velocity,
                }
            )

        return metrics

    def _detect_contact_kinematic_chain(self, metrics, forward_idx, velocity_threshold):
        """
        Detect contact using kinematic chain sequencing (shoulder→elbow→wrist).

        This method looks for the biomechanical signature of efficient contact:
        - Shoulder decelerating (proximal segment slowing)
        - Elbow at or near peak velocity (middle segment)
        - Wrist at peak velocity (distal segment - fastest)
        - Proper velocity sequencing: shoulder < elbow < wrist

        Args:
            metrics: List of frame metrics
            forward_idx: Index of forward swing start
            velocity_threshold: Velocity threshold for detection

        Returns:
            tuple: (contact_metric_dict or None, confidence_score)
        """
        search_window_end = min(forward_idx + self.forward_swing_search_window, len(metrics))
        contact_candidates = []

        for i in range(forward_idx + 1, search_window_end):
            m = metrics[i]

            # Check elbow at high velocity (middle of kinematic chain)
            elbow_high_velocity = m["elbow_velocity"] > velocity_threshold * 0.6  # Lowered from 0.8

            # Check wrist at peak velocity (distal end - fastest)
            wrist_peak_velocity = m["wrist_velocity"] > velocity_threshold

            # Check velocity sequencing: wrist should be fastest (most important)
            # This is the key kinematic chain principle: distal segment (wrist) moves faster than proximal (elbow)
            wrist_fastest = m["wrist_velocity"] > m["elbow_velocity"]

            # Arm should be extended at contact
            arm_extended = m["elbow_angle"] > self.contact_angle_min

            # Wrist should be in front of body
            wrist_in_front = not m["wrist_behind_body"]

            if elbow_high_velocity and wrist_peak_velocity and wrist_fastest and arm_extended and wrist_in_front:
                # Calculate sequencing quality score based on velocity gradient
                # Higher gradient (wrist much faster than elbow) = better kinematic chain
                velocity_gradient = m["wrist_velocity"] - m["elbow_velocity"]
                sequencing_quality = min(1.0, velocity_gradient / 0.5)  # Full score at 0.5 difference

                # Velocity ratios (how well does it follow shoulder < elbow < wrist)
                elbow_wrist_ratio = m["elbow_velocity"] / m["wrist_velocity"] if m["wrist_velocity"] > 0 else 0
                shoulder_elbow_ratio = m["shoulder_velocity"] / m["elbow_velocity"] if m["elbow_velocity"] > 0 else 0

                # Ideal ratios: shoulder ~ 0.5-0.7 * elbow, elbow ~ 0.6-0.8 * wrist
                ratio_score = (
                    (1.0 - abs(shoulder_elbow_ratio - 0.6)) +  # Penalize deviation from 0.6
                    (1.0 - abs(elbow_wrist_ratio - 0.7))      # Penalize deviation from 0.7
                ) / 2.0
                ratio_score = max(0.0, min(1.0, ratio_score))

                # Velocity score
                velocity_score = min(1.0, m["wrist_velocity"] / (velocity_threshold * 2))

                # Arm extension score
                angle_score = min(1.0, (m["elbow_angle"] - self.contact_angle_min) / 30.0)

                # Store scores in metric for evaluation
                m["sequencing_quality"] = sequencing_quality
                m["ratio_score"] = ratio_score
                m["velocity_score"] = velocity_score
                m["angle_score"] = angle_score
                m["shoulder_velocity_at_contact"] = m["shoulder_velocity"]
                m["elbow_velocity_at_contact"] = m["elbow_velocity"]

                contact_candidates.append(m)

        if not contact_candidates:
            return None, 0.0

        # Choose best candidate based on wrist velocity (contact occurs at peak)
        best_contact = max(contact_candidates, key=lambda x: x["wrist_velocity"])

        # Calculate overall confidence
        confidence = (
            best_contact["sequencing_quality"] +
            best_contact["ratio_score"] +
            best_contact["velocity_score"] +
            best_contact["angle_score"]
        ) / 4.0

        return best_contact, confidence

    def _detect_phases(self, metrics, frames, velocity_threshold, kinematic_chain_mode=False):
        """
        Detect the swing phases based on calculated metrics.

        Args:
            metrics: List of frame metrics with angles and velocities
            frames: List of valid frames with pose data
            velocity_threshold: Threshold for velocity-based detection
            kinematic_chain_mode: If True, use multi-joint kinematic chain criteria

        Returns detailed status for each phase including:
        - detected: bool indicating if phase was found
        - confidence: 0-1 score for detection quality
        - reason: explanation of success or failure
        - frame/timestamp/other metrics if detected
        """

        # Initialize phase results with default failure state
        phases = {
            "backswing_start": {
                "detected": False,
                "confidence": 0.0,
                "reason": "Not yet analyzed"
            },
            "max_backswing": {
                "detected": False,
                "confidence": 0.0,
                "reason": "Not yet analyzed"
            },
            "forward_swing_start": {
                "detected": False,
                "confidence": 0.0,
                "reason": "Not yet analyzed"
            },
            "contact": {
                "detected": False,
                "confidence": 0.0,
                "reason": "Not yet analyzed"
            },
            "follow_through": {
                "detected": False,
                "confidence": 0.0,
                "reason": "Not yet analyzed"
            },
        }

        # Find backswing start
        backswing_found = False

        if kinematic_chain_mode:
            # Kinematic chain mode: Look for hip and shoulder rotation indicating backswing
            for i, m in enumerate(metrics):
                # Check for combined rotation (both hips and shoulders rotating back)
                # Positive rotation indicates right side moving back (for right-handed player)
                hip_rotating = abs(m["hip_rotation"]) > 10  # At least 10 degrees rotation
                shoulder_rotating = abs(m["shoulder_rotation"]) > 15  # At least 15 degrees rotation

                if hip_rotating and shoulder_rotating and m["wrist_behind_body"]:
                    # Calculate confidence based on rotation magnitude and wrist position
                    wrist_offset = m["body_center_x"] - m["wrist_x"]
                    rotation_score = min(1.0, (abs(m["hip_rotation"]) + abs(m["shoulder_rotation"])) / 50)
                    wrist_score = min(1.0, wrist_offset / 0.1)
                    confidence = (rotation_score + wrist_score) / 2.0

                    phases["backswing_start"] = {
                        "detected": True,
                        "confidence": confidence,
                        "reason": "Successfully detected (kinematic chain)",
                        "frame": m["frame_number"],
                        "timestamp": m["timestamp"],
                        "wrist_offset": wrist_offset,
                        "hip_rotation": m["hip_rotation"],
                        "shoulder_rotation": m["shoulder_rotation"],
                        "rotation_score": rotation_score
                    }
                    backswing_found = True
                    break

            if not backswing_found:
                phases["backswing_start"]["reason"] = "insufficient_body_rotation"
        else:
            # Traditional mode: wrist goes behind body
            for i, m in enumerate(metrics):
                if m["wrist_behind_body"]:
                    # Calculate confidence based on how far behind body
                    wrist_offset = m["body_center_x"] - m["wrist_x"]
                    confidence = min(1.0, wrist_offset / 0.1)  # Full confidence at 0.1 offset

                    phases["backswing_start"] = {
                        "detected": True,
                        "confidence": confidence,
                        "reason": "Successfully detected",
                        "frame": m["frame_number"],
                        "timestamp": m["timestamp"],
                        "wrist_offset": wrist_offset
                    }
                    backswing_found = True
                    break

            if not backswing_found:
                phases["backswing_start"]["reason"] = "wrist_never_behind_body"

        # Find max backswing (furthest back wrist position)
        if phases["backswing_start"]["detected"]:
            backswing_frames = [m for m in metrics if m["wrist_behind_body"]]
            if backswing_frames:
                max_back = min(backswing_frames, key=lambda x: x["wrist_x"])

                # Calculate confidence based on backswing depth
                backswing_depth = max_back["body_center_x"] - max_back["wrist_x"]
                confidence = min(1.0, backswing_depth / 0.15)  # Full confidence at 0.15 depth

                phases["max_backswing"] = {
                    "detected": True,
                    "confidence": confidence,
                    "reason": "Successfully detected",
                    "frame": max_back["frame_number"],
                    "timestamp": max_back["timestamp"],
                    "wrist_x": max_back["wrist_x"],
                    "backswing_depth": backswing_depth
                }
            else:
                phases["max_backswing"]["reason"] = "no_backswing_frames_found"
        else:
            phases["max_backswing"]["reason"] = "backswing_start_not_detected"

        # Find forward swing start
        if phases["max_backswing"]["detected"]:
            max_back_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["max_backswing"]["frame"]
            )

            forward_found = False

            if kinematic_chain_mode:
                # Kinematic chain mode: Look for hip velocity reversal (proximal initiation)
                # The forward swing should start with hips accelerating forward
                for i in range(max_back_idx, len(metrics)):
                    m = metrics[i]
                    # Hip velocity reversal indicates forward swing initiation
                    if m["hip_velocity"] > 30 and m["wrist_velocity"] > velocity_threshold * 0.5:
                        # Calculate confidence based on hip velocity and wrist velocity
                        hip_vel_score = min(1.0, m["hip_velocity"] / 60)
                        wrist_vel_score = min(1.0, m["wrist_velocity"] / velocity_threshold)
                        confidence = (hip_vel_score + wrist_vel_score) / 2.0

                        phases["forward_swing_start"] = {
                            "detected": True,
                            "confidence": confidence,
                            "reason": "Successfully detected (kinematic chain)",
                            "frame": m["frame_number"],
                            "timestamp": m["timestamp"],
                            "velocity": m["wrist_velocity"],
                            "hip_velocity": m["hip_velocity"],
                            "shoulder_velocity": m["shoulder_velocity"],
                            "hip_vel_score": hip_vel_score
                        }
                        forward_found = True
                        break

                if not forward_found:
                    phases["forward_swing_start"]["reason"] = "no_hip_velocity_reversal"
            else:
                # Traditional mode: velocity increases after max backswing
                for i in range(max_back_idx, len(metrics)):
                    if metrics[i]["wrist_velocity"] > velocity_threshold:
                        # Calculate confidence based on velocity relative to threshold
                        velocity_ratio = metrics[i]["wrist_velocity"] / velocity_threshold
                        confidence = min(1.0, (velocity_ratio - 1.0) / 2.0 + 0.5)  # 0.5-1.0 range

                        phases["forward_swing_start"] = {
                            "detected": True,
                            "confidence": confidence,
                            "reason": "Successfully detected",
                            "frame": metrics[i]["frame_number"],
                            "timestamp": metrics[i]["timestamp"],
                            "velocity": metrics[i]["wrist_velocity"],
                            "velocity_ratio": velocity_ratio
                        }
                        forward_found = True
                        break

                if not forward_found:
                    phases["forward_swing_start"]["reason"] = "insufficient_velocity"
        else:
            phases["forward_swing_start"]["reason"] = "max_backswing_not_detected"

        # Find contact point
        if phases["forward_swing_start"]["detected"]:
            forward_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["forward_swing_start"]["frame"]
            )

            # Determine which contact detection method to use
            detection_method = self.contact_detection_method

            # Use contact detection method
            if detection_method == 'kinematic_chain':
                # Use new kinematic chain method (shoulder→elbow→wrist sequencing)
                contact_result, confidence = self._detect_contact_kinematic_chain(
                    metrics, forward_idx, velocity_threshold
                )

                if contact_result:
                    # Adjust forward by configured offset
                    contact_idx = next(
                        i
                        for i, m in enumerate(metrics)
                        if m["frame_number"] == contact_result["frame_number"]
                    )
                    adjusted_idx = min(
                        len(metrics) - 1, contact_idx + self.contact_frame_offset
                    )
                    adjusted_contact = metrics[adjusted_idx]

                    phases["contact"] = {
                        "detected": True,
                        "confidence": confidence,
                        "reason": "Successfully detected",
                        "method": "kinematic_chain",
                        "frame": adjusted_contact["frame_number"],
                        "timestamp": adjusted_contact["timestamp"],
                        "velocity": adjusted_contact["wrist_velocity"],
                        "elbow_angle": adjusted_contact["elbow_angle"],
                        "shoulder_velocity": contact_result.get("shoulder_velocity_at_contact", 0),
                        "elbow_velocity": contact_result.get("elbow_velocity_at_contact", 0),
                        "sequencing_quality": contact_result.get("sequencing_quality", 0),
                        "ratio_score": contact_result.get("ratio_score", 0),
                        "velocity_score": contact_result.get("velocity_score", 0),
                        "angle_score": contact_result.get("angle_score", 0)
                    }
                else:
                    phases["contact"]["reason"] = "no_kinematic_chain_signature_found"
                    phases["contact"]["method"] = "kinematic_chain"

            elif detection_method == 'hybrid':
                # Try both methods and use best confidence
                kc_result, kc_confidence = self._detect_contact_kinematic_chain(
                    metrics, forward_idx, velocity_threshold
                )

                # Also try velocity peak method
                search_window_end = min(
                    forward_idx + self.forward_swing_search_window, len(metrics)
                )
                vp_candidates = []
                for i in range(forward_idx, search_window_end):
                    m = metrics[i]
                    if (
                        m["elbow_angle"] > self.contact_angle_min
                        and m["wrist_velocity"] > velocity_threshold
                        and not m["wrist_behind_body"]
                    ):
                        vp_candidates.append(m)

                vp_result = None
                vp_confidence = 0.0
                if vp_candidates:
                    vp_contact = max(vp_candidates, key=lambda x: x["wrist_velocity"])
                    velocity_score = min(1.0, vp_contact["wrist_velocity"] / (velocity_threshold * 2))
                    angle_score = min(1.0, (vp_contact["elbow_angle"] - self.contact_angle_min) / 30.0)
                    vp_confidence = (velocity_score + angle_score) / 2.0
                    vp_result = vp_contact

                # Choose method with higher confidence
                if kc_confidence >= vp_confidence and kc_result:
                    # Use kinematic chain result
                    contact_idx = next(
                        i
                        for i, m in enumerate(metrics)
                        if m["frame_number"] == kc_result["frame_number"]
                    )
                    adjusted_idx = min(
                        len(metrics) - 1, contact_idx + self.contact_frame_offset
                    )
                    adjusted_contact = metrics[adjusted_idx]

                    phases["contact"] = {
                        "detected": True,
                        "confidence": kc_confidence,
                        "reason": "Successfully detected",
                        "method": "hybrid (used kinematic_chain)",
                        "frame": adjusted_contact["frame_number"],
                        "timestamp": adjusted_contact["timestamp"],
                        "velocity": adjusted_contact["wrist_velocity"],
                        "elbow_angle": adjusted_contact["elbow_angle"],
                        "shoulder_velocity": kc_result.get("shoulder_velocity_at_contact", 0),
                        "elbow_velocity": kc_result.get("elbow_velocity_at_contact", 0),
                        "sequencing_quality": kc_result.get("sequencing_quality", 0)
                    }
                elif vp_result:
                    # Use velocity peak result
                    contact_idx = next(
                        i
                        for i, m in enumerate(metrics)
                        if m["frame_number"] == vp_result["frame_number"]
                    )
                    adjusted_idx = min(
                        len(metrics) - 1, contact_idx + self.contact_frame_offset
                    )
                    adjusted_contact = metrics[adjusted_idx]

                    velocity_score = min(1.0, adjusted_contact["wrist_velocity"] / (velocity_threshold * 2))
                    angle_score = min(1.0, (adjusted_contact["elbow_angle"] - self.contact_angle_min) / 30.0)

                    phases["contact"] = {
                        "detected": True,
                        "confidence": (velocity_score + angle_score) / 2.0,
                        "reason": "Successfully detected",
                        "method": "hybrid (used velocity_peak)",
                        "frame": adjusted_contact["frame_number"],
                        "timestamp": adjusted_contact["timestamp"],
                        "velocity": adjusted_contact["wrist_velocity"],
                        "elbow_angle": adjusted_contact["elbow_angle"],
                        "velocity_score": velocity_score,
                        "angle_score": angle_score
                    }
                else:
                    phases["contact"]["reason"] = "no_contact_detected_by_any_method"
                    phases["contact"]["method"] = "hybrid"

            else:  # velocity_peak (default)
                # Look ahead from forward swing start with configurable search window
                search_window_end = min(
                    forward_idx + self.forward_swing_search_window, len(metrics)
                )

                contact_candidates = []

                # Traditional mode: Find frames with good arm extension that are moving fast
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

                    # Calculate confidence based on velocity and arm extension
                    velocity_score = min(1.0, adjusted_contact["wrist_velocity"] / (velocity_threshold * 2))
                    angle_score = min(1.0, (adjusted_contact["elbow_angle"] - self.contact_angle_min) / 30.0)
                    confidence = (velocity_score + angle_score) / 2.0

                    phases["contact"] = {
                        "detected": True,
                        "confidence": confidence,
                        "reason": "Successfully detected",
                        "method": "velocity_peak",
                        "frame": adjusted_contact["frame_number"],
                        "timestamp": adjusted_contact["timestamp"],
                        "velocity": adjusted_contact["wrist_velocity"],
                        "elbow_angle": adjusted_contact["elbow_angle"],
                        "velocity_score": velocity_score,
                        "angle_score": angle_score
                    }
                else:
                    # Determine specific failure reason
                    no_velocity = all(
                        m["wrist_velocity"] <= velocity_threshold
                        for m in metrics[forward_idx:search_window_end]
                    )
                    no_extension = all(
                        m["elbow_angle"] <= self.contact_angle_min
                        for m in metrics[forward_idx:search_window_end]
                    )

                    if no_velocity and no_extension:
                        phases["contact"]["reason"] = "insufficient_velocity_and_arm_not_extended"
                    elif no_velocity:
                        phases["contact"]["reason"] = "insufficient_velocity"
                    elif no_extension:
                        phases["contact"]["reason"] = "arm_not_extended"
                    else:
                        phases["contact"]["reason"] = "wrist_position_unclear"
                    phases["contact"]["method"] = "velocity_peak"

        else:
            phases["contact"]["reason"] = "forward_swing_start_not_detected"
            phases["contact"]["method"] = self.contact_detection_method

        # Find follow through (wrist crosses far past body center)
        if phases["contact"]["detected"]:
            contact_idx = next(
                i
                for i, m in enumerate(metrics)
                if m["frame_number"] == phases["contact"]["frame"]
            )

            follow_found = False
            for i in range(contact_idx, len(metrics)):
                m = metrics[i]
                # Wrist significantly past body center on opposite side (using configured offset)
                if m["wrist_x"] > m["body_center_x"] + self.follow_through_offset:
                    # Calculate confidence based on how far past body center
                    follow_distance = m["wrist_x"] - m["body_center_x"]
                    confidence = min(1.0, follow_distance / 0.3)  # Full confidence at 0.3 distance

                    phases["follow_through"] = {
                        "detected": True,
                        "confidence": confidence,
                        "reason": "Successfully detected",
                        "frame": m["frame_number"],
                        "timestamp": m["timestamp"],
                        "wrist_x": m["wrist_x"],
                        "follow_distance": follow_distance
                    }
                    follow_found = True
                    break

            if not follow_found:
                phases["follow_through"]["reason"] = "wrist_never_crossed_body_center"
        else:
            phases["follow_through"]["reason"] = "contact_not_detected"

        # Calculate overall analysis quality score
        detected_count = sum(1 for p in phases.values() if p["detected"])
        total_phases = len(phases)
        avg_confidence = sum(p["confidence"] for p in phases.values()) / total_phases

        phases["_analysis_quality"] = {
            "overall_score": avg_confidence,
            "phases_detected": detected_count,
            "total_phases": total_phases,
            "detection_rate": detected_count / total_phases
        }

        return phases

    def _populate_results_from_phases(self, results, phases_dict, frame_metrics, fps):
        """
        Populate SwingAnalysisResults object from legacy phases dict.

        This method converts the old dict-based phase detection results into
        the new SwingAnalysisResults structure with comprehensive metrics.

        Args:
            results: SwingAnalysisResults object to populate
            phases_dict: Legacy dict with phase detection results
            frame_metrics: List of frame metrics (for calculating engine/tempo/kinetic chain)
            fps: Video frames per second
        """
        # Map old phase names to new phase names
        phase_mapping = {
            'backswing_start': 'unit_turn',
            'max_backswing': 'backswing',
            'forward_swing_start': 'forward_swing',
            'contact': 'contact',
            'follow_through': 'follow_through'
        }

        # Add all phases to results
        for old_name, new_name in phase_mapping.items():
            if old_name in phases_dict:
                phase_data = phases_dict[old_name]

                # Extract base fields
                detected = phase_data.get('detected', False)
                frame = phase_data.get('frame')
                timestamp = phase_data.get('timestamp')
                confidence = phase_data.get('confidence', 0.0)

                # Add phase-specific metrics
                phase_metrics = {}

                if new_name == 'unit_turn' and detected:
                    # Add shoulder rotation for unit turn
                    phase_metrics['shoulder_rotation'] = phase_data.get('shoulder_rotation', 0.0)

                elif new_name == 'backswing' and detected:
                    # Add max wrist depth and shoulder rotation for backswing
                    phase_metrics['shoulder_rotation'] = phase_data.get('shoulder_rotation', 0.0)
                    # Calculate max wrist depth (normalized wrist-x position relative to body)
                    if frame:
                        metric = next((m for m in frame_metrics if m['frame_number'] == frame), None)
                        if metric:
                            # Max depth = how far back wrist is (lower x = more back)
                            phase_metrics['max_wrist_depth'] = 1.0 - metric.get('wrist_x', 0.5)

                elif new_name == 'forward_swing' and detected:
                    # Add hip velocity for forward swing
                    phase_metrics['hip_velocity'] = phase_data.get('hip_velocity', 0.0)

                elif new_name == 'contact' and detected:
                    # Add wrist velocity and elbow angle for contact
                    phase_metrics['wrist_velocity'] = phase_data.get('velocity', 0.0)
                    phase_metrics['elbow_angle'] = phase_data.get('elbow_angle', 0.0)
                    phase_metrics['method'] = phase_data.get('method', 'unknown')
                    # Add kinematic chain metrics if available
                    if 'shoulder_velocity' in phase_data:
                        phase_metrics['shoulder_velocity'] = phase_data['shoulder_velocity']
                    if 'elbow_velocity' in phase_data:
                        phase_metrics['elbow_velocity'] = phase_data['elbow_velocity']
                    if 'sequencing_quality' in phase_data:
                        phase_metrics['sequencing_quality'] = phase_data['sequencing_quality']

                # Add the phase
                results.add_phase(
                    new_name,
                    detected=detected,
                    frame=frame,
                    timestamp=timestamp,
                    confidence=confidence,
                    **phase_metrics
                )

        # Calculate and add engine metrics
        self._calculate_engine_metrics(results, frame_metrics)

        # Calculate and add tempo metrics
        self._calculate_tempo_metrics(results, phases_dict)

        # Calculate and add kinetic chain metrics
        self._calculate_kinetic_chain_metrics(results, frame_metrics, phases_dict)

    def _calculate_engine_metrics(self, results, frame_metrics):
        """
        Calculate engine metrics (hip-shoulder separation, rotations).

        Args:
            results: SwingAnalysisResults object to populate
            frame_metrics: List of frame metrics
        """
        if not frame_metrics:
            return

        # Find maximum hip-shoulder separation
        max_separation = 0.0
        max_sep_frame = None
        max_sep_timestamp = None

        # Find maximum shoulder rotation (most backward)
        max_shoulder_rot = 0.0
        max_shoulder_frame = None
        max_shoulder_timestamp = None

        # Find maximum hip rotation (most backward)
        max_hip_rot = 0.0
        max_hip_frame = None
        max_hip_timestamp = None

        for metric in frame_metrics:
            hip_rot = metric.get('hip_rotation', 0.0)
            shoulder_rot = metric.get('shoulder_rotation', 0.0)
            separation = abs(shoulder_rot - hip_rot)

            # Track max separation
            if separation > max_separation:
                max_separation = separation
                max_sep_frame = metric['frame_number']
                max_sep_timestamp = metric['timestamp']

            # Track max shoulder rotation (most negative = most backward)
            if shoulder_rot < max_shoulder_rot:
                max_shoulder_rot = shoulder_rot
                max_shoulder_frame = metric['frame_number']
                max_shoulder_timestamp = metric['timestamp']

            # Track max hip rotation (most negative = most backward)
            if hip_rot < max_hip_rot:
                max_hip_rot = hip_rot
                max_hip_frame = metric['frame_number']
                max_hip_timestamp = metric['timestamp']

        # Add engine metrics
        results.add_engine_metrics(
            hip_shoulder_sep={
                'max_value': max_separation,
                'frame': max_sep_frame,
                'timestamp': max_sep_timestamp
            },
            max_shoulder_rot={
                'value': max_shoulder_rot,
                'frame': max_shoulder_frame,
                'timestamp': max_shoulder_timestamp
            },
            max_hip_rot={
                'value': max_hip_rot,
                'frame': max_hip_frame,
                'timestamp': max_hip_timestamp
            }
        )

    def _calculate_tempo_metrics(self, results, phases_dict):
        """
        Calculate tempo metrics (durations, rhythm ratio).

        Args:
            results: SwingAnalysisResults object to populate
            phases_dict: Legacy dict with phase detection results
        """
        # Get phase timestamps
        unit_turn_ts = None
        forward_swing_ts = None
        contact_ts = None

        if 'backswing_start' in phases_dict and phases_dict['backswing_start'].get('detected'):
            unit_turn_ts = phases_dict['backswing_start'].get('timestamp')

        if 'forward_swing_start' in phases_dict and phases_dict['forward_swing_start'].get('detected'):
            forward_swing_ts = phases_dict['forward_swing_start'].get('timestamp')

        if 'contact' in phases_dict and phases_dict['contact'].get('detected'):
            contact_ts = phases_dict['contact'].get('timestamp')

        # Calculate durations
        backswing_duration = None
        forward_swing_duration = None
        swing_rhythm_ratio = None

        if unit_turn_ts is not None and forward_swing_ts is not None:
            backswing_duration = forward_swing_ts - unit_turn_ts

        if forward_swing_ts is not None and contact_ts is not None:
            forward_swing_duration = contact_ts - forward_swing_ts

        if backswing_duration and forward_swing_duration and forward_swing_duration > 0:
            swing_rhythm_ratio = backswing_duration / forward_swing_duration

        # Add tempo metrics
        results.add_tempo_metrics(
            backswing_duration=backswing_duration,
            forward_swing_duration=forward_swing_duration,
            swing_rhythm_ratio=swing_rhythm_ratio
        )

    def _calculate_kinetic_chain_metrics(self, results, frame_metrics, phases_dict):
        """
        Calculate kinetic chain metrics (velocity sequencing, lag times).

        Args:
            results: SwingAnalysisResults object to populate
            frame_metrics: List of frame metrics
            phases_dict: Legacy dict with phase detection results
        """
        if not frame_metrics:
            return

        # Find peak velocities for each segment
        max_hip_vel = 0.0
        max_hip_frame = None
        max_hip_ts = None

        max_shoulder_vel = 0.0
        max_shoulder_frame = None
        max_shoulder_ts = None

        max_elbow_vel = 0.0
        max_elbow_frame = None
        max_elbow_ts = None

        max_wrist_vel = 0.0
        max_wrist_frame = None
        max_wrist_ts = None

        for metric in frame_metrics:
            hip_vel = metric.get('hip_velocity', 0.0)
            shoulder_vel = metric.get('shoulder_velocity', 0.0)
            elbow_vel = metric.get('elbow_velocity', 0.0)
            wrist_vel = metric.get('wrist_velocity', 0.0)

            if hip_vel > max_hip_vel:
                max_hip_vel = hip_vel
                max_hip_frame = metric['frame_number']
                max_hip_ts = metric['timestamp']

            if shoulder_vel > max_shoulder_vel:
                max_shoulder_vel = shoulder_vel
                max_shoulder_frame = metric['frame_number']
                max_shoulder_ts = metric['timestamp']

            if elbow_vel > max_elbow_vel:
                max_elbow_vel = elbow_vel
                max_elbow_frame = metric['frame_number']
                max_elbow_ts = metric['timestamp']

            if wrist_vel > max_wrist_vel:
                max_wrist_vel = wrist_vel
                max_wrist_frame = metric['frame_number']
                max_wrist_ts = metric['timestamp']

        # Build sequence dict
        sequence = {
            'hip': {'frame': max_hip_frame, 'timestamp': max_hip_ts, 'velocity': max_hip_vel},
            'shoulder': {'frame': max_shoulder_frame, 'timestamp': max_shoulder_ts, 'velocity': max_shoulder_vel},
            'elbow': {'frame': max_elbow_frame, 'timestamp': max_elbow_ts, 'velocity': max_elbow_vel},
            'wrist': {'frame': max_wrist_frame, 'timestamp': max_wrist_ts, 'velocity': max_wrist_vel}
        }

        # Calculate lag times (time between peak velocities)
        chain_lag = {}
        if max_hip_ts is not None and max_shoulder_ts is not None:
            chain_lag['hip_to_shoulder'] = max_shoulder_ts - max_hip_ts
        if max_shoulder_ts is not None and max_elbow_ts is not None:
            chain_lag['shoulder_to_elbow'] = max_elbow_ts - max_shoulder_ts
        if max_elbow_ts is not None and max_wrist_ts is not None:
            chain_lag['elbow_to_wrist'] = max_wrist_ts - max_elbow_ts

        # Calculate confidence based on proper sequencing
        # Proper sequence: hip peaks first, then shoulder, then elbow, then wrist
        confidence = 0.0
        if all([max_hip_ts, max_shoulder_ts, max_elbow_ts, max_wrist_ts]):
            # Check if sequence is correct
            correct_sequence = (
                max_hip_ts <= max_shoulder_ts <= max_elbow_ts <= max_wrist_ts
            )
            if correct_sequence:
                confidence = 1.0
            else:
                # Partial credit for partial correct ordering
                correct_pairs = 0
                total_pairs = 3
                if max_hip_ts <= max_shoulder_ts:
                    correct_pairs += 1
                if max_shoulder_ts <= max_elbow_ts:
                    correct_pairs += 1
                if max_elbow_ts <= max_wrist_ts:
                    correct_pairs += 1
                confidence = correct_pairs / total_pairs

        # Add kinetic chain metrics
        results.add_kinetic_chain_metrics(
            sequence=sequence,
            chain_lag=chain_lag,
            confidence=confidence
        )


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
    # analyzer = SwingAnalyzer(
    #     use_adaptive_velocity=True,
    #     adaptive_velocity_percent=0.15,  # 15% of max velocity
    #     contact_angle_min=120,  # Lowered from 150 for more relaxed detection
    # )

    # Method 3: KINEMATIC CHAIN MODE (multi-joint biomechanical analysis)
    analyzer = SwingAnalyzer(
        kinematic_chain_mode=True,  # 🔥 ENABLED FOR TESTING
        use_adaptive_velocity=True,
        adaptive_velocity_percent=0.15,
        contact_angle_min=120,
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
