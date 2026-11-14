# Danh mục port

Port là giao diện mà module miền của `robot-core` dùng để làm việc với thiết bị, khai trong `robot-core/src/robot_core/ports/`; adapter trong `robot-core/src/robot_core/adapters/` hiện thực port cho từng thiết bị và cho mô phỏng, theo mô hình [ports and adapters](https://alistair.cockburn.us/hexagonal-architecture/) ([ADR 0002](../decisions/0002-repository-layout.md), [ADR 0003](../decisions/0003-architecture-modular-monolith.md)). Module miền chỉ gọi port, không gọi thẳng adapter.

`ports/` là hợp đồng công khai: thay đổi làm hỏng adapter hay module đang dùng một port là thay đổi không tương thích, theo mục "Thay đổi không tương thích" của [CONTRIBUTING.md](../../CONTRIBUTING.md).

Tài liệu này kê bảy port của ADR 0002: mục đích, thao tác kèm đơn vị và khung toạ độ, hành vi khi lỗi và adapter hiện thực. Hành vi chi tiết nằm ở requirement được dẫn theo ID, chủ yếu trong [perception-calibration-hardware.md](../requirements/perception-calibration-hardware.md) và [mission-motion-arm.md](../requirements/mission-motion-arm.md); mã lỗi nằm trong danh mục [`contracts/schemas/error-codes.schema.json`](../../contracts/schemas/error-codes.schema.json).

## Tổng quan

| Port | Mục đích | Adapter thiết bị | Adapter mô phỏng |
| --- | --- | --- | --- |
| ArmPort | giao segment cho controller của tay máy, đọc trạng thái tay máy | `ur_rtde/` | `sim/` |
| Rail | ra lệnh cho drive của ray, đọc vị trí ray | `modbus/` | `sim/` |
| Io | đọc tín hiệu rời rạc của trạm, ghi đèn tháp và chốt khoá đầu sạc | `modbus/`; giao thức khác chọn theo kiểm kê phần cứng | `sim/` |
| Force | đọc lực và mô-men tiếp xúc | `ur_rtde/` (cảm biến lực tích hợp của UR) | `sim/` |
| Presence | cho biết từng bay có xe hay không | chưa có | `sim/` |
| Evse | giám sát bộ sạc và phiên sạc | `evse/` | `sim/` |
| Perception | cấp khung ảnh và nội tham số camera cho module perception | `realsense/` (camera cổ tay) | `sim/` |

## Quy tắc chung

- Đại lượng vật lý theo đơn vị SI: m, rad, s, N, N·m, V, A, °C (REQ-HAL-009); toạ độ ảnh tính bằng pixel.
- Khung toạ độ ([ADR 0012](../decisions/0012-multi-arm-support.md)): `base` là gốc của model tay máy, trùng khung base mà controller UR dùng khi báo tư thế; `tool0` là mặt bích; TCP tính từ `tool0` theo hồ sơ tool; khung thế giới của trạm là gốc tay máy cộng vị trí ray (REQ-ARM-003, REQ-ARM-018). Không dùng `base_link`.
- Dấu thời gian của số đo theo đồng hồ monotonic của host (REQ-HAL-009, REQ-HAL-027).
- Không có số đo là `null`, khác với 0 hay `false`; adapter rỗng, tức adapter của port chưa nối thiết bị, trả `null` ở mọi kênh đọc và từ chối kèm mã mọi lệnh ra (REQ-HAL-004).
- Mỗi port phát health qua telemetry: đã nối hay chưa, tuổi dữ liệu (ms), lỗi đang chốt kèm mã, đầu ra đã bật hay chưa, trạng thái watchdog, đang dừng hay không, sai lệch bám, cùng trường riêng của adapter (REQ-HAL-005).
- Adapter của mỗi port được chọn tường minh trong cấu hình; giá trị không biết thì `core` không khởi động (`port.adapter_unknown`), và thiết bị mất kết nối không bao giờ được thay bằng adapter mô phỏng hay bản sao số (REQ-HAL-001, REQ-HAL-002, REQ-HAL-003, REQ-GW-021).
- Không port nào xoá chốt dừng khẩn cấp, ghi cấu hình an toàn của tay máy UR, nới giới hạn an toàn hay điều khiển STO của ray; phần mềm chỉ đọc trạng thái của các chức năng an toàn, và lệnh dừng qua port là dừng vận hành, không phải dừng khẩn cấp (REQ-HAL-007, REQ-HAL-021, [ADR 0005](../decisions/0005-safety-allocation.md)).

## Hành vi khi lỗi

Quy tắc chung của [ADR 0004](../decisions/0004-motion-on-controller.md) và ADR 0005: dữ liệu cũ, mất kết nối hoặc adapter lỗi thì phần mềm dừng và vào `SAFE_HOLD`; mất thiết bị không bao giờ tự chuyển sang mô phỏng. Requirement cụ thể hoá quy tắc này theo port:

| Port | Điều kiện | Phản ứng |
| --- | --- | --- |
| ArmPort, Rail, Io, Force | số liệu cũ hơn ngưỡng tuổi (mặc định 0,15 s), mất kết nối hoặc adapter báo lỗi | yêu cầu dừng mọi cơ cấu chấp hành, FSM vào `SAFE_HOLD` với mã của nguồn: `fsm.safe_hold.arm_data`, `fsm.safe_hold.rail_data`, `fsm.safe_hold.io_data`, `fsm.safe_hold.force_data`; port báo nguyên nhân bằng `port.stale_data`, `port.disconnected` hay `port.adapter_fault` (REQ-MOT-024, REQ-HAL-002) |
| Perception | khung mới nhất của camera cổ tay cũ hơn ngưỡng tuổi khung (mặc định 150 ms) hoặc camera mất kết nối | camera cổ tay bị coi là mất, mức giám sát `STOP` và hệ đóng băng; trong pha tay dấn vào xe, FSM còn vào `SAFE_STOP` (`fsm.safe_stop.watchdog`) và tự về pha trước khi mức giám sát trở lại `OK` liên tục 0,5 s (REQ-MIS-050, REQ-MIS-051, REQ-MIS-073, REQ-MIS-074) |
| Evse, Presence | mất số liệu | kênh trả `null`; guard đọc `null` như điều kiện chưa đạt, Presence dùng hiện diện khai thủ công (REQ-MIS-044, REQ-HAL-035); requirement chưa đặt `SAFE_HOLD` cho hai port này |

## ArmPort

Giao chuyển động của tay máy cho controller dưới dạng segment và đọc trạng thái đo của tay máy. Mỗi segment là trọn một đoạn chuyển động để controller tự chạy trong vòng điều khiển 500 Hz của nó; host không gửi điểm đặt theo từng chu kỳ và không chạy vòng servo hay vòng lực (ADR 0004, REQ-MOT-001). Mỗi lúc chỉ một ArmPort hoạt động (REQ-HAL-009).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| segment moveJ (`JointSegment`) | đích khớp (rad); vận tốc (rad/s) và gia tốc (rad/s²) của khớp dẫn; mọi khớp cùng bắt đầu và cùng tới đích | REQ-HAL-009 |
| segment moveL | đích TCP trong khung `base`, vị trí (m) và hướng (rad); vận tốc (m/s) và gia tốc (m/s²) của tool | REQ-HAL-009 |
| segment force mode | đẩy dọc trục cổng sạc tới lực đặt (N), nhường theo lực ở các trục còn lại; dùng cho cắm (lực chạm đáy mặc định 35 N) và spiral search (mặc định bán kính tăng 1,6 mm mỗi rad, tốc độ góc 3,0 rad/s, bán kính tối đa 12 mm); khung tác vụ khai trong khung `base` | REQ-HAL-009, REQ-MOT-007, REQ-MOT-008 |
| dừng | dừng segment đang chạy bằng lệnh dừng có giảm tốc của controller và giữ tư thế đo được; yêu cầu dừng từ lệnh Dừng còn dừng chương trình trên controller và dừng ray | REQ-HAL-021 |
| hệ số tốc độ | trong [0; 1], áp cả lên segment đang chạy; 0 dừng chuyển động | REQ-HAL-014, REQ-MOT-016 |
| bật, tắt đầu ra chuyển động | tắt sau mỗi lần nối adapter thật và mỗi lần khởi động lại; bật và tắt là thao tác liên quan an toàn; khoá chọn chế độ ở thủ công thì lệnh bật bị từ chối (`port.output.key_manual`) | REQ-HAL-022, REQ-HAL-023 |
| gỡ chốt lỗi (`rearm_motion_port`) | kiểm lại controller sẵn sàng trước khi gỡ; chưa sẵn sàng thì `port.rearm_refused` | REQ-HAL-020, REQ-MOT-026 |
| đặt và đọc lại hồ sơ tool | offset TCP so với `tool0` (m, rad), khối lượng (kg), trọng tâm (m) | REQ-HAL-025, REQ-ARM-005 |
| đọc thông số hiệu chuẩn động học | qua primary interface của controller ở cổng 30011, cổng chỉ gửi trạng thái; ghi checksum của bộ thông số | REQ-HAL-025, REQ-ARM-016 |

| Trạng thái đo | Đơn vị và khung | Requirement |
| --- | --- | --- |
| góc khớp, vận tốc khớp | rad, rad/s | REQ-HAL-009 |
| tư thế TCP do controller báo | khung `base`; vị trí (m), hướng (rad) | REQ-HAL-009, REQ-HAL-025 |
| dấu thời gian | đồng hồ monotonic | REQ-HAL-009 |
| kết nối, chế độ robot, trạng thái an toàn, trạng thái chương trình, segment đang chạy | — | REQ-HAL-005, REQ-HAL-009 |
| sai lệch bám giữa vị trí kỳ vọng và vị trí đo | rad ở từng khớp; báo lệch khi vượt mặc định 0,15 rad | REQ-HAL-012 |
| cờ đường lệnh phần cứng sẵn sàng | đúng khi đã nối, đầu ra đã bật và không có lỗi đang chốt; luôn sai với adapter mô phỏng | REQ-HAL-024 |

Khi lỗi:

- Lệnh sai số khớp (`port.dimension_mismatch`), có giá trị không hữu hạn (`port.non_finite`), có loại segment không biết (`port.segment_unknown`) hay hệ số tốc độ ngoài [0; 1] (`port.speed_out_of_range`) bị từ chối trước khi tới adapter; lệnh hợp lệ chỉ tới adapter sau bộ kiểm segment (REQ-HAL-010, REQ-HAL-014, REQ-MOT-014).
- Khi segment đang chạy mà vòng giám sát không gửi lệnh hay nhịp sống quá mặc định 0,5 s, port yêu cầu controller dừng segment và báo `port.host_timeout`; phép kiểm này phục vụ vận hành, không phải chức năng an toàn (REQ-HAL-011).
- Gói trạng thái có góc khớp không hữu hạn hay vượt 2π + 0,1 rad bị bỏ và tính là lỗi kết nối (REQ-HAL-019).
- Controller từ chối lệnh, hoặc gửi lệnh thất bại 3 lần liên tiếp, thì port ngừng gửi và chốt lỗi (`port.command_refused`, `port.send_failed`); tay máy lệch khỏi segment quá dung sai thì chốt `port.tracking_error` và mức giám sát giữ `STOP`; chỉ `rearm_motion_port` gỡ được chốt (REQ-HAL-018, REQ-HAL-020, REQ-MOT-026).
- Sau mỗi lần dừng, tư thế đo được thành mốc của lệnh kế tiếp (REQ-HAL-013).

Adapter:

- `ur_rtde/`: giao tiếp với controller UR chỉ qua thư viện [ur_rtde](https://gitlab.com/sdurobotics/ur_rtde), không có mã tự viết cho giao thức RTDE; segment chạy bằng moveJ, moveL và force mode của controller, với tham số theo [`rtde_control_interface.h`](https://gitlab.com/sdurobotics/ur_rtde/-/blob/master/include/ur_rtde/rtde_control_interface.h) của ur_rtde (khung tác vụ của force mode tính theo khung base); thanh ghi input của RTDE chỉ dùng dải 24–47; lệnh giám sát qua Dashboard Server ở cổng 29999; khi nối, adapter phải đọc được trạng thái trong 3 s với `robot_mode` là RUNNING, `safety_status` là NORMAL hoặc REDUCED và `runtime_state` là PLAYING, theo [hướng dẫn RTDE của UR](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-guide.html) (REQ-HAL-015, REQ-HAL-016, REQ-HAL-017).
- `sim/`: chạy cùng các lệnh segment theo thời gian với vận tốc và gia tốc của segment, chạy force mode theo mô hình cơ cấu cắm, và tính sai lệch bám như adapter thật (REQ-SIM-001, REQ-HAL-012).
- Tay máy của hãng khác UR cần adapter ArmPort riêng và kiểm chứng hệ an toàn của hãng đó (ADR 0004, REQ-ARM-009).

## Rail

Ra lệnh cho drive của ray và đọc vị trí ray. Drive tự chạy vòng vị trí và tự hãm khi tới đích; `core` gửi đích cùng giới hạn rồi giám sát (ADR 0004, REQ-MOT-019). Ray chỉ chạy khi tay máy ở tư thế cất (REQ-MOT-004). STO của ray nối cứng, không đi qua phần mềm (REQ-HAL-029).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| nối, đóng | — | REQ-HAL-028 |
| đi tới vị trí | vị trí dọc trục ray (m) trong biên hành trình; vận tốc (m/s) và gia tốc (m/s²) không quá trần của hình học trạm, mặc định 0,45 m/s và 0,9 m/s² | REQ-HAL-028, REQ-MOT-019 |
| dừng | — | REQ-HAL-028 |
| hệ số tốc độ | trong [0; 1], áp cả lên chuyển động đang chạy | REQ-HAL-014 |
| đọc vị trí đo | m dọc trục ray; gốc tay máy trong khung thế giới tính từ vị trí này | REQ-HAL-028, REQ-ARM-018 |
| cờ nhận lệnh được, health | trạng thái drive nằm trong trường riêng của adapter | REQ-HAL-005, REQ-HAL-028 |
| sai lệch bám | m; báo lệch khi vượt mặc định 0,10 m | REQ-HAL-012 |

Khi lỗi: đọc lỗi hay dữ liệu cũ thì port báo lỗi và yêu cầu dừng, FSM vào `SAFE_HOLD` với `fsm.safe_hold.rail_data` (REQ-HAL-029, REQ-MOT-024). Trạm không có ray dùng đế cố định: vị trí đế lấy từ hình học trạm, lệnh đi tới vị trí khác bị từ chối với `port.rail.fixed_base`, và port báo không có ray (REQ-HAL-030).

Adapter: `modbus/` nói Modbus TCP ([Modbus Organization](https://www.modbus.org/specs.php)) với drive và đọc vị trí ít nhất 20 lần mỗi giây (REQ-HAL-029); adapter qua OPC UA, EtherCAT CiA402 và I/O số của UR là đề xuất (REQ-HAL-040). `sim/` chạy ray tới đích với tốc độ tối đa của ray nhân hệ số tốc độ, đích chỉ đến từ lệnh qua port (REQ-SIM-003, REQ-SIM-013).

## Io

Đọc tín hiệu rời rạc của trạm cho guard của FSM, ghi đèn tháp và chốt khoá đầu sạc (REQ-HAL-031).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| đọc tín hiệu | bảy tín hiệu đúng, sai hoặc `null`: `connector_locked`, `lid_open`, `dc_contactor_closed`, `door_interlock_ok`, `estop_hardware`, `safety_relay_ok`, `auto_mode_key` | REQ-HAL-031 |
| ghi đèn tháp | xanh, vàng, đỏ hoặc tắt; trả thành công hay từ chối kèm mã | REQ-HAL-031, REQ-MIS-076 |
| ghi chốt khoá đầu sạc | đóng hoặc mở; trả thành công hay từ chối kèm mã | REQ-HAL-031, REQ-MIS-075 |
| health | số kênh đang có số đo | REQ-HAL-031 |

`estop_hardware` chỉ được đọc: chốt dừng khẩn cấp chỉ xoá được bằng nút reset vật lý, và trạng thái nút không đọc được thì tính là đang ấn (REQ-MIS-067, REQ-HAL-007).

Khi lỗi: số liệu cũ, mất kết nối hay adapter lỗi thì FSM vào `SAFE_HOLD` với `fsm.safe_hold.io_data` (REQ-MOT-024). Adapter rỗng trả `null` ở mọi kênh và từ chối lệnh ghi với `io.no_port.light`, `io.no_port.lock` (REQ-HAL-004). Đổi giao thức lúc chạy (`set_io_port`) đặt lại ý định đã gửi cho chốt khoá và đèn tháp để gửi lại qua port mới (REQ-HAL-033).

Adapter: giao thức của adapter I/O số chọn theo kiểm kê phần cứng trong Modbus TCP (`modbus/`), I/O số của UR và OPC UA (REQ-HAL-032); danh mục giao thức ghi giao thức nào đã có adapter, chọn giao thức không có trong danh mục trả `port.protocol_unknown`, chọn giao thức chưa có adapter trả `port.no_module` (REQ-HAL-008). `sim/` báo `connector_locked` theo chốt mô phỏng, `dc_contactor_closed` khi dòng trên 1 A, `lid_open` theo nắp cổng của xe mô phỏng, và cho test đặt `estop_hardware`, `door_interlock_ok`, `safety_relay_ok`, `auto_mode_key` qua giao diện của SIM (REQ-SIM-014).

## Force

Cấp lực và mô-men tiếp xúc cho guard khi cắm và rút, cho force mode và cho phép kiểm mô-men của bộ kiểm segment (REQ-HAL-027, REQ-MIS-039, REQ-MIS-046, REQ-MOT-021).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| đọc lực và mô-men | fx, fy, fz (N); tx, ty, tz (N·m); cờ số đo của cảm biến hay số mô phỏng; dấu thời gian monotonic; `null` khi không có cảm biến | REQ-HAL-027 |
| đưa về 0 | trả thành công, hoặc từ chối với `port.force.zero_refused` | REQ-HAL-027 |
| health | — | REQ-HAL-027 |

Khi lỗi: số liệu cũ hay mất kết nối thì FSM vào `SAFE_HOLD` với `fsm.safe_hold.force_data` (REQ-MOT-024). Không có kênh lực thì đầu sạc không được coi là đã chạm đáy hay đã ra khỏi cổng, và force mode không đẩy (REQ-MIS-039, REQ-MIS-046, REQ-MOT-007).

Adapter: `ur_rtde/` đọc trường `actual_TCP_force` của RTDE; cảm biến lực tích hợp của UR là nguồn lực mặc định, lệnh đưa về 0 dùng lệnh của controller (REQ-HAL-026). Adapter cho cảm biến lực sáu trục gắn ngoài là đề xuất (REQ-HAL-042). `sim/` trả fz bằng lực dọc trục của thế giới mô phỏng, các thành phần khác bằng 0, kèm cờ số mô phỏng (REQ-SIM-012).

## Presence

Cho bộ điều phối và FSM biết từng bay có xe hay không (REQ-HAL-034).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| đọc hiện diện | cho từng bay: có xe, không có xe hoặc `null`; cờ số đo của cảm biến hay giá trị khai | REQ-HAL-034 |

Khi lỗi hoặc chưa có cảm biến: port trả `null`, và FSM cùng bộ điều phối dùng hiện diện khai thủ công của người vận hành; telemetry ghi rõ thông tin đến từ cảm biến hay từ khai (REQ-HAL-035).

Adapter: chưa có adapter thiết bị; adapter cho vòng cảm ứng, rèm quang và camera toàn cảnh là đề xuất (REQ-HAL-041), và danh mục giao thức theo REQ-HAL-008. `sim/` báo có xe theo bảng chiếm chỗ của SIM, khai là không phải số đo (REQ-SIM-015).

## Evse

Giám sát bộ sạc và phiên sạc giữa bộ sạc với xe, cho guard từ `S12_SEAT_VERIFY` tới `S17_UNLOCK_WAIT`. Port chỉ đọc: hệ thống không điều khiển CP hay PP, và cổng chính cho việc cấp điện là tín hiệu cho phép nối cứng giữa trạm và bộ sạc (REQ-HAL-036, REQ-HAL-037).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| đọc điện áp Control Pilot | V, quy ra trạng thái A (12 V), B (9 V), C (6 V), D (3 V), E (0 V) hoặc F (lỗi) theo [IEC 61851-1](https://webstore.iec.ch/en/publication/33644) | REQ-HAL-036 |
| đọc trạng thái phiên | bắt tay theo [ISO 15118-2](https://committee.iso.org/standard/55366.html) hoặc [ISO 15118-20](https://committee.iso.org/standard/77845.html) xong hay chưa; dòng sạc (A); điện áp bus DC (V); contactor đóng hay mở; SoC của xe (%); nhiệt độ chân sạc (°C) khi bộ sạc cung cấp | REQ-HAL-037 |

Mỗi giá trị bộ sạc không cung cấp là `null`.

Khi lỗi: thông tin không có thì guard đọc nó như điều kiện chưa đạt, ví dụ chưa có số đo dòng thì coi là còn dòng (REQ-MIS-044); trên máy thật không có phiên giả nào luôn báo thành công (REQ-HAL-037).

Adapter: `evse/` dùng [EVerest](https://github.com/EVerest/everest-core) làm kênh giám sát (REQ-HAL-037). `sim/` theo mô hình điện, bắt tay, SoC và nhiệt độ của SIM (REQ-SIM-008 tới REQ-SIM-011).

## Perception

Cấp khung ảnh và nội tham số của camera cho module perception, nơi duy nhất mở và đọc thiết bị camera; HMI, gateway, harvest và hiệu chuẩn chỉ nhận khung hay kết quả qua perception (REQ-PER-001).

| Thao tác | Tham số, đơn vị và khung | Requirement |
| --- | --- | --- |
| đọc khung màu mới nhất của một camera | độ phân giải và fps theo hồ sơ camera; dấu thời gian monotonic; không có khung khi camera ở nguồn `disabled` hay chưa có khung, không trả khung cũ hay khung trống | REQ-HAL-038, REQ-PER-012 |
| đọc nội tham số do thiết bị báo | fx, fy, cx, cy (px) và hệ số méo, dùng làm nội tham số danh nghĩa cho tới khi hiệu chuẩn | REQ-HAL-038, REQ-CAL-006 |
| đọc trạng thái nguồn | nguồn thực tế `device`, `synthetic`, `disabled`, `unavailable` hoặc `unknown`; tuổi khung (ms) | REQ-PER-003, REQ-PER-007 |

Tư thế của camera cổ tay trong khung thế giới bằng tư thế `tool0` tính từ góc khớp và vị trí ray đo được nhân với phép biến đổi tay-mắt; port không cấp tư thế thật của cổng sạc trong thế giới mô phỏng (REQ-PER-037).

Khi lỗi: camera nguồn `device` không mở hay không đọc được thì nguồn thực tế là `unavailable`, lý do được ghi vào lỗi thiết bị, và khung không bao giờ được thay bằng khung mô phỏng hay khung cũ (REQ-PER-004); mở lại sau 5 s, 15 s, 60 s rồi cứ 300 s một lần (REQ-PER-009). Mất camera cổ tay dẫn tới mức giám sát `STOP` như ở mục "Hành vi khi lỗi".

Adapter: `realsense/` cấp luồng màu và nội tham số của camera cổ tay bằng [librealsense](https://github.com/IntelRealSense/librealsense) (REQ-HAL-038). `sim/` dựng khung của camera cổ tay cỡ 320×180, góc mở 85°, một khung mỗi nhịp giám sát, và khung JPEG 640×360 của camera toàn cảnh (REQ-SIM-021, REQ-SIM-022).

## Chưa chốt

- Dạng dữ liệu của segment moveL và segment force mode, và dạng biểu diễn hướng trong tư thế Descartes của port; hướng dẫn RTDE của UR báo hướng TCP bằng vector quay (ADR 0004).
- Khung của phép đo ở port Force: hướng dẫn RTDE của UR mô tả `actual_TCP_force` là lực tổng quát tại TCP mà không nêu khung; kiểm với URSim hoặc controller thật trước khi viết adapter.
- Tiêu chí của bộ kiểm segment, ngưỡng của bộ giám sát tiến trình, cách controller dừng segment khi mất liên lạc với host (REQ-MOT-033, đề xuất), và dữ liệu nào đặt vào thanh ghi nào trong dải 24–47 (ADR 0004).
- Lệnh jog có deadman đi qua ArmPort ở dạng nào (ADR 0004, ADR 0006).
- Phản ứng khi port Evse hay Presence mất kết nối ngoài việc trả `null`: requirement chưa đặt `SAFE_HOLD` cho hai port này, trong khi quy tắc chung của ADR 0004 và ADR 0005 đòi dừng và vào `SAFE_HOLD`.
- Adapter cho camera toàn cảnh mở theo chỉ mục thiết bị, đường dẫn `/dev/` hay RTSP (REQ-PER-010, REQ-HAL-039), và chỗ đặt adapter rỗng cùng đế cố định của ray: ADR 0002 chưa có thư mục cho các phần này.
- Port Perception có mang cả kết quả của perception khi perception tách thành service hay không (ADR 0002).
- Model UR thật, drive của ray, loại camera và giao thức I/O: chốt bằng kiểm kê phần cứng trước khi viết adapter cho thiết bị thật (ADR 0004).
