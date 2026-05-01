# Kế hoạch Xây dựng Ứng dụng Android Độc lập - Taekwondo Poomsae

Kế hoạch này hướng dẫn xây dựng một ứng dụng Android hoàn chỉnh từ con số 0, không phụ thuộc vào các tệp Python hiện có, tập trung vào kiến trúc di động hiện đại và hiệu năng AI cao nhất.

---

## 1. Kiến trúc & Công nghệ (System Architecture)
- **Kiến trúc**: MVVM (Model-View-ViewModel) giúp tách biệt logic xử lý AI và giao diện.
- **UI Framework**: **Jetpack Compose** (hiện đại, linh hoạt cho các hiệu ứng động).
- **Ngôn ngữ**: Kotlin (100%).
- **AI/ML**: MediaPipe Tasks Vision (Sử dụng trực tiếp các API Android Native).
- **Xử lý Video**: CameraX (Live) và Media3/Transformer (Video files).

---

## 2. Các thành phần chính của dự án

### Phần A: Thiết lập dự án (Project Setup)
1. **Khởi tạo**: Tạo "Empty Compose Activity" project trong Android Studio.
2. **Dependencies**:
   - `androidx.compose.*`: Giao diện người dùng.
   - `com.google.mediapipe:tasks-vision`: Thư viện xử lý Pose.
   - `androidx.camera.*`: Xử lý camera.
   - `androidx.lifecycle:lifecycle-viewmodel-compose`: Quản lý trạng thái ứng dụng.
3. **Assets**: Đưa model `pose_landmarker.task` vào thư mục `src/main/assets`.

### Phần B: Xây dựng Engine Toán học (Native Math Engine)
Thay vì chuyển đổi từ Python, chúng ta sẽ viết trực tiếp logic tính toán bằng Kotlin:
1. **`PoseMath.kt`**:
   - Triển khai hàm tính độ dốc và góc giữa 2 vector.
   - Xử lý chuẩn hóa tọa độ từ MediaPipe (0.0 - 1.0) sang tọa độ màn hình (Pixels).
2. **`PoomsaeLogic.kt`**:
   - Định nghĩa bộ quy tắc cho từng thế võ (ví dụ: góc tấn công, góc phòng thủ).
   - Thiết lập các hằng số ngưỡng (threshold) để đánh giá độ chính xác.
3. **`SimilarityEngine.kt`**:
   - Triển khai thuật toán **Jensen-Shannon Distance** để so sánh sự tương đồng giữa hai tập hợp dữ liệu góc.
   - Xây dựng logic tạo Histogram cho các góc (từ 0 đến 180 độ) để chuẩn bị cho việc tính toán phân phối xác suất.

### Phần C: Xử lý Camera & AI (AI Core)
1. **`PoseLandmarkerHelper.kt`**:
   - Tạo class quản lý vòng đời của MediaPipe.
   - Cấu hình chạy trên GPU (GPU Delegate) để đạt tốc độ > 30 FPS.
   - Xử lý hai chế độ: `LIVE_STREAM` và `VIDEO`.
2. **`CameraManager.kt`**:
   - Kết nối luồng CameraX với `PoseLandmarkerHelper`.
   - Đảm bảo frame hình được xử lý mượt mà và không gây rác bộ nhớ.

### Phần D: Giao diện & Trực quan hóa (UI & Visualization)
1. **Skeleton Overlay**:
   - Sử dụng `Canvas` trong Jetpack Compose để vẽ khung xương.
   - Áp dụng các hiệu ứng Gradient và Glow cho xương để tạo cảm giác "Premium/Cyber".
2. **Dashboard Kết quả**:
   - Hiển thị các chỉ số góc theo thời gian thực bằng các "Circular Progress Bars" hoặc "Real-time Graphs".
   - Hệ thống thông báo bằng màu sắc: 
     - *Xanh dương*: Hoàn hảo.
     - *Vàng*: Cần điều chỉnh.
     - *Đỏ*: Sai tư thế.

---

## 3. Quy trình triển khai chi tiết

### Bước 1: Hạ tầng (Infrastructure) - [1-2 ngày]
- Tạo project, cấu hình Gradle.
- Thiết lập quyền Camera và Storage (Android 13+ yêu cầu quyền Media Video).

### Bước 2: AI Core & Math - [3-4 ngày]
- Viết class `PoseLandmarkerHelper` xử lý landmarks.
- Viết class `AngleEngine` để tính 18 góc khớp xương.
- Kiểm tra độ chính xác của landmarks bằng cách in log tọa độ.

### Bước 3: Camera Live & Skeleton - [3 ngày]
- Tích hợp CameraX.
- Vẽ skeleton cơ bản lên màn hình.
- Đồng bộ hóa tọa độ landmarks với Preview của camera để xương không bị lệch.

### Bước 4: So sánh & Đồng bộ (Video Comparison) - [4-5 ngày]
- Xây dựng logic chọn video từ thư viện máy.
- Viết module xử lý video offline (không hiển thị lên màn hình nhưng vẫn lấy được landmarks).
- Triển khai thuật toán **Interpolation** (nội suy) để khớp nhịp độ 2 video.
- Tính toán điểm **Similarity Score** sử dụng thuật toán **Jensen-Shannon Distance**:
  - Tạo phân phối xác suất (Probability Distribution) từ các góc đã tính toán.
  - Tính toán KL Divergence giữa hai phân phối để đưa ra chỉ số khoảng cách (Distance).
  - Chuyển đổi chỉ số khoảng cách sang điểm số phần trăm tương đồng (0% - 100%).


### Bước 5: Hoàn thiện UX & Export - [2 ngày]
- Thiết kế màn hình kết quả chuyên nghiệp.
- Logic lưu dữ liệu vào tệp CSV và chia sẻ qua hệ thống của Android.
- Tối ưu hóa hiệu năng để máy không bị nóng khi chạy AI liên tục.

---

## 4. Danh sách các màn hình (App Screens)
1. **Home Screen**: Chọn chế độ (Live Training / Video Analysis).
2. **Camera Screen**: Màn hình chính để tập luyện, có overlay skeleton.
3. **Video Picker**: Chọn video mẫu và video thực tế.
4. **Analysis Report**: Hiển thị điểm số, biểu đồ so sánh và nút xuất CSV.

---
*Kế hoạch này đảm bảo bạn có một ứng dụng Android hiện đại, độc lập hoàn toàn và đạt tiêu chuẩn chất lượng cao.*
