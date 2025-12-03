"""
Kinematic Chain Utility Functions

Functions to calculate biomechanical metrics for tennis swing analysis,
including hip rotation, shoulder rotation, knee bend, trunk lean, and upper arm angles.
"""

import math


def calculate_hip_rotation(landmarks):
    """
    Calculate hip rotation angle relative to camera plane.

    Hip rotation is measured by the angle of the line connecting the hips
    relative to horizontal. Positive values indicate the right hip is forward.

    Args:
        landmarks (dict): Dictionary containing landmark data with 'left_hip' and 'right_hip'
                         Each landmark should have 'x', 'y', 'z' coordinates

    Returns:
        float: Hip rotation angle in degrees (-180 to 180)
               0 = hips parallel to camera
               Positive = right hip forward (rotation to left)
               Negative = left hip forward (rotation to right)
               Returns 0.0 if required landmarks are missing

    Example:
        >>> landmarks = {
        ...     'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.1},
        ...     'right_hip': {'x': 0.6, 'y': 0.5, 'z': -0.1}
        ... }
        >>> angle = calculate_hip_rotation(landmarks)
    """
    try:
        left_hip = landmarks.get('left_hip')
        right_hip = landmarks.get('right_hip')

        if not left_hip or not right_hip:
            return 0.0

        # Calculate rotation using z-coordinates (depth)
        # Positive z means further from camera
        z_diff = right_hip['z'] - left_hip['z']
        x_diff = right_hip['x'] - left_hip['x']

        # Calculate angle in degrees
        # atan2 gives us the angle of rotation
        angle_rad = math.atan2(z_diff, x_diff)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    except (KeyError, TypeError, ValueError):
        return 0.0


def calculate_shoulder_rotation(landmarks):
    """
    Calculate shoulder rotation angle relative to camera plane.

    Shoulder rotation is measured by the angle of the line connecting the shoulders
    relative to horizontal. This indicates upper body rotation.

    Args:
        landmarks (dict): Dictionary containing 'left_shoulder' and 'right_shoulder'
                         Each landmark should have 'x', 'y', 'z' coordinates

    Returns:
        float: Shoulder rotation angle in degrees (-180 to 180)
               0 = shoulders parallel to camera
               Positive = right shoulder forward (rotation to left)
               Negative = left shoulder forward (rotation to right)
               Returns 0.0 if required landmarks are missing

    Example:
        >>> landmarks = {
        ...     'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.05},
        ...     'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': -0.05}
        ... }
        >>> angle = calculate_shoulder_rotation(landmarks)
    """
    try:
        left_shoulder = landmarks.get('left_shoulder')
        right_shoulder = landmarks.get('right_shoulder')

        if not left_shoulder or not right_shoulder:
            return 0.0

        # Calculate rotation using z-coordinates (depth)
        z_diff = right_shoulder['z'] - left_shoulder['z']
        x_diff = right_shoulder['x'] - left_shoulder['x']

        # Calculate angle in degrees
        angle_rad = math.atan2(z_diff, x_diff)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    except (KeyError, TypeError, ValueError):
        return 0.0


def calculate_knee_bend(landmarks, side='right'):
    """
    Calculate knee bend angle for the specified leg.

    The knee bend is the angle formed by hip-knee-ankle. A straight leg is ~180°,
    a bent knee is less (e.g., 90° for a right angle bend).

    Args:
        landmarks (dict): Dictionary containing hip, knee, and ankle landmarks
        side (str): Which leg to measure - 'left' or 'right' (default: 'right')

    Returns:
        float: Knee bend angle in degrees (0-180)
               180 = fully straight leg
               90 = leg bent at right angle
               Returns 180.0 (straight) if required landmarks are missing

    Example:
        >>> landmarks = {
        ...     'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0},
        ...     'right_knee': {'x': 0.6, 'y': 0.7, 'z': 0},
        ...     'right_ankle': {'x': 0.6, 'y': 0.9, 'z': 0}
        ... }
        >>> angle = calculate_knee_bend(landmarks, side='right')
    """
    try:
        # Get the appropriate landmarks based on side
        hip = landmarks.get(f'{side}_hip')
        knee = landmarks.get(f'{side}_knee')
        ankle = landmarks.get(f'{side}_ankle')

        if not hip or not knee or not ankle:
            return 180.0  # Default to straight leg

        # Calculate vectors
        # Vector from knee to hip
        hip_vector = (
            hip['x'] - knee['x'],
            hip['y'] - knee['y'],
            hip['z'] - knee['z']
        )

        # Vector from knee to ankle
        ankle_vector = (
            ankle['x'] - knee['x'],
            ankle['y'] - knee['y'],
            ankle['z'] - knee['z']
        )

        # Calculate dot product
        dot_product = sum(h * a for h, a in zip(hip_vector, ankle_vector))

        # Calculate magnitudes
        hip_mag = math.sqrt(sum(h * h for h in hip_vector))
        ankle_mag = math.sqrt(sum(a * a for a in ankle_vector))

        # Avoid division by zero
        if hip_mag == 0 or ankle_mag == 0:
            return 180.0

        # Calculate angle using dot product formula
        cos_angle = dot_product / (hip_mag * ankle_mag)

        # Clamp to valid range for acos
        cos_angle = max(-1.0, min(1.0, cos_angle))

        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    except (KeyError, TypeError, ValueError):
        return 180.0


def calculate_trunk_lean(landmarks):
    """
    Calculate trunk lean angle relative to vertical.

    Trunk lean is measured by the angle between the midpoint of hips and midpoint
    of shoulders, relative to vertical. Positive indicates forward lean.

    Args:
        landmarks (dict): Dictionary containing hip and shoulder landmarks
                         Needs 'left_hip', 'right_hip', 'left_shoulder', 'right_shoulder'

    Returns:
        float: Trunk lean angle in degrees (-90 to 90)
               0 = perfectly upright
               Positive = leaning forward
               Negative = leaning backward
               Returns 0.0 if required landmarks are missing

    Example:
        >>> landmarks = {
        ...     'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0},
        ...     'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0},
        ...     'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0},
        ...     'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0}
        ... }
        >>> angle = calculate_trunk_lean(landmarks)
    """
    try:
        left_hip = landmarks.get('left_hip')
        right_hip = landmarks.get('right_hip')
        left_shoulder = landmarks.get('left_shoulder')
        right_shoulder = landmarks.get('right_shoulder')

        if not all([left_hip, right_hip, left_shoulder, right_shoulder]):
            return 0.0

        # Calculate midpoints
        hip_mid_x = (left_hip['x'] + right_hip['x']) / 2
        hip_mid_y = (left_hip['y'] + right_hip['y']) / 2
        hip_mid_z = (left_hip['z'] + right_hip['z']) / 2

        shoulder_mid_x = (left_shoulder['x'] + right_shoulder['x']) / 2
        shoulder_mid_y = (left_shoulder['y'] + right_shoulder['y']) / 2
        shoulder_mid_z = (left_shoulder['z'] + right_shoulder['z']) / 2

        # Calculate trunk vector (from hips to shoulders)
        dx = shoulder_mid_x - hip_mid_x
        dy = shoulder_mid_y - hip_mid_y  # Negative y means up in image coordinates
        dz = shoulder_mid_z - hip_mid_z

        # Calculate lean angle in the x-z plane (forward/backward lean)
        # Positive z means leaning forward (away from camera)
        lean_angle_rad = math.atan2(dz, -dy)  # -dy because y increases downward
        lean_angle_deg = math.degrees(lean_angle_rad)

        return lean_angle_deg

    except (KeyError, TypeError, ValueError):
        return 0.0


def calculate_upper_arm_angle(landmarks, side='right'):
    """
    Calculate upper arm angle relative to torso.

    This measures the angle between the shoulder-elbow line and the vertical trunk line.
    Useful for measuring arm elevation during backswing and follow-through.

    Args:
        landmarks (dict): Dictionary containing shoulder, elbow, and hip landmarks
        side (str): Which arm to measure - 'left' or 'right' (default: 'right')

    Returns:
        float: Upper arm angle in degrees (0-180)
               0 = arm pointing straight down
               90 = arm horizontal
               180 = arm pointing straight up
               Returns 0.0 if required landmarks are missing

    Example:
        >>> landmarks = {
        ...     'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0},
        ...     'right_elbow': {'x': 0.7, 'y': 0.4, 'z': 0},
        ...     'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0}
        ... }
        >>> angle = calculate_upper_arm_angle(landmarks, side='right')
    """
    try:
        shoulder = landmarks.get(f'{side}_shoulder')
        elbow = landmarks.get(f'{side}_elbow')
        hip = landmarks.get(f'{side}_hip')

        if not shoulder or not elbow or not hip:
            return 0.0

        # Vector from shoulder to elbow (upper arm)
        arm_vector = (
            elbow['x'] - shoulder['x'],
            elbow['y'] - shoulder['y'],
            elbow['z'] - shoulder['z']
        )

        # Vertical reference vector (from shoulder toward hip)
        vertical_vector = (
            0,  # No horizontal component
            hip['y'] - shoulder['y'],  # Vertical component (positive = downward)
            0   # No depth component
        )

        # Calculate dot product
        dot_product = sum(a * v for a, v in zip(arm_vector, vertical_vector))

        # Calculate magnitudes
        arm_mag = math.sqrt(sum(a * a for a in arm_vector))
        vertical_mag = math.sqrt(sum(v * v for v in vertical_vector))

        # Avoid division by zero
        if arm_mag == 0 or vertical_mag == 0:
            return 0.0

        # Calculate angle using dot product formula
        cos_angle = dot_product / (arm_mag * vertical_mag)

        # Clamp to valid range for acos
        cos_angle = max(-1.0, min(1.0, cos_angle))

        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    except (KeyError, TypeError, ValueError):
        return 0.0


# Helper function for testing
def create_sample_landmarks():
    """
    Create sample landmarks for testing purposes.

    Returns a dictionary with all required landmarks in a neutral standing position.
    """
    return {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.0, 'visibility': 0.9},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.0, 'visibility': 0.9},
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.0, 'visibility': 0.9},
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0.0, 'visibility': 0.9},
        'left_elbow': {'x': 0.35, 'y': 0.4, 'z': 0.0, 'visibility': 0.9},
        'right_elbow': {'x': 0.65, 'y': 0.4, 'z': 0.0, 'visibility': 0.9},
        'left_wrist': {'x': 0.35, 'y': 0.5, 'z': 0.0, 'visibility': 0.9},
        'right_wrist': {'x': 0.65, 'y': 0.5, 'z': 0.0, 'visibility': 0.9},
        'left_knee': {'x': 0.4, 'y': 0.7, 'z': 0.0, 'visibility': 0.9},
        'right_knee': {'x': 0.6, 'y': 0.7, 'z': 0.0, 'visibility': 0.9},
        'left_ankle': {'x': 0.4, 'y': 0.9, 'z': 0.0, 'visibility': 0.9},
        'right_ankle': {'x': 0.6, 'y': 0.9, 'z': 0.0, 'visibility': 0.9},
    }
