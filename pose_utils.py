import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseEstimator:
    def __init__(self, model_path='pose_landmarker.task'):
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_segmentation_masks=False
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def close(self):
        self.landmarker.close()

    def get_landmarks(self, frame, timestamp_ms):
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        result = self.landmarker.detect_for_video(mp_image, timestamp_ms)
        if result.pose_landmarks:
            return result.pose_landmarks[0]
        return None

    @staticmethod
    def calculate_angle(a, b, c):
        """Tính góc tại điểm b (độ)"""
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        if angle > 180.0:
            angle = 360 - angle

        return angle

    def process_frame(self, frame, landmarks):
        if not landmarks:
            return frame, {}

        h, w, _ = frame.shape
        points = {}
        for idx, lm in enumerate(landmarks):
            points[idx] = (int(lm.x * w), int(lm.y * h))

        # Tính toán các điểm trung tâm nếu cần
        mid_shoulder = (
            (points[11][0] + points[12][0]) // 2,
            (points[11][1] + points[12][1]) // 2
        )
        mid_hip = (
            (points[23][0] + points[24][0]) // 2,
            (points[23][1] + points[24][1]) // 2
        )
        mid_body = (
            (mid_shoulder[0] + mid_hip[0]) // 2,
            (mid_shoulder[1] + mid_hip[1]) // 2
        )

        angle_definitions = {
            "Khuỷu tay trái": (points[11], points[13], points[15]),
            "Khuỷu tay phải": (points[12], points[14], points[16]),
            "Vai trái": (points[23], points[11], points[13]),
            "Vai phải": (points[24], points[12], points[14]),
            "Hông trái": (points[11], points[23], points[25]),
            "Hông phải": (points[12], points[24], points[26]),
            "Gối trái": (points[23], points[25], points[27]),
            "Gối phải": (points[24], points[26], points[28]),
            "Cổ chân trái": (points[25], points[27], points[31]),
            "Cổ chân phải": (points[26], points[28], points[32]),
            "Cổ tay trái": (points[13], points[15], points[19]),
            "Cổ tay phải": (points[14], points[16], points[20]),
            "Chân trái - Chân phải": (points[25], mid_hip, points[26]),
            "Tay trái - Tay phải": (points[13], mid_shoulder, points[14]),
            "Tay trái - Chân trái": (points[13], mid_body, points[25]),
            "Tay trái - Chân phải": (points[13], mid_body, points[26]),
            "Tay phải - Chân trái": (points[14], mid_body, points[25]),
            "Tay phải - Chân phải": (points[14], mid_body, points[26]),
        }

        calculated_angles = {}
        for name, (a, b, c) in angle_definitions.items():
            calculated_angles[name] = self.calculate_angle(a, b, c)

        # Vẽ các kết nối
        self.draw_skeleton(frame, points, mid_shoulder, mid_hip)
        
        return frame, calculated_angles

    def draw_skeleton(self, frame, points, mid_shoulder, mid_hip):
        # Các cặp điểm cần nối (theo MediaPipe)
        connections = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Thân trên
            (11, 23), (12, 24), (23, 24), # Thân giữa
            (23, 25), (25, 27), (27, 31), # Chân trái
            (24, 26), (26, 28), (28, 32)  # Chân phải
        ]
        
        for p1, p2 in connections:
            cv2.line(frame, points[p1], points[p2], (0, 255, 0), 2)
            
        for idx in connections:
            for i in idx:
                cv2.circle(frame, points[i], 5, (0, 0, 255), -1)
