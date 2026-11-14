# 0003. Kiến trúc modular monolith Python theo ports/adapters

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Hệ thống điều khiển một tay máy UR đặt trên ray để tự động cắm và rút đầu sạc cho xe điện. Phần mềm chạy bằng Docker trên một máy tính đặt tại chỗ, gọi là host: Jetson khi cần GPU, hoặc PC Linux x86. Host nối với controller của tay máy, drive của ray, camera và bộ sạc (EVSE), đồng thời phục vụ giao diện vận hành (HMI). Quy mô là một máy, một cell (khu làm việc của robot).

Các vòng điều khiển thời gian thực (500 Hz) có thể nằm ngay trong controller UR và drive của ray, hoặc chạy trên host. Chạy trên host thì host cần kernel Linux thời gian thực (PREEMPT_RT), trong khi kernel thời gian thực của Jetson mới ở mức developer preview.

Cần chọn cách tổ chức phần mềm trên host và chỗ đặt các vòng điều khiển thời gian thực. Mọi ước tính công sức trong ADR này tính cho một người làm.

## Yếu tố quyết định

- Chỗ đặt thời gian thực: host có phải chạy vòng điều khiển và cần PREEMPT_RT hay không.
- Cùng một image chạy được trên Jetson (arm64) và PC x86 (amd64).
- Công sức của một người: thời gian tới khung chạy đầu-cuối (walking skeleton) và tới đủ chức năng, lượng kiến thức mới phải học, số runtime phải bảo trì.
- Công cụ có sẵn và mức đồng thuận của cộng đồng robotics, nhất là planner tránh va chạm.
- Vừa với quy mô một máy, một cell.
- Có đường nâng cấp khi cần planner, behaviour tree, mã C++ riêng hay kernel thời gian thực.

## Các phương án đã xét

- A: modular monolith Python theo ports/adapters. Phần lõi là một ứng dụng Python (`robot-core`, chạy thành service `core`) chia module theo miền. Module miền chỉ làm việc với thiết bị qua các port khai trong `robot-core/src/robot_core/ports/`; adapter thật và adapter mô phỏng nằm trong `robot-core/src/robot_core/adapters/`. Controller UR chạy lệnh chuyển động `moveJ`, `moveL` và force mode qua `ur_rtde`; drive của ray tự chạy vòng vị trí. Host là bộ giám sát chạy ở 30–50 Hz, không cần thời gian thực.
- B: ROS 2 Jazzy toàn phần: `ros2_control`, driver UR chính hãng, MoveIt 2.
- C: A cộng một container ROS 2/MoveIt làm planner, đặt sau `PlannerPort`.
- D: mỗi thiết bị một service, các service nối với nhau qua bus.

## Kết quả quyết định

Chọn phương án A, vì:

- Yếu tố quan trọng nhất là chỗ đặt thời gian thực. Mọi vòng 500 Hz nằm trong controller UR và drive của ray, nên host không cần PREEMPT_RT.
- An toàn không phụ thuộc phương án. Với phương án nào thì mọi chức năng an toàn cũng nằm ở hệ an toàn của UR, mạch E-stop/safeguard nối cứng và STO (ngắt mô-men an toàn) của ray; phần mềm trên host không phải chức năng an toàn.
- B có sẵn planner và công cụ, nhưng phải học và tích hợp nhiều nhất, driver cần thời gian thực trên host, và cần 6–9 tháng để đủ chức năng so với 3–4 tháng của A. D quá mức cho một máy, một cell. C giữ tốc độ của A và mở đường lên ROS 2, nên để dành tới khi có trigger.

Mỗi bước nâng cấp có trigger (điều kiện kích hoạt) riêng:

- Lên phương án C: hành lang tiếp cận thất bại với một xe có trong danh mục xe, hoặc có vật cản động.
- Dùng behaviour tree: nhánh phục hồi vượt quá sức của máy trạng thái (FSM) mà mission đang dùng.
- Viết C++ riêng: profile chỉ ra điểm nóng.
- Dùng PREEMPT_RT trên host: jitter đo được làm trễ hạn.

### Hệ quả

- Tốt, vì host không phải chạy kernel thời gian thực, và Jetson lẫn PC x86 dùng chung một image `core`.
- Tốt, vì phần lớn mã (mission, API, adapter mô phỏng) chạy và test được thẳng trên Windows, macOS hoặc Linux mà không cần thiết bị thật; các mức chạy và kiểm ghi ở [CONTRIBUTING.md](../../CONTRIBUTING.md).
- Xấu, vì không có planner tránh va chạm: chuyển động chỉ dựa vào hành lang tiếp cận có cấu trúc. Khi trigger lên C xảy ra thì cần thêm 1–2 tháng công sức, và từ đó phải bảo trì hai runtime.

### Xác nhận

- CI build image `core` cho amd64 và arm64 rồi gộp thành một image index; khung chạy đầu-cuối chỉ tính là xong khi image index có đủ hai kiến trúc.
- Job chạy đầu-cuối trên mô phỏng (SIM) trong CI đi qua ArmPort với adapter mô phỏng và phải xanh.
- Import `robot_core` không gây tác dụng phụ.
- ArmPort nhận lệnh segment (ADR 0004), nên vòng 500 Hz của tay máy vẫn nằm trong controller.

## Ưu và nhược của từng phương án

### Phương án A: modular monolith Python theo ports/adapters

- Tốt, vì cùng một image chạy được trên Jetson và x86.
- Tốt, vì ít phải học mới.
- Tốt, vì mô hình miền và test viết bằng Python, không gắn với framework robot nào.
- Xấu, vì không có planner tránh va chạm, chỉ dựa vào hành lang tiếp cận có cấu trúc.
- Công sức một người (ước tính): khung chạy đầu-cuối 2–3 tuần; đủ chức năng trong 3–4 tháng.

### Phương án B: ROS 2 Jazzy toàn phần

- Tốt, vì có mức đồng thuận cao nhất trong cộng đồng robotics.
- Tốt, vì có sẵn planner và công cụ.
- Xấu, vì phải học và tích hợp nhiều nhất.
- Xấu, vì driver cần thời gian thực trên host.
- Xấu, vì image lớn.
- Công sức một người (ước tính): đủ chức năng trong 6–9 tháng.

### Phương án C: A cộng planner ROS 2/MoveIt

- Tốt, vì giữ được tốc độ của A.
- Tốt, vì mở sẵn đường lên ROS 2.
- Xấu, vì phải bảo trì hai runtime.
- Công sức một người (ước tính): thêm 1–2 tháng, làm khi có trigger.

### Phương án D: mỗi thiết bị một service

- Tốt, vì cô lập từng thiết bị.
- Xấu, vì quá mức cho một máy, một cell.
- Công sức một người: không ước tính, vì phương án này không làm.

## Thông tin thêm

- ADR liên quan: 0002 (bố cục repo, ranh giới component, thuật ngữ), 0004 (chuyển động và lực chạy trên controller; ArmPort nhận lệnh segment), 0005 (phân bổ an toàn).
- Perception hiện là một module trong `robot-core`; sau này tách thành service `perception` dùng GPU, chạy image riêng. Image `core` chỉ dùng CPU.
- Chưa quyết định:
  - bản ROS 2 và MoveIt cho phương án C; `PlannerPort` chỉ cần khi lên C, chưa quyết định có khai sẵn trong `ports/` từ đầu hay không;
  - ngưỡng định lượng cho các trigger, ví dụ hành lang tiếp cận thất bại bao nhiêu lần, hay jitter được so với hạn chót nào;
  - cách kiểm tự động để module miền không gọi thẳng vào adapter.
- Nguồn:
  - [Hexagonal architecture (ports and adapters), Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/): mẫu kiến trúc của phương án A.
  - [Hướng dẫn RTDE của Universal Robots](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-guide.html) và [thư viện ur_rtde](https://gitlab.com/sdurobotics/ur_rtde): giao tiếp giữa host và controller UR.
  - [Danh sách bản phân phối ROS 2](https://raw.githubusercontent.com/ros2/ros2_documentation/rolling/source/Releases.rst), gồm Jazzy của phương án B.
  - [Real-Time Kernel trong tài liệu Jetson Linux](https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/SD/Kernel/RealTimeKernel.html): trạng thái kernel thời gian thực trên Jetson.
  - [OCI image index](https://github.com/opencontainers/image-spec/blob/main/image-index.md): một image cho nhiều kiến trúc.
