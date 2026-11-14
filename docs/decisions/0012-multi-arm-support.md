# 0012. Tay máy đa năng: model có sẵn và model custom, hồ sơ tool riêng, tính bằng Pinocchio

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Hệ thống điều khiển một tay máy UR đặt trên ray (ADR 0003). Controller của tay máy chạy chuyển động và lực, còn service `core` trên host phát lệnh segment và giám sát (ADR 0004). Host vẫn cần model động học của tay máy: module `robot-core/src/robot_core/arm/` tính FK, Jacobian và IK cho phần chuyển động chạy trên host, như kiểm segment và chọn vị trí ray trước khi giao lệnh cho controller (ADR 0002, ADR 0004).

Sản phẩm không gắn với một model tay máy cố định: trong cài đặt, người dùng chọn một model có sẵn của UR hoặc khai một model custom; model UR dùng thật cũng chưa chốt (ADR 0004). Tool gắn ở mặt bích đổi TCP và tải mà không đổi tay máy. Model hay tool khai sai làm host tính sai pose và mô-men, nên đổi model hoặc tool là thao tác liên quan an toàn (ADR 0005).

Thông số động học trong gói mô tả chính hãng của UR là giá trị mặc định, không ứng với một tay máy cụ thể nào. Chính gói ghi rằng FK theo các giá trị này sẽ lệch pose mà teach pendant (bảng điều khiển cầm tay của UR) báo, và muốn có phép biến đổi đúng cho từng tay máy thì phải dùng thông số của chính tay máy đó ([`urdf/ur_macro.xacro`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/urdf/ur_macro.xacro)).

Model tay máy lấy thông số từ đâu và nằm ở đâu, model custom được nhận với điều kiện gì, tool được mô tả ra sao, model trên host được giữ khớp với tay máy thật bằng cách nào, và động học tính bằng gì?

## Yếu tố quyết định

- Đổi model tay máy hoặc tool là thao tác liên quan an toàn, cần vai trò nâng quyền, xác thực lại và nhật ký kiểm toán (ADR 0005).
- Pose mà host tính phải cùng frame và cùng thông số với pose mà controller báo, kể cả thông số hiệu chuẩn riêng của từng tay máy.
- Thông số của model có sẵn truy được tới nguồn chính hãng, và mọi nơi dùng URDF, từ mã tới test, dùng cùng một bản.
- Mô-men trọng lực tính theo thông số vật lý mà hãng công bố.
- Một tay máy dùng được nhiều tool mà không phải đổi model.
- File URDF người dùng tải lên là đầu vào không tin cậy.
- Động học và động lực học dùng thư viện có người duy trì; dự án chỉ tự viết phần thư viện không có sẵn.
- Phần mềm không phải chức năng an toàn (ADR 0005): phép kiểm của ứng dụng không thay cho giới hạn trong cấu hình an toàn của UR.

## Các phương án đã xét

Chỉ các phần dưới đây có hơn một phương án; các phần khác của quyết định chỉ có một phương án được ghi lại.

- Thư viện tính động học và động lực học:
  - A1. Pinocchio
  - A2. Tự viết FK, Jacobian và động lực học
- Nguồn URDF của model có sẵn:
  - B1. Sinh bằng xacro từ gói mô tả chính hãng, ghim theo tag và commit
  - B2. Sinh từ gói mô tả chính hãng theo nhánh mới nhất, không ghim
- Thông số quán tính của các khâu:
  - C1. Thông số vật lý của hãng
  - C2. Khối lượng của hãng đặt ở trung điểm hai gốc khớp DH của mỗi khâu
- Frame gốc của model:
  - D1. Frame `base`, trùng base của controller
  - D2. Frame `base_link` của URDF
- Tải và TCP của tool:
  - E1. Hồ sơ tool riêng, đặt xuống controller rồi đọc lại
  - E2. Tải và TCP ghi trong model tay máy

## Kết quả quyết định

Chọn A1, B1, C1, D1 và E1, vì:

- A1: Pinocchio là thư viện có người duy trì, tính FK, Jacobian và động lực học thẳng từ URDF, nên dự án chỉ còn tự viết vòng IK; A2 buộc dự án tự viết và tự kiểm toàn bộ phần này.
- B1: từ cùng một commit và cùng phiên bản xacro, lần sinh nào cũng cho cùng URDF, nên mã, test và các phép kiểm chứng dùng cùng một bản; với B2, URDF đổi theo mỗi thay đổi trên nhánh của gói.
- C1: đặt trọng tâm mỗi khâu ở trung điểm hai gốc khớp DH thay cho trọng tâm hãng công bố làm mô-men trọng lực lệch tới khoảng 10%: ở khớp `shoulder_lift_joint` của UR20, lệch tới 33 N·m, trong khi mô-men trọng lực lớn nhất của khớp này là 315 N·m. Hai số này tính bằng Pinocchio ngày 2026-11-12 trên cùng 1000 cấu hình phân bố đều trong giới hạn khớp, hai bên cùng khối lượng khâu của hãng.
- D1: `base_link` của URDF lệch base của controller 180° quanh trục z, nên pose đo từ `base_link` sai hướng 180° so với pose controller báo.
- E1: một tay máy đổi được tool mà không đổi model; pose mà controller báo là pose của TCP đang đặt trên controller, nên TCP và tải trên host và trên controller phải là một thì phép kiểm FK ở dưới mới có nghĩa.

**Model có sẵn.** Danh sách bắt đầu với UR5e, UR10e, UR16e, UR20 và UR30. Mỗi model một thư mục `robot-core/src/robot_core/defaults/arms/<model>/` gồm:

- `model.urdf`, sinh bằng xacro từ `urdf/ur.urdf.xacro` của gói mô tả chính hãng [Universal_Robots_ROS2_Description](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description), ghim tag [`4.4.1`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/tree/4.4.1), commit [`0eb1a861f7772fceb38510d90fa2f98ec668070c`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/commit/0eb1a861f7772fceb38510d90fa2f98ec668070c), giấy phép BSD-3-Clause, với tham số mặc định của gói (`default_kinematics.yaml`, `physical_parameters.yaml`, `joint_limits.yaml` trong thư mục `config/` của model đó), giữ nguyên đầu ra của xacro, kể cả phần visual và collision trỏ tới mesh của gói: Pinocchio chỉ đọc cây khớp và quán tính, còn tham chiếu mesh không kéo file mesh nào vào repo;
- `spec.yaml`: tầm với và tải theo bảng thông số kỹ thuật của UR, adapter ArmPort dùng cho model, cùng giới hạn vị trí, tốc độ và mô-men của các khớp lấy từ `joint_limits.yaml` của gói, nên bằng đúng giới hạn trong `model.urdf`.

URDF sinh ra được kê trong `third_party/assets.yaml` cùng nguồn, giấy phép và cách sinh, gồm phiên bản xacro và PyYAML đã dùng; văn bản BSD-3-Clause nằm trong `third_party/licenses/` (ADR 0010, ADR 0011). Mesh dùng cho twin 3D kiểm giấy phép riêng và có `nc: true` nếu chỉ được dùng cho mục đích phi thương mại (ADR 0011).

**Model custom.** Model custom được khai trong cài đặt và lưu trong volume `ev-arm-config` (ADR 0007).

- Model dựng từ bảng DH hoặc từ file URDF người dùng tải lên.
- File tải lên được parse an toàn, chống được tấn công qua thực thể ngoài (XXE) và mở rộng thực thể ([OWASP XML External Entity Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)), có giới hạn kích thước, và phải mô tả một chuỗi khớp hợp lệ; không đạt một trong các điều này thì file bị từ chối.
- Model thiếu thông số quán tính chỉ bật phần hình học (FK, IK, Jacobian); các chức năng cần động lực học bị tắt.
- Model custom không gắn adapter ArmPort nào chỉ chạy được với adapter mô phỏng (SIM).

**Hồ sơ tool** gồm offset TCP, khối lượng và trọng tâm, tách riêng khỏi model tay máy. Hồ sơ mặc định nằm ở `robot-core/src/robot_core/defaults/tools/`, hồ sơ người dùng tạo nằm trong volume `ev-arm-config` (ADR 0007). Hồ sơ được đặt xuống controller rồi đọc lại để so khớp.

**Đổi model hoặc tool** là thao tác liên quan an toàn (ADR 0005):

- cần vai trò bảo trì và xác thực lại; mỗi lần đổi ghi một dòng nhật ký kiểm toán;
- FK trên host được so với pose mà controller báo, tại pose hiện tại và tại các pose đi qua khi chạy tay (jog); lệch vượt ngưỡng thì đầu ra chuyển động bị khoá;
- phép kiểm này và việc khoá đầu ra chuyển động nằm trong phần mềm nên không phải chức năng an toàn; giới hạn an toàn vẫn nằm trong cấu hình an toàn của UR (ADR 0005).

**Ngưỡng của phép kiểm FK** (Status: proposed): khởi điểm 1 mm cho vị trí và 0,1° cho hướng; khi phần này chưa đóng, phép kiểm dùng ngưỡng khởi điểm. Phần này đóng khi độ lệch giữa FK và pose controller được đo trên tay máy thật (mức 3 trong [CONTRIBUTING.md](../../CONTRIBUTING.md)) và ngưỡng chỉnh theo số đo được ghi vào ADR này. Tại ngày ghi ADR, chưa có số đo.

**Khung toạ độ.** Model lấy frame `base` của URDF làm gốc; frame này trùng base của controller. Không dùng `base_link`: frame này theo quy ước REP-103 (trục x hướng trước, y sang trái, z lên trên), còn `base` là `base_link` quay π quanh trục z để trùng base của controller, như ghi chú trong `urdf/ur_macro.xacro`. Mặt bích là frame `tool0`, frame tool có mọi offset bằng 0 của gói; TCP tính từ `tool0` theo hồ sơ tool.

**Hiệu chuẩn riêng từng tay máy.** Adapter UR đọc thông số hiệu chuẩn động học của tay máy từ controller qua primary interface ở cổng chỉ đọc 30011 ([bảng cổng giao tiếp của UR](https://www.universal-robots.com/articles/ur/interface-communication/remote-control-via-tcpip/)), áp vào model và ghi lại checksum của bộ thông số đó. Định dạng gói dữ liệu này còn phải kiểm lại (mục Thông tin thêm).

**IK.** Dự án tự viết vòng IK kiểu DLS (damped least squares) trên Jacobian của Pinocchio, dùng chung cho mọi model, kể cả model custom, có xử lý giới hạn khớp. [Ví dụ IK của Pinocchio 4.1.0](https://github.com/stack-of-tasks/pinocchio/blob/v4.1.0/examples/inverse-kinematics.py) tính bước theo cùng cách nhưng không xử lý giới hạn khớp.

**Hãng khác UR.** Tay máy của hãng khác cần adapter ArmPort riêng và phải tự kiểm chứng hệ an toàn của hãng đó (ADR 0004, ADR 0005).

### Hệ quả

- Ưu: model có sẵn truy được tới một commit của gói chính hãng, và mã, test cùng dùng một URDF.
- Ưu: mô-men trọng lực theo khối lượng và trọng tâm hãng công bố, không mang sai số tới khoảng 10% của cách đặt trọng tâm ở trung điểm.
- Ưu: pose trên host và pose controller báo cùng frame; model, tool hay hiệu chuẩn lệch với tay máy thật bị phát hiện bằng phép kiểm FK ngay khi đổi model hoặc tool.
- Ưu: đổi tool không phải đổi model, và một vòng IK dùng cho mọi model.
- Nhược: `pin` chỉ khai cho Linux, nên trên Windows và macOS, test động học chỉ chạy được qua Docker (mức 2) hoặc trên job Linux của CI (ADR 0008).
- Nhược: vòng IK tự viết phải tự kiểm và tự bảo trì: hội tụ, điểm kỳ dị, giới hạn khớp.
- Nhược: nâng gói mô tả lên tag khác là đổi quyết định này, nên cần một ADR mới thay ADR này, sinh lại mọi `model.urdf` và chạy lại các test kiểm chứng.
- Nhược: mỗi lần đổi model hoặc tool cần người có vai trò bảo trì xác thực lại; phép kiểm FK chỉ phủ pose hiện tại và các pose đi qua khi chạy tay, không phủ cả vùng làm việc.
- Nhược: model custom thiếu quán tính không dùng được các chức năng cần động lực học, và model custom không có adapter chỉ chạy trong SIM.
- Trung tính: tay máy của hãng khác UR cần adapter ArmPort riêng và tự kiểm chứng hệ an toàn của hãng đó.

### Xác nhận

- Commit đổi hành vi ở scope `arm` phải có label Why, How và Test ([CONTRIBUTING.md](../../CONTRIBUTING.md), mục "Body").
- Test cho từng model có sẵn, với dung sai theo REQ-ARM-023 ([mission-motion-arm.md](../requirements/mission-motion-arm.md)); các test này cần Pinocchio nên chỉ chạy trên Linux, kể cả qua Docker ở mức 2, và job Linux của CI coi test bị bỏ qua là lỗi (ADR 0008):
  - FK của `tool0` trong `base`, tính bằng Pinocchio trên `model.urdf`, so với FK tính theo bảng DH trong [bài DH của UR](https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/). Phép so này giữ luôn frame: khung 0 của bảng DH trùng `base`, không trùng `base_link`. Gói ghi góc α đã làm tròn tới 9 chữ số thập phân (`1.570796327` trong [`config/ur5e/default_kinematics.yaml`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/config/ur5e/default_kinematics.yaml)) còn bảng DH dùng π/2, nên hai bên lệch cỡ 10⁻¹⁰ m và 10⁻¹⁰ rad; dung sai của phép so phải lớn hơn mức này.
  - Jacobian của Pinocchio so với sai phân hữu hạn của FK.
  - Mô-men trọng lực của Pinocchio so với mô-men tính bằng công thức tĩnh từ khối lượng và trọng tâm các khâu theo thông số của hãng.
- Test của model custom: file vượt giới hạn kích thước, file không parse an toàn được và file không mô tả chuỗi khớp hợp lệ đều bị từ chối; model thiếu quán tính chỉ có FK, IK và Jacobian; model không có adapter không chọn được khi đang dùng adapter thật.
- Test của IK: nghiệm trả về không vượt giới hạn khớp của model.
- Test API: đổi model hoặc tool bị từ chối khi thiếu vai trò bảo trì hoặc chưa xác thực lại; mỗi lần đổi thêm một dòng nhật ký kiểm toán.
- Test với adapter mô phỏng: FK lệch pose mà adapter báo quá ngưỡng thì đầu ra chuyển động bị khoá.
- Ở mức 2, adapter UR nối với URSim: hồ sơ tool đặt xuống controller rồi đọc lại khớp với hồ sơ đã đặt.
- Ở mức 3, bằng test `hil` trên tay máy thật: đọc được thông số hiệu chuẩn qua cổng 30011; đo độ lệch giữa FK và pose controller để chỉnh ngưỡng (phần đề xuất ở trên).
- Tại ngày ghi ADR, `arm/`, `defaults/arms/` và `defaults/tools/` chưa có code, nên chưa có test nào ở trên.

## Ưu và nhược của từng phương án

### A1. Pinocchio

[Pinocchio](https://github.com/stack-of-tasks/pinocchio), giấy phép BSD-2-Clause theo file [`LICENSE` ở tag v4.1.0](https://github.com/stack-of-tasks/pinocchio/blob/v4.1.0/LICENSE), gói `pin` 4.1.0 (ADR 0008). Metadata của gói `pin` 4.1.0 trên PyPI ghi `BSD-3-Clause`, khác file `LICENSE`; khi liệt kê giấy phép, dự án ghi theo file `LICENSE`.

- Ưu: thư viện có người duy trì, đọc thẳng URDF và tính FK, Jacobian cùng động lực học, trong đó có mô-men trọng lực.
- Ưu: một model URDF dùng cho mọi phép tính, không phải chép thông số sang bảng riêng.
- Nhược: `pin` chỉ khai cho Linux, nên trên Windows và macOS, test động học bị bỏ qua ở mức 1 (ADR 0008).
- Trung tính: IK vẫn do dự án tự viết trên Jacobian của thư viện.

### A2. Tự viết FK, Jacobian và động lực học

- Ưu: không thêm dependency, chạy được ở mức 1 trên mọi hệ điều hành.
- Nhược: toàn bộ thuật toán và test do dự án tự viết, tự kiểm và tự bảo trì.
- Nhược: thông số mỗi model phải chép từ URDF hay bảng DH sang dạng riêng, thêm một chỗ có thể lệch nguồn chính hãng.

### B1. Sinh bằng xacro từ gói mô tả chính hãng, ghim theo tag và commit

- Ưu: từ cùng commit và cùng phiên bản xacro, lần sinh nào cũng cho cùng URDF; mã, test và các phép kiểm chứng dùng cùng một bản.
- Ưu: nguồn và giấy phép của URDF ghi được chính xác tới commit.
- Nhược: bản sửa của gói ra sau commit đã ghim không tự vào repo; muốn dùng thì phải nâng ghim bằng một ADR mới.

### B2. Sinh từ gói mô tả chính hãng theo nhánh mới nhất, không ghim

- Ưu: luôn có bản sửa mới nhất của gói.
- Nhược: hai lần sinh ở hai thời điểm có thể cho hai URDF khác nhau, nên không biết chắc mã và test đang dùng bản nào.

### C1. Thông số vật lý của hãng

Khối lượng, trọng tâm và ma trận quán tính của từng khâu lấy từ `physical_parameters.yaml` của gói mô tả; trọng tâm trong file này được quy từ bài DH của UR, như ghi chú trong file.

- Ưu: mô-men trọng lực khớp với khối lượng và trọng tâm hãng công bố.
- Nhược: số liệu của hãng chưa được đối chiếu với tay máy thật, và với UR20, khâu wrist_3 trong gói lệch bài DH của UR (mục Thông tin thêm).

### C2. Khối lượng của hãng đặt ở trung điểm hai gốc khớp DH của mỗi khâu

- Ưu: chỉ cần bảng DH và khối lượng khâu, nên dùng được cho mọi model có bảng DH, kể cả model custom.
- Nhược: mô-men trọng lực lệch tới khoảng 10% so với dùng trọng tâm hãng công bố, tới 33 N·m ở khớp `shoulder_lift_joint` của UR20.

### D1. Frame `base`, trùng base của controller

- Ưu: pose tính trên host so thẳng được với pose controller báo, không cần đổi frame.
- Ưu: khung 0 của bảng DH của hãng trùng `base`, nên phép so FK với bảng DH dùng luôn frame này.

### D2. Frame `base_link` của URDF

- Ưu: theo quy ước REP-103 mà các công cụ ROS dùng.
- Nhược: lệch base của controller 180° quanh trục z, nên so thẳng với pose controller thì sai hướng 180°.

### E1. Hồ sơ tool riêng, đặt xuống controller rồi đọc lại

- Ưu: đổi tool không đổi model tay máy, và một hồ sơ tool dùng được với nhiều model.
- Ưu: đọc lại sau khi đặt cho biết controller đang dùng đúng TCP và tải mà host dùng.
- Nhược: thêm một loại cấu hình phải quản lý, và đổi tool cũng là thao tác liên quan an toàn.

### E2. Tải và TCP ghi trong model tay máy

- Ưu: chỉ một loại cấu hình cho cả tay máy và tool.
- Nhược: đổi tool thành đổi model, hoặc phải có một bản model cho mỗi cặp tay máy và tool.

## Thông tin thêm

- ADR liên quan: 0002 (bố cục repo, gồm `arm/`, `defaults/arms/`, `defaults/tools/`), 0004 (chuyển động chạy trên controller, ArmPort, adapter `ur_rtde`), 0005 (phân bổ an toàn, thao tác liên quan an toàn), 0007 (model custom và hồ sơ tool trong volume `ev-arm-config`), 0008 (Pinocchio chỉ khai cho Linux), 0010 và 0011 (tài sản không phải code, giấy phép của URDF và mesh). "Model" trong ADR 0015 là model nhận dạng, khác model tay máy ở đây.
- Không có phép so sánh nào được ghi lại giữa vòng IK DLS với IK giải tích hay một thư viện IK khác, cũng như cho cách xử lý model custom thiếu quán tính hoặc không có adapter.
- Dữ kiện về gói mô tả tại commit đã ghim:
  - Riêng UR20, khâu wrist_3 trong [`config/ur20/physical_parameters.yaml`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/config/ur20/physical_parameters.yaml) có khối lượng 0,926 kg và trọng tâm (0; 0; −0,0293) m, còn bài DH của UR ghi 0,846 kg và (0; −0,0003; −0,0318) m; hai số của gói trùng số bài DH ghi cho khâu cuối của UR30.
  - Gói giới hạn khớp khuỷu (`elbow_joint`) ở ±π, bằng một nửa giới hạn thật của khớp; theo ghi chú trong gói, cấu tạo tay máy không cho khuỷu quay quá khoảng ±π.
  - [`config/ur30/joint_limits.yaml`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/config/ur30/joint_limits.yaml) ghi nguồn là user manual của UR20, bản 5.14.
  - [README của gói](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/README.md) ghi mesh của một số model, trong đó có UR20 và UR30, theo điều khoản "Graphical Documentation" của UR, không theo BSD-3-Clause.
- Nguồn, đọc ngày 2026-11-12:
  - [Universal_Robots_ROS2_Description](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description): gói mô tả chính hãng của UR, giấy phép BSD-3-Clause trừ các mesh nêu trên; [`urdf/ur_macro.xacro`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description/blob/0eb1a861f7772fceb38510d90fa2f98ec668070c/urdf/ur_macro.xacro) ghi frame `base`, `tool0` và việc thông số mặc định không ứng với tay máy cụ thể.
  - [DH Parameters for calculations of kinematics and dynamics](https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics/): bảng DH, khối lượng, trọng tâm và ma trận quán tính các khâu do UR công bố.
  - [Bảng cổng giao tiếp của UR](https://www.universal-robots.com/articles/ur/interface-communication/remote-control-via-tcpip/): cổng 30011 thuộc primary interface, chỉ gửi trạng thái, không nhận lệnh.
  - [Pinocchio](https://github.com/stack-of-tasks/pinocchio) và [ví dụ IK ở tag v4.1.0](https://github.com/stack-of-tasks/pinocchio/blob/v4.1.0/examples/inverse-kinematics.py).
  - [xacro](https://github.com/ros/xacro): công cụ sinh URDF từ macro XML.
  - [OWASP XML External Entity Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html): tấn công qua thực thể ngoài và mở rộng thực thể khi parse XML không tin cậy.
- Chưa quyết định:
  - UR20 dùng khối lượng và trọng tâm khâu wrist_3 theo gói hay theo bài DH của UR, và test mô-men trọng lực đối chiếu với nguồn nào; chốt trước khi thêm UR20 vào `defaults/arms/`.
  - Giới hạn trong `spec.yaml` liên hệ thế nào với application limits ở ADR 0005.
  - Lệnh hay script sinh `model.urdf`, và có kiểm tự động rằng sinh lại từ commit đã ghim cho đúng file trong repo hay không; hiện cách sinh chỉ được ghi bằng lời trong `third_party/assets.yaml`.
  - Định dạng gói hiệu chuẩn động học mà controller gửi qua cổng 30011 và cách áp vào model; kiểm trên controller thật trước khi viết phần đọc gói này.
  - Bảng DH của model custom theo quy ước DH chuẩn hay DH cải tiến, số khớp được nhận, giới hạn kích thước file URDF, và dạng lưu model custom trong `ev-arm-config`.
  - Danh sách chức năng cần động lực học, bị tắt khi model thiếu quán tính, và cách cộng tải của tool vào mô-men trọng lực.
  - Hồ sơ tool đọc lại không khớp thì xử lý thế nào, và so khớp với dung sai nào.
  - Điều kiện mở lại đầu ra chuyển động đã bị khoá vì vượt ngưỡng; bật đầu ra chuyển động đã là thao tác liên quan an toàn ở ADR 0005.
  - Model nào được chọn khi thiết bị mới cài, khi model UR dùng thật chưa chốt (ADR 0004).
