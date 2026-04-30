import cv2
import pandas as pd
import numpy as np
from pose_utils import PoseEstimator
import os
from scipy.spatial import distance

def process_video(video_path, output_video_path, output_csv_path, progress_callback=None, target_frames=None):
    estimator = PoseEstimator()
    cap = cv2.VideoCapture(video_path)
    
    source_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Xác định danh sách các khung hình cần lấy
    if target_frames and target_frames > 0:
        # Lấy các chỉ số khung hình phân bổ đều
        frame_indices = np.linspace(0, source_total_frames - 1, target_frames, dtype=int)
        total_to_process = target_frames
    else:
        frame_indices = range(source_total_frames)
        total_to_process = source_total_frames

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    all_data = []
    
    for i, frame_idx in enumerate(frame_indices):
        # Di chuyển tới khung hình cần thiết
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
            
        timestamp_ms = int(1000 * frame_idx / fps)
        landmarks = estimator.get_landmarks(frame, timestamp_ms)
        
        processed_frame, angles = estimator.process_frame(frame, landmarks)
        
        # Lưu dữ liệu (sử dụng chỉ số mới để đồng bộ)
        data_row = {"frame": i} # frame index trong bộ dữ liệu đã đồng bộ
        data_row.update(angles)
        all_data.append(data_row)
        
        out.write(processed_frame)
        
        if progress_callback:
            progress = (i + 1) / total_to_process
            if hasattr(progress_callback, 'put'): 
                progress_callback.put(progress)
            else:
                progress_callback(progress)
        
    cap.release()
    out.release()
    estimator.close()
    
    df = pd.DataFrame(all_data)
    df.to_csv(output_csv_path, index=False)
    return df

def compare_angles(df_sample, df_practice):
    """So sánh hai bộ dữ liệu góc"""
    # Đồng bộ hóa độ dài bằng cách nội suy (interpolation)
    #common_length = max(len(df_sample), len(df_practice))
    common_length = min(len(df_sample), len(df_practice))
    
    def resample(df, target_len):
        x = np.linspace(0, 1, len(df))
        x_new = np.linspace(0, 1, target_len)
        new_df = pd.DataFrame({"frame": range(target_len)})
        for col in df.columns:
            if col == "frame": continue
            new_df[col] = np.interp(x_new, x, df[col])
        return new_df

    df_s_resampled = resample(df_sample, common_length)
    df_p_resampled = resample(df_practice, common_length)
    
    metrics = {}
    
    for col in df_s_resampled.columns:
        if col == "frame": continue
        
        s_vals = df_s_resampled[col].values
        p_vals = df_p_resampled[col].values
        
        # Jensen-Shannon Distance
        # Tính histogram để tạo phân phối xác suất
        h_s, _ = np.histogram(s_vals, bins=18, range=(0, 180), density=True)
        h_p, _ = np.histogram(p_vals, bins=18, range=(0, 180), density=True)
        
        # Tránh division by zero/log(0) bằng cách thêm epsilon nhỏ
        h_s += 1e-10
        h_p += 1e-10
        h_s /= h_s.sum()
        h_p /= h_p.sum()
        
        js_dist = distance.jensenshannon(h_s, h_p)
        
        metrics[col] = {
            "JS_Distance": js_dist
        }
        
    return metrics, df_s_resampled, df_p_resampled
