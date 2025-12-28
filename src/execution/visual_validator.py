import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import os

class VideoContentValidator:
    """
    Analyzes rendered video to detect common visual issues.
    """
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        self.cap = cv2.VideoCapture(str(video_path))
        
        if not self.cap.isOpened():
            # This might happen if opencv is missing or codec issues
            raise ValueError(f"Could not open video: {video_path}")
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def validate(self) -> Dict:
        """
        Run all validation checks.
        Returns: { 'valid': bool, 'issues': [], ... }
        """
        issues = []
        
        # Sample frames at 25%, 50%, 75%
        # (Skip 0% as it's often black fade-in, skip 100% as it's fade-out)
        sample_points = [
            int(self.total_frames * 0.25),
            int(self.total_frames * 0.5),
            int(self.total_frames * 0.75),
        ]
        
        frame_results = []
        
        for frame_num in sample_points:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = self.cap.read()
            
            if not ret:
                continue
            
            result = self._analyze_frame(frame, frame_num)
            frame_results.append(result)
        
        if not frame_results:
             return {"valid": False, "issues": ["CRITICAL: Could not read any frames from video."]}

        # Check 1: Blank frames
        blank_frames = [r for r in frame_results if r['is_blank']]
        if len(blank_frames) == len(frame_results):
            issues.append("CRITICAL: Video appears to be completely blank (black screen).")
        
        # Check 2: Low contrast
        # If all sampled frames correspond to low contrast, might be an issue
        low_contrast_frames = [r for r in frame_results if r['low_contrast']]
        if len(low_contrast_frames) == len(frame_results) and not issues: # Only warn if not already blank
            issues.append("WARNING: Low video contrast detected.")
        
        self.cap.release()
        
        return {
            'valid': len([i for i in issues if 'CRITICAL' in i]) == 0,
            'issues': issues,
            'metrics': {
                'frame_results': frame_results
            }
        }
    
    def _analyze_frame(self, frame: np.ndarray, frame_num: int) -> Dict:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        mean_brightness = np.mean(gray)
        is_blank = mean_brightness < 10 # Threshold for black
        
        std_dev = np.std(gray)
        low_contrast = std_dev < 20
        
        return {
            'frame_num': frame_num,
            'is_blank': bool(is_blank),
            'low_contrast': bool(low_contrast),
            'mean_brightness': mean_brightness
        }

def validate_video_content(video_path: str) -> Dict:
    try:
        validator = VideoContentValidator(video_path)
        return validator.validate()
    except Exception as e:
        return {
            "valid": False,
            "issues": [f"Validator Error: {str(e)}"]
        }
