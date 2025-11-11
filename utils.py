import numpy as np
import math

def calculate_angle(point_a, point_b, point_c):
    """
    Calculate angle at point B given three points A, B, C
    Returns angle in degrees
    """
    # Convert to numpy arrays
    a = np.array([point_a['x'], point_a['y']])
    b = np.array([point_b['x'], point_b['y']])
    c = np.array([point_c['x'], point_c['y']])
    
    # Vectors
    ba = a - b
    bc = c - b
    
    # Angle calculation
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    # Clamp to avoid numerical errors
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.arccos(cosine_angle)
    
    return np.degrees(angle)

def calculate_velocity(current_pos, previous_pos, time_delta):
    """
    Calculate velocity between two positions
    Returns velocity as pixels per second
    """
    if time_delta == 0:
        return 0
    
    dx = current_pos['x'] - previous_pos['x']
    dy = current_pos['y'] - previous_pos['y']
    
    distance = math.sqrt(dx**2 + dy**2)
    velocity = distance / time_delta
    
    return velocity

def get_body_center_x(left_shoulder, right_shoulder):
    """Get x-coordinate of body center (midpoint between shoulders)"""
    return (left_shoulder['x'] + right_shoulder['x']) / 2

def is_wrist_behind_body(wrist, left_shoulder, right_shoulder):
    """Check if wrist is behind the body center line"""
    body_center_x = get_body_center_x(left_shoulder, right_shoulder)
    # For right-handed forehand from right side view, 
    # wrist is "behind" if x is less than body center
    return wrist['x'] < body_center_x

def calculate_shoulder_rotation(left_shoulder, right_shoulder):
    """
    Calculate shoulder rotation angle relative to horizontal
    Returns angle in degrees
    """
    dx = right_shoulder['x'] - left_shoulder['x']
    dy = right_shoulder['y'] - left_shoulder['y']
    
    angle = math.atan2(dy, dx)
    return math.degrees(angle)


# Test the utility functions
if __name__ == "__main__":
    # Test data
    shoulder = {'x': 0.5, 'y': 0.3}
    elbow = {'x': 0.6, 'y': 0.5}
    wrist = {'x': 0.7, 'y': 0.6}
    
    angle = calculate_angle(shoulder, elbow, wrist)
    print(f"Elbow angle: {angle:.2f} degrees")
    
    # Test velocity
    pos1 = {'x': 0.5, 'y': 0.5}
    pos2 = {'x': 0.6, 'y': 0.6}
    vel = calculate_velocity(pos2, pos1, 1/30)  # 1 frame at 30fps
    print(f"Velocity: {vel:.2f} units/second")