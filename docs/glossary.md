# Thuật ngữ

Mỗi mục ghi từ tiếng Việt, từ tiếng Anh và nghĩa của từ đó trong repo. Tài liệu, mã và chuỗi hiển thị trong `locales/` dùng các từ này theo đúng nghĩa ghi ở đây ([ADR 0002](decisions/0002-repository-layout.md)).

- Tên tiếng Anh của thuật ngữ robot theo [ISO 8373](https://committee.iso.org/standard/75539.html), tên hệ toạ độ theo [ISO 9787](https://committee.iso.org/standard/59444.html); mục lấy tên từ chuẩn ghi tên chuẩn đó ở cột Nghĩa. Định nghĩa do dự án viết, không chép nguyên văn chuẩn.
- Từ tiếng Việt là lựa chọn của dự án. [TCVN 13228:2025](https://thuvienphapluat.vn/TCVN/Dien-dien-tu/TCVN-13228-2025-ISO-8373-2021-Ro-bot-Tu-vung-921883.aspx) là bản tiếng Việt tương đương ISO 8373:2021; từ tiếng Việt trong bảng chưa được đối chiếu với tiêu chuẩn này.
- Văn bản tiếng Việt của repo giữ nguyên một số từ tiếng Anh, như service, container, segment, bay. Định danh trong mã, như `SAFE_HOLD`, `base`, `tool0`, giữ nguyên ở mọi ngôn ngữ.
- Mục có quyết định gốc trong ADR ghi số ADR đó; mục lục ADR ở [decisions/README.md](decisions/README.md).

## Repo và triển khai

| Tiếng Việt | English | Nghĩa |
| --- | --- | --- |
| hệ thống | system | Toàn bộ sản phẩm (ADR 0002). |
| thành phần | component | Một trong ba phần mã có manifest, công cụ và nơi chạy riêng: `robot-core`, `operator-ui`, `training` (ADR 0002). |
| service | service | Đơn vị chạy khai trong Docker Compose: `core`, `hmi`, `perception`. Service `hmi` phục vụ bản build của `operator-ui`; `perception` hiện là module của `robot-core`, sau này tách thành service (ADR 0002). Dịch vụ cập nhật chạy trên host (`deploy/host/updater/`, ADR 0013) không phải service theo nghĩa này. |
| container | container | Một bản đang chạy của một service (ADR 0002). |
| module, package | module, package | Thư mục mã bên trong `robot-core/src/robot_core/`, ví dụ `mission/`, `motion/` (ADR 0002). |
| C4 container | C4 container | Container theo [mô hình C4](https://c4model.com/): một ứng dụng hay một kho dữ liệu chạy và triển khai riêng; khác với Docker container. Tài liệu kiến trúc luôn ghi đủ "C4 container" (ADR 0002). |
| host | host | Máy tính đặt tại chỗ, chạy phần mềm bằng Docker: Jetson khi cần GPU, hoặc PC Linux x86. Host nối với controller của tay máy, drive của ray, camera và bộ sạc, đồng thời phục vụ HMI (ADR 0003). |
| giao diện vận hành (HMI) | human-machine interface (HMI) | Giao diện của người vận hành, chạy trong trình duyệt: component `operator-ui`, do service `hmi` phục vụ (ADR 0006). |
| port | port | Giao diện tới thiết bị mà module miền dùng, khai trong `robot-core/src/robot_core/ports/`, ví dụ ArmPort (ADR 0002, ADR 0003). |
| adapter | adapter | Hiện thực của một port cho một thiết bị cụ thể hoặc cho mô phỏng, nằm trong `robot-core/src/robot_core/adapters/`, ví dụ `adapters/ur_rtde/`, `adapters/sim/` (ADR 0002). |

## Tay máy và toạ độ

| Tiếng Việt | English | Nghĩa |
| --- | --- | --- |
| tay máy | manipulator (robot arm) | Cơ cấu gồm chuỗi khâu nối với nhau bằng khớp, dùng để cầm hoặc di chuyển vật hay tool (ISO 8373). Hệ thống dùng một tay máy UR đặt trên ray (ADR 0004). |
| khâu | link | Thân cứng nối hai khớp liền nhau của tay máy (ISO 8373). |
| khớp | joint | Chỗ nối hai khâu, cho khâu này quay hoặc trượt so với khâu kia (ISO 8373). |
| đế | base | Phần đỡ mà khâu đầu tiên của tay máy gắn vào (ISO 8373). Ray dời đế của tay máy (ADR 0005). |
| mặt bích | mechanical interface (flange) | Mặt lắp ở đầu khâu cuối của tay máy, nơi gắn tool (ISO 8373). |
| tool | end effector (tool) | Thiết bị gắn vào mặt bích để tay máy làm được việc của nó (ISO 8373). |
| tư thế | pose | Vị trí và hướng của một vật hay một khung toạ độ, tính trong một khung tham chiếu (ISO 8373). |
| controller | controller | Bộ điều khiển đi kèm tay máy. Controller UR chạy vòng điều khiển 500 Hz và chạy moveJ, moveL, force mode; host ra lệnh cho nó qua thư viện `ur_rtde` (ADR 0004). |
| ray | rail | Trục tuyến tính mang tay máy. Drive của ray tự chạy vòng vị trí, `core` ra lệnh qua Modbus TCP; ray chỉ chạy khi tay máy đã thu về (ADR 0004). |
| model tay máy | arm model | Mô tả một loại tay máy. Model có sẵn nằm ở `robot-core/src/robot_core/defaults/arms/<model>/`, gồm `model.urdf` và `spec.yaml` (ADR 0002, ADR 0012); model custom nằm trong volume `ev-arm-config` (ADR 0007). Khác với model học máy. |
| hồ sơ tool | tool profile | Mô tả một tool: độ lệch của TCP so với khung `tool0`, khối lượng, trọng tâm; tách riêng khỏi model tay máy. Hồ sơ có sẵn nằm ở `robot-core/src/robot_core/defaults/tools/` (ADR 0002, ADR 0012). |
| khung `base` | `base` frame | Hệ toạ độ đế (base coordinate system, ISO 9787) của model tay máy, trùng với khung base mà controller UR dùng khi báo pose; pose trong repo tính theo khung này. Khung `base_link` trong URDF của UR quay 180° quanh trục z so với `base`, nên không dùng làm khung tham chiếu (ADR 0012). |
| khung `tool0` | `tool0` frame | Hệ toạ độ mặt bích (mechanical interface coordinate system, ISO 9787) của model tay máy: gốc ở tâm mặt bích, trục z vuông góc với mặt bích, hướng ra khỏi tay máy. Khung này chưa tính tool (ADR 0012). |
| TCP | tool centre point (TCP) | Điểm xác định cho từng ứng dụng, tính theo hệ toạ độ mặt bích (ISO 8373). Độ lệch của TCP so với khung `tool0` ghi trong hồ sơ tool (ADR 0012). |
| động học thuận (FK) | forward kinematics (FK) | Tính tư thế của một khung trên tay máy, ví dụ `tool0` hay TCP, từ vị trí các khớp. |
| động học nghịch (IK) | inverse kinematics (IK) | Tính vị trí các khớp để đạt một tư thế cho trước. Repo giải IK bằng damped least squares (DLS) trên Jacobian, tính bằng Pinocchio (ADR 0002). |

## Chuyển động

| Tiếng Việt | English | Nghĩa |
| --- | --- | --- |
| segment | segment | Một đoạn chuyển động trọn vẹn, moveJ hoặc moveL, mà ArmPort giao cho controller tự chạy; host không gửi điểm đặt theo từng chu kỳ điều khiển (ADR 0004). |
| force mode | force mode | Chế độ điều khiển theo lực của controller UR. Admittance và spiral search dựng trên force mode; host không chạy vòng lực (ADR 0004). |
| admittance | admittance | Cách điều khiển lúc tiếp xúc, trong đó tay máy nhường theo lực đo được (ADR 0004). |
| spiral search | spiral search | Dò cổng sạc theo đường xoắn ốc khi cắm đầu sạc (ADR 0004). |
| chạy tay | jog | Người vận hành điều khiển trực tiếp chuyển động của tay máy từ HMI; chỉ chạy khi đang giữ deadman (ADR 0006). |
| deadman | deadman | Tín hiệu người vận hành phải giữ suốt lúc chạy tay; buông ra hoặc mất tín hiệu thì jog dừng. Deadman nằm trong phần mềm nên không phải chức năng an toàn (ADR 0006). |

## Sạc và nhận dạng

| Tiếng Việt | English | Nghĩa |
| --- | --- | --- |
| cell | cell | Khu làm việc của tay máy. Hệ thống có quy mô một máy, một cell (ADR 0003); mạng của cell tách riêng, chỉ host tới được (ADR 0006). |
| bay | bay | Chỗ đỗ của một xe để tay máy cắm đầu sạc; một cell có thể có nhiều bay. |
| bộ sạc (EVSE) | EV supply equipment (EVSE) | Thiết bị lấy điện từ hệ thống điện cố định để cấp cho xe điện khi sạc ([IEC 61851-1](https://webstore.iec.ch/en/publication/33644)). `core` làm việc với bộ sạc qua port `Evse` (ADR 0002). |
| đầu sạc | vehicle connector | Đầu cuối cáp sạc của bộ sạc, cắm vào cổng sạc của xe (IEC 61851-1). Tay máy cắm đầu sạc vào xe rồi rút ra khi sạc xong (ADR 0004). |
| cổng sạc | vehicle inlet | Phần gắn trên xe để nhận đầu sạc (IEC 61851-1). Module perception nhận dạng cổng sạc trên ảnh camera và tính tư thế của nó (ADR 0015). |
| model học máy | ML model | Model mà thiết bị chạy bằng ONNX Runtime, như model keypoint cổng sạc và model làm mờ mặt người, biển số (ADR 0010). Khác với model tay máy. |
| model nhận dạng | recognition model | Model học máy mà module perception dùng để nhận dạng cổng sạc, train trong `training/` (ADR 0015). |

## An toàn và vận hành

| Tiếng Việt | English | Nghĩa |
| --- | --- | --- |
| người vận hành | operator | Người được giao khởi động, theo dõi và dừng hoạt động của hệ thống (ISO 8373). |
| chức năng an toàn | safety function | Chức năng của máy mà khi hỏng có thể làm rủi ro tăng ngay ([ISO 13849-1](https://committee.iso.org/standard/73481.html)). Trong hệ thống, chức năng an toàn chỉ nằm ở phần cứng có mức an toàn (PL): hệ an toàn của tay máy UR, mạch dừng khẩn cấp và mạch safeguard 2 kênh nối cứng, STO của ray. Phần mềm, HMI, perception, mạng và Docker không phải chức năng an toàn (ADR 0005). |
| dừng khẩn cấp | emergency stop (E-stop) | Chức năng dừng máy để tránh hay giảm nguy hiểm, kích bằng một thao tác của người trên thiết bị dừng khẩn cấp vật lý ([ISO 13850](https://committee.iso.org/standard/59970.html)). Mạch dừng khẩn cấp nối cứng vào I/O an toàn của UR; chỉ nút reset vật lý xoá được chốt, và reset không tự cho máy chạy lại (ADR 0005). |
| Dừng | Stop | Lệnh dừng của phần mềm, như nút "Dừng" trên HMI; phục vụ vận hành, không phải chức năng an toàn. Chuỗi hiển thị không gọi nút này là "Dừng khẩn cấp", "E-Stop" hay "Emergency Stop" (ADR 0005). |
| dừng bảo vệ | protective stop | Dừng chuyển động vì mục đích bảo vệ khi thiết bị bảo vệ như rào hay scanner tác động; khác với dừng khẩn cấp. Các ADR gọi mạch này là mạch safeguard; mạch safeguard 2 kênh nối cứng vào I/O an toàn của UR (ADR 0005). |
| ngắt mô-men an toàn (STO) | safe torque off (STO) | Chức năng an toàn của drive, cắt năng lượng tạo mô-men tới động cơ. STO của ray nối cứng, và đầu ra an toàn của UR cắt STO của ray (ADR 0005). |
| giới hạn của ứng dụng | application limits | Giới hạn mà phần mềm áp cho ứng dụng, chỉ được hẹp hơn giới hạn an toàn trong cấu hình an toàn của UR. Cấu hình trạm chỉ được thu hẹp giới hạn, không được nới (ADR 0005). |
| trạng thái chờ an toàn (`SAFE_HOLD`) | safe hold (`SAFE_HOLD`) | Trạng thái chờ của phần mềm sau khi dừng. Phần mềm dừng và vào `SAFE_HOLD` khi dữ liệu cũ, mất kết nối hoặc adapter lỗi, và vào `SAFE_HOLD` mỗi lần khởi động. Đây là trạng thái phục vụ vận hành, không phải chức năng an toàn (ADR 0004, ADR 0005). |
| thao tác liên quan an toàn | safety-related operation | Đổi cấu hình an toàn, đổi model tay máy hoặc tool, cập nhật, bật đầu ra chuyển động. Mỗi thao tác cần vai trò nâng quyền, xác thực lại và ghi nhật ký kiểm toán (ADR 0005). |
