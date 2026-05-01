
'''
    # Phân tích frame theo slider
    target_error_pct = st.slider("Mức độ lệch khớp muốn kiểm tra (%):", 5, 50, 5, key="joint_slider")
    diffs = np.abs(df_s_res[angle_to_plot] - df_p_res[angle_to_plot])
    rel_errors = np.clip(np.nan_to_num(diffs / (df_s_res[angle_to_plot] + 1e-6), nan=0.0), 0, 1.0)

    indices = []
    for start, end in calculate_segments(len(rel_errors)):
        seg = rel_errors[start:end]
        indices.append(start + np.argmin(np.abs(seg - target_error_pct/100.0)))

    s_frames = get_multiple_frames(st.session_state['s_video_bytes'], indices)
    p_frames = get_multiple_frames(st.session_state['p_video_bytes'], indices)

    cols = st.columns(3)
    for i, idx in enumerate(indices):
        with cols[i]:
            st.write(f"**Cặp {i+1} (Frame {idx})**")
            st.caption(f"Độ lệch: {rel_errors[idx]*100:.1f}% ({diffs[idx]:.1f}°)")
            if idx in s_frames and idx in p_frames:
                st.image(s_frames[idx], caption="Mẫu", width='stretch')
                st.image(p_frames[idx], caption="Thực hiện", width='stretch')
'''