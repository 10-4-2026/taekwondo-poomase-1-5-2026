# Ứng dụng Tính toán Góc Khớp Cơ thể

## 1. Mục tiêu dự án
Xây dựng một ứng dụng giao diện web (Streamlit) cho phép người dùng tải lên 2 video ( video mẫu và video thực hiện), tự động phát hiện các khớp xương, tính toán góc giữa các chi, hiển thị kết quả trực tiếp trên video và xuất dữ liệu ra file CSV giá trị các góc theo từng khung hình. Mỗi vidoe sinh ra 1 file csv kết quả và 1 video có vẽ đường nối các khớp. Video được xử lý song song trên cùng giao diện. Các góc cần tính toán là các góc được xác định bởi 3 điểm mốc. Giao diện tiếng Việt. Sinh đồ thị so sánh từng cặp góc tương ứng của 2 video theo thời gian. Giao diện ưu tiên sử dụng mobile first, mobile friendly. Ưu tiên sử dụng tiếng Việt cho toàn bộ ứng dụng. Sử dụng file model `pose_landmarker_heavy.task` đặt trong cùng thư mục với file script, không cần tải về lại. Sử dụng opencv để đọc video và xử lý video, vẽ đường nối các khớp. Sử dụng độ đó Jensen-Shannon để so sánh sự giống nhau giữa các góc của hai video. Tính sai khác tuyệt đối trung bình. 



## 2. Các góc cần tính toán
- Góc khớp khuỷu tay trái
- Góc khớp khuỷu tay phải
- Góc khớp vai trái
- Góc khớp vai phải
- Góc khớp hông trái
- Góc khớp hông phải
- Góc khớp gối trái
- Góc khớp gối phải
- Góc khớp cổ chân trái
- Góc khớp cổ chân phải
- Góc khớp cổ tay trái
- Góc khớp cổ tay phải
- Góc chân trái với chân phải
- Góc tay trái với tay phải
- Góc tay trái với chân trái
- Góc tay trái với chân phải
- Góc tay phải với chân trái
- Góc tay phải với chân phải



## 3. Công nghệ sử dụng
- **Ngôn ngữ:** Python 3.x
- **Giao diện:** Streamlit
- **Xử lý AI:** MediaPipe (Pose Landmarker)
- **Xử lý Video/Hình ảnh:** OpenCV
- **Xử lý dữ liệu:** Pandas, NumPy
- **Đồ thị:** Matplotlib hoặc Plotly