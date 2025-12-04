"""
Swing Analysis Results Data Structure

This module provides a structured way to store and manage tennis swing analysis results,
including phase detection, engine metrics, tempo analysis, and kinetic chain data.
"""

import json
from typing import Dict, Any, Optional


class SwingAnalysisResults:
    """
    Stores comprehensive swing analysis data including phases, engine metrics,
    tempo analysis, and kinetic chain information.

    Attributes:
        phases (dict): Detected swing phases (unit_turn, backswing, forward_swing, contact, follow_through)
        engine (dict): Engine metrics (hip_shoulder_separation, max_shoulder_rotation, max_hip_rotation)
        tempo (dict): Tempo metrics (backswing_duration, forward_swing_duration, swing_rhythm_ratio)
        kinetic_chain (dict): Kinetic chain metrics (peak_velocity_sequence, chain_lag, confidence)
        video_quality (dict): Video quality assessment from video_quality_checker
        tracking_quality (dict): Pose tracking quality from video_processor
    """

    def __init__(self):
        """Initialize empty swing analysis results structure."""
        self.phases = {
            'unit_turn': None,
            'backswing': None,
            'forward_swing': None,
            'contact': None,
            'follow_through': None
        }

        self.engine = {
            'hip_shoulder_separation': None,
            'max_shoulder_rotation': None,
            'max_hip_rotation': None
        }

        self.tempo = {
            'backswing_duration': None,
            'forward_swing_duration': None,
            'swing_rhythm_ratio': None
        }

        self.kinetic_chain = {
            'peak_velocity_sequence': None,
            'chain_lag': None,
            'confidence': None
        }

        self.video_quality = None
        self.tracking_quality = None

    def add_phase(
        self,
        phase_name: str,
        detected: bool,
        frame: Optional[int] = None,
        timestamp: Optional[float] = None,
        confidence: float = 0.0,
        **metrics
    ) -> None:
        """
        Add or update a swing phase with detection results and metrics.

        Args:
            phase_name: Name of phase ('unit_turn', 'backswing', 'forward_swing', 'contact', 'follow_through')
            detected: Whether the phase was detected
            frame: Frame number where phase occurs (None if not detected)
            timestamp: Timestamp in seconds where phase occurs (None if not detected)
            confidence: Detection confidence score (0.0-1.0)
            **metrics: Phase-specific metrics (e.g., wrist_velocity, shoulder_rotation, elbow_angle)

        Raises:
            ValueError: If phase_name is invalid or data types are incorrect
        """
        # Validate phase name
        if phase_name not in self.phases:
            raise ValueError(
                f"Invalid phase_name: {phase_name}. "
                f"Must be one of: {', '.join(self.phases.keys())}"
            )

        # Validate data types
        if not isinstance(detected, bool):
            raise ValueError(f"detected must be a boolean, got {type(detected)}")

        if detected:
            if frame is not None and not isinstance(frame, int):
                raise ValueError(f"frame must be an integer, got {type(frame)}")
            if timestamp is not None and not isinstance(timestamp, (int, float)):
                raise ValueError(f"timestamp must be a number, got {type(timestamp)}")

        if not isinstance(confidence, (int, float)):
            raise ValueError(f"confidence must be a number, got {type(confidence)}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")

        # Build phase data
        phase_data = {
            'detected': detected,
            'frame': frame,
            'timestamp': timestamp,
            'confidence': confidence
        }

        # Add any additional metrics
        for key, value in metrics.items():
            phase_data[key] = value

        self.phases[phase_name] = phase_data

    def add_engine_metrics(
        self,
        hip_shoulder_sep: Optional[Dict[str, Any]] = None,
        max_shoulder_rot: Optional[Dict[str, Any]] = None,
        max_hip_rot: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add engine metrics (hip-shoulder separation, rotations).

        Args:
            hip_shoulder_sep: Dict with keys: max_value, frame, timestamp
                Example: {'max_value': 35.2, 'frame': 67, 'timestamp': 2.23}
            max_shoulder_rot: Dict with keys: value, frame, timestamp
                Example: {'value': -42.1, 'frame': 67, 'timestamp': 2.23}
            max_hip_rot: Dict with keys: value, frame, timestamp
                Example: {'value': -55.3, 'frame': 65, 'timestamp': 2.17}

        Raises:
            ValueError: If data types are incorrect
        """
        if hip_shoulder_sep is not None:
            if not isinstance(hip_shoulder_sep, dict):
                raise ValueError(f"hip_shoulder_sep must be a dict, got {type(hip_shoulder_sep)}")
            self.engine['hip_shoulder_separation'] = hip_shoulder_sep

        if max_shoulder_rot is not None:
            if not isinstance(max_shoulder_rot, dict):
                raise ValueError(f"max_shoulder_rot must be a dict, got {type(max_shoulder_rot)}")
            self.engine['max_shoulder_rotation'] = max_shoulder_rot

        if max_hip_rot is not None:
            if not isinstance(max_hip_rot, dict):
                raise ValueError(f"max_hip_rot must be a dict, got {type(max_hip_rot)}")
            self.engine['max_hip_rotation'] = max_hip_rot

    def add_tempo_metrics(
        self,
        backswing_duration: Optional[float] = None,
        forward_swing_duration: Optional[float] = None,
        swing_rhythm_ratio: Optional[float] = None
    ) -> None:
        """
        Add tempo metrics (swing timing and rhythm).

        Args:
            backswing_duration: Duration of backswing in seconds
            forward_swing_duration: Duration of forward swing in seconds
            swing_rhythm_ratio: Ratio of backswing to forward swing duration

        Raises:
            ValueError: If data types are incorrect
        """
        if backswing_duration is not None:
            if not isinstance(backswing_duration, (int, float)):
                raise ValueError(f"backswing_duration must be a number, got {type(backswing_duration)}")
            if backswing_duration < 0:
                raise ValueError(f"backswing_duration must be non-negative, got {backswing_duration}")
            self.tempo['backswing_duration'] = backswing_duration

        if forward_swing_duration is not None:
            if not isinstance(forward_swing_duration, (int, float)):
                raise ValueError(f"forward_swing_duration must be a number, got {type(forward_swing_duration)}")
            if forward_swing_duration < 0:
                raise ValueError(f"forward_swing_duration must be non-negative, got {forward_swing_duration}")
            self.tempo['forward_swing_duration'] = forward_swing_duration

        if swing_rhythm_ratio is not None:
            if not isinstance(swing_rhythm_ratio, (int, float)):
                raise ValueError(f"swing_rhythm_ratio must be a number, got {type(swing_rhythm_ratio)}")
            if swing_rhythm_ratio < 0:
                raise ValueError(f"swing_rhythm_ratio must be non-negative, got {swing_rhythm_ratio}")
            self.tempo['swing_rhythm_ratio'] = swing_rhythm_ratio

    def add_kinetic_chain_metrics(
        self,
        sequence: Optional[Dict[str, Any]] = None,
        chain_lag: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None
    ) -> None:
        """
        Add kinetic chain metrics (velocity sequencing and lag times).

        Args:
            sequence: Dict describing peak velocity sequence
                Example: {
                    'hip': {'frame': 65, 'timestamp': 2.17, 'velocity': 245.3},
                    'shoulder': {'frame': 67, 'timestamp': 2.23, 'velocity': 312.1},
                    'elbow': {'frame': 99, 'timestamp': 3.30, 'velocity': 425.7},
                    'wrist': {'frame': 102, 'timestamp': 3.40, 'velocity': 612.4}
                }
            chain_lag: Dict with lag times between segments
                Example: {
                    'hip_to_shoulder': 0.06,
                    'shoulder_to_elbow': 1.07,
                    'elbow_to_wrist': 0.10
                }
            confidence: Overall confidence in kinetic chain detection (0.0-1.0)

        Raises:
            ValueError: If data types are incorrect
        """
        if sequence is not None:
            if not isinstance(sequence, dict):
                raise ValueError(f"sequence must be a dict, got {type(sequence)}")
            self.kinetic_chain['peak_velocity_sequence'] = sequence

        if chain_lag is not None:
            if not isinstance(chain_lag, dict):
                raise ValueError(f"chain_lag must be a dict, got {type(chain_lag)}")
            self.kinetic_chain['chain_lag'] = chain_lag

        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                raise ValueError(f"confidence must be a number, got {type(confidence)}")
            if not 0.0 <= confidence <= 1.0:
                raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")
            self.kinetic_chain['confidence'] = confidence

    def set_video_quality(self, quality_metrics: Dict[str, Any]) -> None:
        """
        Set video quality metrics from video_quality_checker.

        Args:
            quality_metrics: Dict containing video quality assessment
                Example: {
                    'resolution': {'width': 1920, 'height': 1080, 'quality': 'high'},
                    'frame_rate': {'fps': 60, 'quality': 'excellent'},
                    'overall_quality': 'good'
                }

        Raises:
            ValueError: If quality_metrics is not a dict
        """
        if not isinstance(quality_metrics, dict):
            raise ValueError(f"quality_metrics must be a dict, got {type(quality_metrics)}")
        self.video_quality = quality_metrics

    def set_tracking_quality(self, tracking_metrics: Dict[str, Any]) -> None:
        """
        Set tracking quality metrics from video_processor.

        Args:
            tracking_metrics: Dict containing pose tracking quality
                Example: {
                    'detection_rate': 0.95,
                    'high_confidence_rate': 0.87,
                    'average_confidence': 0.82
                }

        Raises:
            ValueError: If tracking_metrics is not a dict
        """
        if not isinstance(tracking_metrics, dict):
            raise ValueError(f"tracking_metrics must be a dict, got {type(tracking_metrics)}")
        self.tracking_quality = tracking_metrics

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert results to nested dictionary.

        Returns:
            dict: Complete analysis results as nested dictionary
        """
        return {
            'phases': self.phases,
            'engine': self.engine,
            'tempo': self.tempo,
            'kinetic_chain': self.kinetic_chain,
            'video_quality': self.video_quality,
            'tracking_quality': self.tracking_quality
        }

    def to_json(self, indent: int = 2) -> str:
        """
        Convert results to JSON string.

        Args:
            indent: Number of spaces for JSON indentation (default: 2)

        Returns:
            str: JSON-formatted string of analysis results
        """
        return json.dumps(self.to_dict(), indent=indent)

    def get_phases_detected_count(self) -> int:
        """
        Get count of detected phases.

        Returns:
            int: Number of phases that were successfully detected
        """
        return sum(
            1 for phase_data in self.phases.values()
            if phase_data and phase_data.get('detected', False)
        )

    def get_overall_confidence(self) -> float:
        """
        Calculate overall detection confidence across all phases.

        Returns:
            float: Average confidence score (0.0-1.0), or 0.0 if no phases detected
        """
        confidences = [
            phase_data.get('confidence', 0.0)
            for phase_data in self.phases.values()
            if phase_data and phase_data.get('detected', False)
        ]

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)

    def __repr__(self) -> str:
        """String representation of results."""
        phases_detected = self.get_phases_detected_count()
        overall_confidence = self.get_overall_confidence()

        return (
            f"SwingAnalysisResults("
            f"phases_detected={phases_detected}/5, "
            f"overall_confidence={overall_confidence:.2f})"
        )


# Example usage and testing
if __name__ == "__main__":
    print("Testing SwingAnalysisResults class\n")
    print("=" * 60)

    # Create results object
    results = SwingAnalysisResults()

    # Add phases
    print("\n[Test 1] Adding phases")
    results.add_phase(
        'contact',
        detected=True,
        frame=102,
        timestamp=3.4,
        confidence=0.95,
        wrist_velocity=0.82,
        elbow_angle=165.3,
        method='kinematic_chain'
    )
    print("  ✅ Added contact phase")

    results.add_phase(
        'backswing',
        detected=True,
        frame=45,
        timestamp=1.5,
        confidence=0.88,
        shoulder_rotation=-35.2,
        hip_rotation=-28.1
    )
    print("  ✅ Added backswing phase")

    results.add_phase(
        'unit_turn',
        detected=False,
        confidence=0.0
    )
    print("  ✅ Added unit_turn phase (not detected)")

    # Add engine metrics
    print("\n[Test 2] Adding engine metrics")
    results.add_engine_metrics(
        hip_shoulder_sep={'max_value': 35.2, 'frame': 67, 'timestamp': 2.23},
        max_shoulder_rot={'value': -42.1, 'frame': 67, 'timestamp': 2.23},
        max_hip_rot={'value': -55.3, 'frame': 65, 'timestamp': 2.17}
    )
    print("  ✅ Added engine metrics")

    # Add tempo metrics
    print("\n[Test 3] Adding tempo metrics")
    results.add_tempo_metrics(
        backswing_duration=1.2,
        forward_swing_duration=0.3,
        swing_rhythm_ratio=4.0
    )
    print("  ✅ Added tempo metrics")

    # Add kinetic chain metrics
    print("\n[Test 4] Adding kinetic chain metrics")
    results.add_kinetic_chain_metrics(
        sequence={
            'hip': {'frame': 65, 'timestamp': 2.17, 'velocity': 245.3},
            'shoulder': {'frame': 67, 'timestamp': 2.23, 'velocity': 312.1},
            'elbow': {'frame': 99, 'timestamp': 3.30, 'velocity': 425.7},
            'wrist': {'frame': 102, 'timestamp': 3.40, 'velocity': 612.4}
        },
        chain_lag={
            'hip_to_shoulder': 0.06,
            'shoulder_to_elbow': 1.07,
            'elbow_to_wrist': 0.10
        },
        confidence=0.92
    )
    print("  ✅ Added kinetic chain metrics")

    # Add quality metrics
    print("\n[Test 5] Adding quality metrics")
    results.set_video_quality({
        'resolution': {'width': 1920, 'height': 1080, 'quality': 'high'},
        'frame_rate': {'fps': 60, 'quality': 'excellent'},
        'overall_quality': 'good'
    })
    results.set_tracking_quality({
        'detection_rate': 0.95,
        'high_confidence_rate': 0.87,
        'average_confidence': 0.82
    })
    print("  ✅ Added video and tracking quality metrics")

    # Test utility methods
    print("\n[Test 6] Testing utility methods")
    print(f"  Phases detected: {results.get_phases_detected_count()}/5")
    print(f"  Overall confidence: {results.get_overall_confidence():.2f}")
    print(f"  Repr: {results}")

    # Test to_dict()
    print("\n[Test 7] Converting to dictionary")
    data_dict = results.to_dict()
    print(f"  ✅ Dictionary keys: {list(data_dict.keys())}")
    print(f"  Contact phase data: {data_dict['phases']['contact']}")

    # Test to_json()
    print("\n[Test 8] Converting to JSON")
    json_str = results.to_json()
    print("  ✅ JSON output (first 200 chars):")
    print(f"  {json_str[:200]}...")

    # Test validation
    print("\n[Test 9] Testing validation")
    try:
        results.add_phase('invalid_phase', detected=True, frame=100, timestamp=3.3, confidence=0.9)
        print("  ❌ Should have raised ValueError for invalid phase name")
    except ValueError as e:
        print(f"  ✅ Correctly rejected invalid phase: {str(e)[:60]}...")

    try:
        results.add_phase('contact', detected=True, frame=100, timestamp=3.3, confidence=1.5)
        print("  ❌ Should have raised ValueError for confidence > 1.0")
    except ValueError as e:
        print(f"  ✅ Correctly rejected invalid confidence: {str(e)[:60]}...")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("\nFull JSON output:")
    print(results.to_json())
