# 0004. Chuyển động và lực chạy trên controller UR, ArmPort nhận lệnh segment

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Hệ thống dùng một tay máy UR đặt trên ray để cắm đầu sạc vào xe điện rồi rút ra khi sạc xong. Service `core` chạy trên host là Jetson hoặc PC x86 chạy Linux, trong cùng một image chỉ dùng CPU. Kiến trúc theo ports/adapters ([Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/), ADR 0003): `core` điều khiển tay máy qua ArmPort, còn tay máy thật và bộ mô phỏng là các adapter của port này.

Controller của tay máy UR chạy vòng điều khiển 500 Hz ([hướng dẫn RTDE của UR](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-guide.html)). Khi cắm và rút, ngoài chuyển động còn cần điều khiển lực lúc tiếp xúc: admittance (tay máy nhường theo lực đo được) và spiral search (dò cổng sạc theo đường xoắn ốc). Nếu host tự chạy các vòng này thì phải giữ đúng hạn từng chu kỳ, tức là cần kernel thời gian thực.

Vấn đề: vòng điều khiển chuyển động và lực chạy ở đâu, trên host hay trên controller của tay máy, và vì thế ArmPort nhận lệnh ở dạng nào?

## Yếu tố quyết định

- Host không có kernel thời gian thực đạt chất lượng sản xuất: NVIDIA mới hỗ trợ kernel thời gian thực cho Jetson ở chất lượng Developer Preview ([trang Real-Time Kernel của NVIDIA](https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/SD/Kernel/RealTimeKernel.html)).
- Cùng một image `core` chỉ dùng CPU phải chạy được như nhau trên Jetson và PC x86.
- An toàn không phụ thuộc lựa chọn này: mọi chức năng an toàn nằm ở hệ an toàn của UR, mạch E-stop/safeguard 2 kênh nối cứng và STO của ray; phần mềm chỉ quan sát và yêu cầu dừng (ADR 0005).
- Mission và motion phải kiểm được khi không có tay máy, bằng adapter mô phỏng nhận cùng loại lệnh với adapter thật.
- Giao tiếp với UR dùng thư viện có người duy trì thay cho driver tự viết.

## Các phương án đã xét

- Controller UR chạy chuyển động và lực, ArmPort nhận lệnh segment
- Host chạy vòng servo và vòng lực, ArmPort nhận điểm đặt liên tục
- ROS 2 Jazzy với ros2_control và driver UR chính hãng

## Kết quả quyết định

Phương án được chọn: "Controller UR chạy chuyển động và lực, ArmPort nhận lệnh segment", vì đây là phương án duy nhất không đòi host chạy thời gian thực.

| Phần | Chạy gì |
| --- | --- |
| Controller UR | moveJ, moveL và force mode, trong vòng điều khiển 500 Hz của controller |
| Drive của ray | vòng vị trí của ray |
| Host | bộ giám sát 30–50 Hz, không cần thời gian thực |

Các đường dẫn dưới đây tính từ `robot-core/src/robot_core/`.

- ArmPort nhận lệnh segment: mỗi lệnh giao cho controller trọn một đoạn chuyển động (moveJ hoặc moveL) để controller tự chạy; host không gửi điểm đặt theo từng chu kỳ điều khiển.
- [ur_rtde](https://gitlab.com/sdurobotics/ur_rtde) (giấy phép MIT) nằm sau ArmPort, trong adapter `adapters/ur_rtde/`. Adapter mô phỏng `adapters/sim/` hiện thực cùng ArmPort và chạy cùng các lệnh segment.
- Admittance và spiral search dựng trên force mode của controller; host không chạy vòng lực. Trước hết dùng cảm biến lực tích hợp của tay máy UR.
- Lệnh giám sát đi qua Dashboard Server ở cổng 29999. Thanh ghi input của RTDE dùng dải 24–47: theo hướng dẫn RTDE của UR, với thanh ghi int và double, dải 0–23 dành cho fieldbus/PLC, dải 24–47 dành cho client RTDE bên ngoài.
- Drive của ray tự chạy vòng vị trí, `core` ra lệnh qua Modbus TCP (`adapters/modbus/`). Ray chỉ chạy khi tay máy đã thu về. STO của ray nối cứng.
- `motion/` trên host gồm motion director phát lệnh dưới dạng segment, bảng standoff, cách chọn vị trí ray, bộ kiểm segment (segment checker) và bộ giám sát tiến trình (progress monitor).
- Dữ liệu cũ, mất kết nối hoặc adapter lỗi thì dừng và vào SAFE_HOLD, trạng thái chờ an toàn. Mất thiết bị không bao giờ tự chuyển sang mô phỏng.
- Host không có watchdog an toàn bằng phần mềm: phần mềm chỉ quan sát và yêu cầu dừng, còn chức năng an toàn nằm ở phần cứng có mức an toàn.

### Hệ quả

- Tốt, vì host không cần PREEMPT_RT, nên một image `core` chạy được như nhau trên Jetson và PC x86.
- Tốt, vì adapter mô phỏng và adapter `ur_rtde` nhận cùng lệnh segment: mission và motion kiểm được ở mức 1 mà không cần tay máy, adapter `ur_rtde` kiểm được với URSim ở mức 2 (mục "Ba mức chạy và kiểm" trong [CONTRIBUTING.md](../../CONTRIBUTING.md)).
- Trung tính, vì tay máy của hãng khác UR cần adapter ArmPort riêng và phải tự kiểm chứng hệ an toàn của hãng đó.
- Xấu, vì không có planner tránh va chạm; đường đi chỉ dựa vào hành lang tiếp cận có cấu trúc.
- Xấu, vì `ur_rtde` 1.6.5 chỉ có wheel cho Python 3.7–3.12 và không có wheel arm64, nên phải build từ source, có cache, cho arm64 và cho cả amd64 nếu dùng Python 3.14; ADR 0008 chốt phiên bản Python theo kết quả build.

### Xác nhận

- Job đầu-cuối SIM trên CI chạy nhiệm vụ qua ArmPort bằng lệnh segment, với adapter mô phỏng.
- Test integration ở mức 2 nối adapter `ur_rtde` với URSim. URSim miễn phí nhưng không phải mã nguồn mở, nên chỉ dùng để test, không phát hành kèm sản phẩm.
- Test hồi quy an toàn dùng lỗi giả lập của adapter mô phỏng: dữ liệu cũ, mất kết nối và adapter lỗi đều dẫn tới dừng và SAFE_HOLD; mất adapter thật không làm `core` chuyển sang adapter mô phỏng.
- Khi review mã: không có vòng servo hay vòng lực nào chạy trên host; admittance và spiral search đi qua force mode của controller.
- Ở mức 3, trên Jetson và PC x86 thật: đo chu kỳ và jitter của vòng giám sát 30–50 Hz; kiểm admittance và spiral search bằng test `hil` trên tay máy thật.

## Ưu và nhược của từng phương án

### Controller UR chạy chuyển động và lực, ArmPort nhận lệnh segment

Controller UR chạy moveJ, moveL và force mode qua `ur_rtde`; drive của ray tự chạy vòng vị trí; host giám sát ở 30–50 Hz.

- Tốt, vì mọi vòng 500 Hz nằm ở controller UR và drive của ray, nên host không cần thời gian thực.
- Tốt, vì adapter mô phỏng chạy cùng lệnh segment với adapter thật.
- Xấu, vì không có planner tránh va chạm, chỉ dựa vào hành lang tiếp cận có cấu trúc.

### Host chạy vòng servo và vòng lực, ArmPort nhận điểm đặt liên tục

Host chạy vòng servo 125 Hz cùng admittance và spiral search, gửi điểm đặt mới xuống controller ở mỗi chu kỳ.

- Tốt, vì luật điều khiển lực nằm trong mã của dự án.
- Xấu, vì host phải giữ đúng hạn từng chu kỳ, tức là cần kernel thời gian thực (PREEMPT_RT), mà kernel thời gian thực cho Jetson mới ở chất lượng Developer Preview.

### ROS 2 Jazzy với ros2_control và driver UR chính hãng

Điều khiển đi qua ros2_control, driver UR chính hãng và MoveIt 2.

- Tốt, vì có đồng thuận cao nhất trong cộng đồng robotics, có sẵn planner và công cụ.
- Xấu, vì driver cần thời gian thực trên host.
- Xấu, vì phải học và tích hợp nhiều nhất, image lớn.

## Thông tin thêm

- Quyết định liên quan: ADR 0003 (kiến trúc modular monolith theo ports/adapters), ADR 0005 (phân bổ an toàn), ADR 0008 (môi trường dev và phiên bản công cụ), ADR 0012 (tay máy đa năng).
- Mở lại quyết định khi jitter đo được của vòng giám sát làm trễ hạn (xét PREEMPT_RT), hoặc khi hành lang tiếp cận thất bại với xe trong danh mục hay gặp vật cản động (xét thêm planner ROS 2/MoveIt đặt sau một PlannerPort).
- Model UR thật và drive của ray chưa chốt; chốt bằng kiểm kê phần cứng, trước khi viết adapter cho thiết bị thật.
- Trang của NVIDIA và hướng dẫn RTDE của UR dẫn ở trên được đọc ngày 2026-11-12.
- ADR này chưa quyết định:
  - dạng dữ liệu của một segment, và force mode đi qua ArmPort như một loại segment hay một lệnh riêng;
  - tiêu chí của bộ kiểm segment và ngưỡng của bộ giám sát tiến trình, kể cả tuổi dữ liệu bị coi là cũ và thời gian bị coi là mất kết nối;
  - cách controller dừng segment đang chạy khi mất liên lạc với host;
  - cách dựng admittance và spiral search bằng force mode;
  - lệnh jog có deadman từ HMI đi qua ArmPort ở dạng nào;
  - khi nào cần cảm biến lực ngoài thay cho cảm biến tích hợp của UR;
  - dữ liệu nào đặt vào thanh ghi nào trong dải 24–47.
