import streamlit as st
import cv2
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from video_processor import process_video, compare_angles
import tempfile
import os
import time
import multiprocessing
import shutil
from scipy.spatial import distance


# --- CẤU HÌNH & STYLE ---
def setup_page():
    st.set_page_config(page_title="Phân tích Tư thế Cơ thể", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        .stButton>button {
            width: 100%; border-radius: 10px; height: 3em;
            background-color: #007bff; color: white; font-weight: bold;
        }
        .metric-card {
            background-color: white; padding: 15px; border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_multiple_frames(video_bytes, indices):
    """Trích xuất nhiều frame từ bytes cùng lúc để tối ưu"""
    frames = {}
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tfile:
        tfile.write(video_bytes)
        tfile_path = tfile.name
    
    cap = cv2.VideoCapture(tfile_path)
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frames[idx] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cap.release()
    
    try:
        os.remove(tfile_path)
    except:
        pass
    return frames

def calculate_segments(n_frames, n_segments=3):
    """Chia video thành các đoạn để lấy mẫu"""
    size = n_frames // n_segments
    return [(i * size, (i + 1) * size if i < n_segments - 1 else n_frames) for i in range(n_segments)]

def js_distance(v1, v2):
    """Tính khoảng cách Jensen-Shannon giữa hai vector (chuẩn hóa thành phân phối)"""
    v1 = np.atleast_1d(v1).astype(float) + 1e-10
    v2 = np.atleast_1d(v2).astype(float) + 1e-10
    return distance.jensenshannon(v1 / np.sum(v1), v2 / np.sum(v2))


# --- CÁC THÀNH PHẦN GIAO DIỆN ---
def sidebar_info():
    with st.sidebar:
        st.header("Hướng dẫn")
        st.write("1. Tải lên video mẫu (chuẩn).")
        st.write("2. Tải lên video bạn thực hiện.")
        st.write("3. Nhấn 'Bắt đầu Phân tích' và đợi kết quả.")
        st.divider()
        st.info("Sử dụng MediaPipe Pose Landmarker Heavy")

def video_upload_section():
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📁 Video Mẫu")
        sample_file = st.file_uploader("Tải video mẫu", type=['mp4', 'mov', 'avi'], key="sample")
    with col2:
        st.subheader("📁 Video Thực hiện")
        practice_file = st.file_uploader("Tải video thực hành", type=['mp4', 'mov', 'avi'], key="practice")
    return sample_file, practice_file

def process_videos_handler(sample_file, practice_file):
    """Xử lý chính khi nhấn nút Bắt đầu"""
    tmpdir = tempfile.mkdtemp()
    try:
        sample_path = os.path.join(tmpdir, "sample.mp4")
        practice_path = os.path.join(tmpdir, "practice.mp4")
        
        with open(sample_path, "wb") as f: f.write(sample_file.read())
        with open(practice_path, "wb") as f: f.write(practice_file.read())
            
        out_s_video = os.path.join(tmpdir, "res_sample.mp4")
        out_p_video = os.path.join(tmpdir, "res_practice.mp4")
        out_s_csv = os.path.join(tmpdir, "res_sample.csv")
        out_p_csv = os.path.join(tmpdir, "res_practice.csv")
        
        # Đồng bộ hóa frames
        cap_s = cv2.VideoCapture(sample_path)
        cap_p = cv2.VideoCapture(practice_path)
        target_frames = min(int(cap_s.get(cv2.CAP_PROP_FRAME_COUNT)), int(cap_p.get(cv2.CAP_PROP_FRAME_COUNT)))
        cap_s.release(); cap_p.release()

        status_placeholder = st.empty()
        p_col1, p_col2 = st.columns(2)
        with p_col1:
            st.write(f"Tiến độ Mẫu ({target_frames} frames)")
            p1 = st.progress(0.0)
        with p_col2:
            st.write(f"Tiến độ Thực hành ({target_frames} frames)")
            p2 = st.progress(0.0)

        status_placeholder.info(f"⏳ Đang xử lý đồng bộ {target_frames} frames...")
        
        queue_s, queue_p = multiprocessing.Queue(), multiprocessing.Queue()
        proc_s = multiprocessing.Process(target=process_video, args=(sample_path, out_s_video, out_s_csv, queue_s, target_frames))
        proc_p = multiprocessing.Process(target=process_video, args=(practice_path, out_p_video, out_p_csv, queue_p, target_frames))
        
        proc_s.start(); proc_p.start()
        
        while proc_s.is_alive() or proc_p.is_alive() or not queue_s.empty() or not queue_p.empty():
            try:
                while not queue_s.empty(): p1.progress(min(queue_s.get_nowait(), 1.0))
                while not queue_p.empty(): p2.progress(min(queue_p.get_nowait(), 1.0))
                time.sleep(0.1)
            except: pass
        
        proc_s.join(); proc_p.join()

        # Lưu vào session_state
        with open(out_s_video, "rb") as f: st.session_state['s_video_bytes'] = f.read()
        with open(out_p_video, "rb") as f: st.session_state['p_video_bytes'] = f.read()
        with open(out_s_csv, "rb") as f: st.session_state['s_csv_bytes'] = f.read()
        with open(out_p_csv, "rb") as f: st.session_state['p_csv_bytes'] = f.read()
        
        df_s, df_p = pd.read_csv(out_s_csv), pd.read_csv(out_p_csv)
        metrics, df_s_res, df_p_res = compare_angles(df_s, df_p)
        
        st.session_state['analysis_done'] = True
        st.session_state['metrics'] = metrics
        st.session_state['df_s_res'] = df_s_res
        st.session_state['df_p_res'] = df_p_res
        status_placeholder.success("✅ Đã xử lý xong!")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def display_summary_metrics(metrics):
    avg_js = np.mean([v['JS_Distance'] for v in metrics.values()])
    similarity_pct = (1 - avg_js) * 100
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1: st.info(f"**Chỉ số JS Trung bình:** {avg_js:.4f}")
    with m_col3: st.success(f"**ĐỘ TƯƠNG ĐỒNG TỔNG THỂ: {similarity_pct:.4f}%**")

def display_overall_analysis(df_s_res, df_p_res, metrics):
    st.divider()
    st.header("🌐 Phân tích Khoảnh khắc theo Độ lệch Tổng thể")
    target_pct = st.slider("Mức độ lệch tổng thể muốn kiểm tra (%):", 5, 50, 5, key="overall_slider")
    
    joint_cols = list(metrics.keys())
    all_diffs = [np.nan_to_num(np.abs(df_s_res[c] - df_p_res[c]) / (df_s_res[c] + 1e-6), nan=0.0) for c in joint_cols]
    overall_errors = np.clip(np.mean(all_diffs, axis=0), 0, 1.0)
    
    indices = []
    for start, end in calculate_segments(len(overall_errors)):
        seg = overall_errors[start:end]
        indices.append(start + np.argmin(np.abs(seg - target_pct/100.0)))

    # Tìm frame tốt nhất trong khoảng lân cận dựa trên dữ liệu góc
    best_p_indices = []
    for idx in indices:
        min_js = float('inf')
        best_idx = idx
        for ii in range(max(0, idx - 250), min(len(df_p_res), idx + 251)):
            if ii < 0 or ii >= len(df_p_res):
                continue                
            v_s = df_s_res[joint_cols].iloc[idx].values
            v_p = df_p_res[joint_cols].iloc[ii].values
            #dist = js_distance(v_s, v_p)
            # tính dist = trung bình sai số góc            
            dist = np.mean(np.abs(v_s - v_p))
            if dist < min_js:
                min_js = dist
                best_idx = ii
        best_p_indices.append(best_idx)

    s_frames = get_multiple_frames(st.session_state['s_video_bytes'], indices)
    p_frames = get_multiple_frames(st.session_state['p_video_bytes'], best_p_indices)

    cols = st.columns(3)
    for i, idx in enumerate(indices):
        best_p_idx = best_p_indices[i]
        with cols[i]:
            st.write(f"**Khoảnh khắc {i+1} (Frame {idx})**")
            st.caption(f"Sai lệch tổng thể: {overall_errors[idx]*100:.1f}%")
            if idx in s_frames and best_p_idx in p_frames:
                st.image(s_frames[idx], caption="Mẫu", width='stretch')
                st.image(p_frames[best_p_idx], caption=f"Thực hiện (Tối ưu tại frame {best_p_idx})", width='stretch')


def display_joint_analysis(df_s_res, df_p_res, metrics):
    st.divider()
    st.header("📊 Biểu đồ & Phân tích Chi tiết từng Khớp")
    angle_to_plot = st.selectbox("Chọn góc khớp để so sánh:", list(metrics.keys()))
    
    # Biểu đồ
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_s_res['frame'], y=df_s_res[angle_to_plot], name="Mẫu", line=dict(color='#007bff')))
    fig.add_trace(go.Scatter(x=df_p_res['frame'], y=df_p_res[angle_to_plot], name="Thực hiện", line=dict(color='#ff7f0e', dash='dash')))
    fig.update_layout(title=f"Đồ thị: {angle_to_plot}", hovermode="x unified")
    st.plotly_chart(fig, width='stretch')

    pass


# --- MAIN APP ---
def main():
    setup_page()
    st.title("Ứng dụng Phân tích & So sánh Tư thế 🏃‍♂️")
    st.markdown("Hệ thống tự động đánh giá kỹ thuật thực hiện động tác qua video.")
    
    sidebar_info()
    sample_file, practice_file = video_upload_section()

    if sample_file and practice_file:
        if st.button("🚀 Bắt đầu Phân tích"):
            process_videos_handler(sample_file, practice_file)

    if st.session_state.get('analysis_done'):
        st.divider()

        
        display_summary_metrics(st.session_state['metrics'])
        display_overall_analysis(st.session_state['df_s_res'], st.session_state['df_p_res'], st.session_state['metrics'])
        display_joint_analysis(st.session_state['df_s_res'], st.session_state['df_p_res'], st.session_state['metrics'])
        
        with st.expander("📊 Xem bảng thống kê chi tiết tất cả các khớp"):
            summary_df = pd.DataFrame([{"Góc Khớp": k, "Độ đo JS": round(v["JS_Distance"], 4)} for k, v in st.session_state['metrics'].items()])
            st.dataframe(summary_df, width='stretch')
    else:
        st.info("💡 Mẹo: Tải lên cả hai video và nhấn nút bắt đầu để xem phân tích chi tiết.")

if __name__ == "__main__":
    main()
