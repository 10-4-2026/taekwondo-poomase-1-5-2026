# Tài liệu Kỹ thuật Dự án Phân tích Tư thế Taekwondo Poomsae

Tài liệu này mô tả chi tiết các công nghệ, thuật toán và quy trình triển khai ứng dụng phân tích tư thế võ thuật từ phiên bản Web (Python) đến phiên bản Di động (Android Native).

---

## 1. Tổng quan dự án
Mục tiêu của dự án là xây dựng một hệ thống AI hỗ trợ vận động viên Taekwondo tập luyện Poomsae (quyền) bằng cách so sánh tư thế của họ với các bài quyền mẫu thông qua video hoặc camera trực tiếp. Hệ thống tính toán các góc khớp xương và đưa ra điểm số tương đồng (Similarity Score).

---

## 2. Ngôn ngữ và Công nghệ (Tech Stack)

### A. Phiên bản Web & Nghiên cứu (Python)
- **Framework UI**: Streamlit (tạo dashboard phân tích nhanh).
- **Computer Vision**: OpenCV (xử lý luồng video, vẽ overlay).
- **Machine Learning**: MediaPipe (Google) - Sử dụng model Pose Landmarker để nhận diện 33 điểm mốc trên cơ thể.
- **Xử lý dữ liệu**: 
  - **NumPy**: Tính toán vector và ma trận góc.
  - **Pandas**: Quản lý dữ liệu chuỗi thời gian (time-series) của các góc.
  - **SciPy**: Tính toán khoảng cách thống kê (Jensen-Shannon) để so sánh hai phân phối góc.

### B. Phiên bản Di động (Android Native)
- **Ngôn ngữ**: Kotlin (hiệu năng cao, tương thích tốt với SDK hiện đại).
- **ML Engine**: MediaPipe Tasks Vision Android (chạy trực tiếp model `.task` trên NPU/GPU điện thoại).
- **Camera**: CameraX (Jetpack) - API camera hiện đại hỗ trợ xử lý frame mượt mà.
- **UI/UX**: Jetpack Compose hoặc XML Views với Material Design 3 (Dark Mode).
- **Multithreading**: Kotlin Coroutines (xử lý bất đồng bộ để tránh lag giao diện).

---

## 3. Thuật toán cốt lõi

### 3.1 Nhận diện tư thế (Pose Estimation)
Sử dụng model **BlazePose** của MediaPipe. Model này trả về tọa độ (x, y, z) của 33 điểm mốc. 
- **Độ chính xác**: Cao, hỗ trợ nhận diện cả khi một phần cơ thể bị che khuất.
- **Tốc độ**: Tối ưu hóa cho thiết bị di động (GPU/NPU acceleration).

### 3.2 Thuật toán tính góc (Angle Calculation)
Để tính góc giữa 3 điểm A (start), B (mid/joint), C (end), ta sử dụng hàm `atan2` (arc tangent 2):
```kotlin
// Công thức toán học
angle = abs(atan2(Cy - By, Cx - Bx) - atan2(Ay - By, Ax - Bx))
angle = angle * 180 / PI
if (angle > 180) angle = 360 - angle
```
Thuật toán này đảm bảo góc trả về luôn nằm trong khoảng [0, 180] độ, phù hợp với biên độ vận động của khớp người.

### 3.3 Đồng bộ hóa dữ liệu (Synchronization)
Khi so sánh hai video có độ dài khác nhau, hệ thống sử dụng **Nội suy tuyến tính (Linear Interpolation)**:
- Chuyển đổi cả hai chuỗi dữ liệu về cùng một số lượng khung hình (ví dụ 100 frames).
- Việc này giúp khớp từng nhịp động tác của người tập với mẫu kể cả khi họ thực hiện nhanh hay chậm hơn.

### 3.4 Độ tương đồng (Similarity Metrics)
Sử dụng **Khoảng cách Jensen-Shannon (JS Distance)**:
- Thay vì so sánh từng khung hình (dễ bị sai lệch do thời gian), ta so sánh "phân phối xác suất" của các góc trong suốt bài quyền.
- JS Distance nằm trong khoảng [0, 1], trong đó 0 là hoàn toàn giống nhau.

---

## 4. Quy trình xây dựng (Step-by-Step)

### Bước 1: Tiền xử lý & Model
1. Tải model `pose_landmarker.task`.
2. Định nghĩa các nhóm góc cần theo dõi:
   - Thân trên: Khuỷu tay, Vai.
   - Thân dưới: Hông, Gối, Cổ chân.
   - Trọng tâm: Góc giữa hai chân, góc nghiêng cơ thể.

### Bước 2: Xử lý Video/Camera
- **Python**: Dùng `cv2.VideoCapture` để đọc từng frame.
- **Android**: Dùng `ImageAnalysis` của CameraX để lấy luồng ảnh ở định dạng YUV/RGB.

### Bước 3: Pipeline xử lý Frame
1. Chuyển đổi Frame sang định dạng MediaPipe Image.
2. Chạy Inference (Suy luận) để lấy Landmarks.
3. Tính toán 18+ loại góc dựa trên tọa độ landmarks.
4. Lưu dữ liệu vào CSV hoặc SQLite để phân tích hậu kỳ.

### Bước 4: Vẽ Overlay (Trực quan hóa)
Vẽ skeleton (xương) lên màn hình để người dùng biết AI đang theo dõi đúng bộ phận.
- **Màu Xanh**: Tư thế đúng (sai số < 10 độ).
- **Màu Đỏ**: Tư thế sai (sai số > 20 độ).

### Bước 5: So sánh & Báo cáo
1. Đọc tệp mẫu (CSV hoặc Video mẫu).
2. Chạy thuật toán đồng bộ hóa.
3. Tính toán độ tương đồng tổng thể.
4. Hiển thị biểu đồ đường (Line Chart) để chỉ ra chính xác thời điểm người tập làm sai.

---

## 5. Thách thức và Giải pháp
- **Hiệu năng**: Trên Android, sử dụng `RunningMode.LIVE_STREAM` và ủy thác cho GPU để đạt 30+ FPS.
- **Ánh sáng/Bối cảnh**: MediaPipe Pose Landmarker có khả năng lọc nhiễu tốt, nhưng khuyến nghị người dùng mặc quần áo gọn gàng và đứng đủ xa để lấy toàn thân.

---
*Tài liệu được biên soạn bởi Antigravity AI Assistant.*
