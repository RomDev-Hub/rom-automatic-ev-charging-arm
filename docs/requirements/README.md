# Requirement

Thư mục này ghi requirement của hệ thống: điều hệ thống phải làm, mỗi điều một ID, viết sao cho kiểm chứng được và không ràng buộc cách hiện thực. Cách viết và các thuộc tính của requirement dựa theo [ISO/IEC/IEEE 29148:2018](https://standards.ieee.org/ieee/29148/6937/). Quyết định kiến trúc nằm ở [docs/decisions](../decisions/), tài liệu an toàn và hazard nằm ở [docs/safety](../safety/).

## ID

- ID có dạng `REQ-<AREA>-NNN`, ví dụ `REQ-MIS-001`. `<AREA>` là mã vùng ở bảng dưới; `NNN` gồm ba chữ số, đánh liên tiếp từ `001` trong mỗi vùng.
- ID đã cấp không đổi và không dùng lại.
- Sửa câu chữ mà không đổi ý thì giữ ID. Đổi ý thì bỏ requirement cũ và thêm requirement mới với ID mới.
- Requirement bị bỏ thì xoá khỏi bảng; lịch sử của nó nằm trong Git.

| Mã | Vùng | Phạm vi |
| --- | --- | --- |
| MIS | mission | máy trạng thái, guard, điều phối nhiều ô (`robot-core/src/robot_core/mission/`) |
| MOT | motion | director, segment, bộ kiểm segment, giám sát tiến trình, jog (`robot-core/src/robot_core/motion/`) |
| ARM | tay máy | model tay máy và tool, FK, Jacobian, IK, động lực học, tầm với (`robot-core/src/robot_core/arm/`, `defaults/arms/`, `defaults/tools/`) |
| PER | perception | nhận dạng, tư thế cổng sạc (`robot-core/src/robot_core/perception/`) |
| CAL | calibration | hiệu chuẩn (`robot-core/src/robot_core/calibration/`) |
| HAL | thiết bị | port và adapter của thiết bị thật (`robot-core/src/robot_core/ports/`, `adapters/` trừ `adapters/sim/`) |
| SIM | mô phỏng | adapter mô phỏng, lỗi giả lập (`robot-core/src/robot_core/adapters/sim/`) |
| GW | gateway | REST, WSS, telemetry, sự kiện (`robot-core/src/robot_core/gateway/`, `contracts/`) |
| AUTH | xác thực | đăng nhập, vai trò, xác thực lại, nhật ký kiểm toán |
| CFG | cấu hình | schema, áp dụng nguyên tử, chuyển đổi phiên bản, danh mục xe (`robot-core/src/robot_core/config/`, `defaults/vehicles/`) |
| REC | ghi dữ liệu | MCAP, journal mất điện (`robot-core/src/robot_core/recording/`) |
| HRV | harvest | đồng ý, làm mờ, chọn khung, gửi dữ liệu (`robot-core/src/robot_core/harvest/`) |
| OTA | cập nhật | điều kiện cập nhật, release manifest, dịch vụ cập nhật (`robot-core/src/robot_core/ota/`, `deploy/release/`, `deploy/host/updater/`, `deploy/os/`) |
| CLI | dòng lệnh | lệnh dòng lệnh (`robot-core/src/robot_core/cli/`) |
| TRN | training | huấn luyện, đánh giá, xuất model (`training/`) |
| HMI | giao diện vận hành | `operator-ui/` |
| I18N | ngôn ngữ | bản dịch, thuật ngữ (`robot-core/src/robot_core/locales/`, `docs/glossary.md`) |
| DEP | triển khai | image, Compose, cấu hình host và trạm (`deploy/`) |

## Trường

Mỗi requirement là một hàng của bảng, với các cột theo đúng thứ tự dưới đây, nên mỗi requirement nằm trên một dòng và tìm được bằng ID.

| Cột | Ghi gì |
| --- | --- |
| ID | `REQ-<AREA>-NNN` |
| Yêu cầu | một câu có chủ ngữ "hệ thống" và động từ "phải" hoặc "không được", có thể mở đầu bằng điều kiện ("Ở `<trạng thái>`, ...", "Khi ..., ..."); nêu một hành vi kiểm chứng được |
| Lý do | vì sao cần requirement này, ngắn |
| Kiểm chứng | một hoặc nhiều phương pháp ở mục "Kiểm chứng" |
| Trạng thái | `bắt buộc` hoặc `đề xuất` |
| Liên quan | ADR (`ADR NNNN`), hazard (`HZ-NN`) hoặc requirement khác; `—` khi không có |

- Tên trạng thái, mã, lệnh, đường dẫn và định danh giữ nguyên, đặt trong backtick.
- Số dùng dấu phẩy thập phân và đơn vị SI.
- Số có chữ "mặc định" đi kèm là giá trị cấu hình được; số khác là giá trị cố định. Cấu hình chỉ được thu hẹp giới hạn an toàn và giới hạn ứng dụng, không được nới (ADR 0005).

## Trạng thái

| Trạng thái | Nghĩa |
| --- | --- |
| `bắt buộc` | thuộc phạm vi sản phẩm: phải được hiện thực và qua mọi phương pháp kiểm chứng đã ghi |
| `đề xuất` | ứng viên, chưa thuộc phạm vi: chưa phải hiện thực; thành `bắt buộc` khi Mr.Ròm duyệt, bằng một commit đổi cột Trạng thái |

## Kiểm chứng

Mức chạy 1, 2, 3 theo mục "Ba mức chạy và kiểm" của [CONTRIBUTING.md](../../CONTRIBUTING.md). Requirement ghi nhiều phương pháp thì phải qua tất cả.

| Phương pháp | Cách kiểm | Ở đâu |
| --- | --- | --- |
| `unit` | unit test, không cần thiết bị hay dịch vụ ngoài; chạy ở mức 1 | `robot-core/tests/unit/`; test `*.test.tsx` của `operator-ui` |
| `integration` | test nối nhiều module, hoặc nối với thư viện và bộ mô phỏng ngoài như Pinocchio, URSim; chạy ở mức 1 hoặc 2 | `robot-core/tests/integration/` |
| `SIM` | chạy cả hệ với adapter mô phỏng và lỗi giả lập; khi có trace tham chiếu thì so chuỗi pha và mã lý do với trace đó | `robot-core/tests/sim/`; trace tham chiếu ở `robot-core/tests/sim/golden/` |
| `HIL` | test với tay máy, ray, camera hoặc bộ sạc thật; chạy tay trên runner tự host, ở mức 3 | `robot-core/tests/hil/`, marker `hil` |
| `inspection` | người review xem tài liệu, cấu hình, hợp đồng hoặc mã; không chạy gì | review của commit |

## File

| File | Vùng |
| --- | --- |
| [mission-motion-arm.md](mission-motion-arm.md) | MIS, MOT, ARM |
| [perception-calibration-hardware.md](perception-calibration-hardware.md) | PER, CAL, HAL, SIM |
| [gateway-config-data.md](gateway-config-data.md) | GW, AUTH, CFG, REC, HRV, OTA, CLI, TRN |
| [hmi-i18n-deploy.md](hmi-i18n-deploy.md) | HMI, I18N, DEP |
