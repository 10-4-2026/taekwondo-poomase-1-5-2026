# Kế hoạch phát triển ứng dụng Android Taekwondo Poomsae (On-Device)

Kế hoạch này chi tiết lộ trình chuyển đổi ứng dụng từ Python sang Android native, đảm bảo mọi khâu xử lý từ nhận diện tư thế đến tính toán góc đều diễn ra trực tiếp trên điện thoại.

## 1. Kiến trúc tổng quan
- **Ngôn ngữ**: Kotlin (đề xuất) vì hỗ trợ tốt nhất cho CameraX và MediaPipe.
- **Framework ML**: MediaPipe Tasks cho Android (nhúng trực tiếp model `.task`).
- **Xử lý đồ họa**: OpenGL ES hoặc Canvas API để vẽ skeleton real-time.
- **Xử lý Video**: CameraX (cho live stream) và MediaCodec/ExoPlayer (cho video file).

## 2. Các giai đoạn triển khai

### Giai đoạn 1: Thiết lập môi trường & Cấu trúc
- Tạo project Android Studio mới (Empty Views Activity hoặc Jetpack Compose).
- Thêm dependency MediaPipe:
  ```gradle
  implementation 'com.google.mediapipe:tasks-vision:latest.release'
  ```
- Copy file `pose_landmarker.task` vào thư mục `assets` của ứng dụng Android.

### Giai đoạn 2: Porting Logic tính toán (pose_utils.py -> Kotlin)
- Chuyển đổi hàm `calculate_angle`:
  - Sử dụng `Math.atan2` trong Kotlin.
  - Xây dựng class `PoseAnalyzer` để quản lý các danh sách điểm (landmarks) và định nghĩa các góc (Vai, Gối, Hông...).
- Định nghĩa lại các điểm trung tâm (mid-shoulder, mid-hip) tương tự logic hiện tại.

### Giai đoạn 3: Xử lý Camera & Model Inference
- Sử dụng **MediaPipe Pose Landmarker** ở chế độ:
  - `RunningMode.LIVE_STREAM`: Cho phân tích trực tiếp qua camera.
  - `RunningMode.VIDEO`: Cho phân tích video đã quay sẵn.
- Tối ưu hóa: Sử dụng GPU Delegate để tăng tốc độ xử lý trên Android.

### Giai đoạn 4: Giao diện & Luồng người dùng (UX Flow)
Ứng dụng sẽ tập trung vào 2 chế độ hoạt động chính:

#### Chế độ 1: So sánh 2 Video (File vs File)
- **Luồng**: Chọn Video A (Mẫu) -> Chọn Video B (Thực tế) -> Nhấn "Phân tích".
- **Kỹ thuật**: 
  - Sử dụng MediaPipe `RunningMode.VIDEO` để xử lý offline cả 2 file.
  - Đồng bộ hóa timeline dựa trên thời lượng hoặc điểm bắt đầu của động tác.
  - Hiển thị kết quả so sánh qua biểu đồ độ lệch (Similarity Chart).

#### Chế độ 2: Tập luyện trực tiếp (Video mẫu vs Camera)
- **Luồng**: Chọn Video Mẫu -> Mở Camera -> Nhấn "Bắt đầu".
- **Kỹ thuật**:
  - Video mẫu phát ở một góc màn hình (Picture-in-Picture) hoặc chia đôi màn hình.
  - Camera xử lý bằng MediaPipe `RunningMode.LIVE_STREAM` để cho phản hồi ngay lập tức.
  - Hiển thị skeleton và cảnh báo góc sai trực tiếp trên màn hình (Real-time overlay).

#### Chế độ 3: So sánh dựa trên dữ liệu chuẩn (CSV vs Video/Camera)
- **Luồng**: Chọn File CSV (chứa dữ liệu mẫu) -> Chọn Video Thực tế HOẶC Mở Camera.
- **Kỹ thuật**:
  - Ứng dụng đọc dữ liệu từ CSV vào bộ nhớ (không cần xử lý MediaPipe cho nguồn mẫu -> tiết kiệm pin và tài nguyên).
  - So sánh trực tiếp dữ liệu CSV với kết quả MediaPipe từ nguồn thực tế (Video/Camera).
  - Rất hữu ích khi người dùng đã có bộ dữ liệu chuẩn từ các vận động viên chuyên nghiệp.

### Giai đoạn 5: Lưu trữ & Xuất dữ liệu (Data Export)
- **Lưu trữ nội bộ**: Sử dụng SQLite để quản lý danh sách các phiên tập.
- **Xuất file CSV**:
  - Mỗi khi kết thúc phân tích, ứng dụng tự động tổng hợp dữ liệu (Frame ID, Timestamp, Góc 1, Góc 2...).
  - Lưu file CSV vào bộ nhớ của ứng dụng (Scoped Storage).
  - Cung cấp nút "Chia sẻ" hoặc "Tải xuống" để người dùng lưu file ra ngoài hoặc gửi qua email/zalo.
- **Tính toán điểm số**: Similarity score dựa trên độ lệch góc giữa 2 nguồn dữ liệu.

## 3. Các thách thức kỹ thuật & Giải pháp
| Thách thức | Giải pháp |
| :--- | :--- |
| **Hiệu năng** | Sử dụng MediaPipe GPU delegate và xử lý bất đồng bộ (Coroutines). |
| **Độ trễ** | Giảm độ phân giải input cho MediaPipe (ví dụ 256x256) nhưng vẫn giữ chất lượng video cho người dùng xem. |
| **Đồng bộ video** | Implement logic Frame-by-frame processing để đảm bảo 2 video chạy khớp nhịp khi so sánh. |

## 4. Danh sách công việc ưu tiên (To-do)
1. [ ] Khởi tạo Project Android và tích hợp SDK MediaPipe.
2. [ ] Viết class `AngleCalculator.kt` dựa trên `calculate_angle` của Python.
3. [ ] Xây dựng Camera Preview với CameraX.
4. [ ] Implement Pose Landmarker kết nối với Camera feed.
5. [ ] Vẽ Skeleton lên SurfaceView/Overlay.
6. [ ] Xử lý lưu và so sánh dữ liệu giữa 2 phiên tập.

---
> [!NOTE]
> Mọi xử lý sẽ được đóng gói hoàn toàn trong file APK, không cần Server hay Internet sau khi cài đặt.
