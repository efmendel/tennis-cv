"""
Video Quality Checker

This module provides functionality to assess video quality for tennis swing analysis.
It checks resolution, frame rate, brightness, and sharpness to ensure videos are
suitable for pose detection and swing analysis.

Author: Tennis-CV Project
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple


def check_video_quality(video_path: str) -> Dict:
    """
    Analyze video quality and return a comprehensive quality report.

    Checks:
    - Resolution: Warns if < 720p (1280x720)
    - Frame rate: Warns if < 24fps
    - Brightness: Warns if average brightness < 100 (0-255 scale)
    - Sharpness: Warns if Laplacian variance < 100 (motion blur detection)

    Args:
        video_path: Path to the video file

    Returns:
        dict: Quality report containing:
            - resolution: (width, height) tuple
            - fps: Frame rate as float
            - brightness: Average brightness (0-255)
            - sharpness: Laplacian variance (higher = sharper)
            - warnings: List of warning strings
            - is_acceptable: Boolean indicating if video meets minimum standards

    Raises:
        FileNotFoundError: If video file doesn't exist
        ValueError: If video cannot be opened or is corrupted
    """
    # Open video file
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    # Initialize report
    warnings: List[str] = []

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Check 1: Resolution
    if width < 1280 or height < 720:
        warnings.append(f"Resolution {width}x{height} is below recommended 720p (1280x720)")

    # Check 2: Frame rate
    if fps < 24:
        warnings.append(f"Frame rate {fps:.1f}fps is below recommended 24fps")

    # Sample frames for brightness and sharpness analysis
    # We'll sample every 10th frame or up to 30 frames, whichever is smaller
    sample_interval = max(1, frame_count // 30)
    sample_count = min(30, frame_count // sample_interval)

    brightness_values = []
    sharpness_values = []

    frame_idx = 0
    samples_collected = 0

    while samples_collected < sample_count:
        # Jump to next sample frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if not ret:
            break

        # Calculate brightness (average pixel intensity)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        brightness_values.append(avg_brightness)

        # Calculate sharpness using Laplacian variance
        # Higher variance = sharper image, lower variance = more blur
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        sharpness_values.append(variance)

        frame_idx += sample_interval
        samples_collected += 1

    cap.release()

    # Calculate average metrics
    avg_brightness = np.mean(brightness_values) if brightness_values else 0
    avg_sharpness = np.mean(sharpness_values) if sharpness_values else 0

    # Check 3: Brightness
    if avg_brightness < 100:
        warnings.append(f"Video is too dark (brightness: {avg_brightness:.1f}/255). Recommended: ≥100")

    # Check 4: Sharpness (motion blur)
    if avg_sharpness < 100:
        warnings.append(f"Video has motion blur or low sharpness (sharpness: {avg_sharpness:.1f}). Recommended: ≥100")

    # Determine if video is acceptable
    # Video is acceptable if it has no warnings
    is_acceptable = len(warnings) == 0

    # Build quality report
    report = {
        'resolution': (width, height),
        'fps': fps,
        'brightness': float(avg_brightness),
        'sharpness': float(avg_sharpness),
        'warnings': warnings,
        'is_acceptable': is_acceptable
    }

    return report


def print_quality_report(report: Dict) -> None:
    """
    Print a formatted quality report to console.

    Args:
        report: Quality report dict from check_video_quality()
    """
    print("\n" + "="*60)
    print("VIDEO QUALITY REPORT")
    print("="*60)

    print(f"\nResolution: {report['resolution'][0]}x{report['resolution'][1]}")
    print(f"Frame Rate: {report['fps']:.1f} fps")
    print(f"Brightness: {report['brightness']:.1f}/255")
    print(f"Sharpness:  {report['sharpness']:.1f}")

    print(f"\nStatus: {'✅ ACCEPTABLE' if report['is_acceptable'] else '⚠️  NEEDS ATTENTION'}")

    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for i, warning in enumerate(report['warnings'], 1):
            print(f"  {i}. {warning}")
    else:
        print("\nNo warnings - video quality is good!")

    print("="*60 + "\n")


if __name__ == "__main__":
    """Test the video quality checker on sample videos."""
    import sys
    import os

    # Check if video path provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Default test video
        video_path = "uploads/test_swing.mp4"

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    print(f"Analyzing video: {video_path}")

    try:
        report = check_video_quality(video_path)
        print_quality_report(report)
    except Exception as e:
        print(f"Error analyzing video: {e}")
        sys.exit(1)
