# 0013. Cập nhật OTA cho container và hệ điều hành

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Thiết bị chạy các service `core`, `hmi`, `perception` bằng Docker trên Jetson hoặc PC Linux, lắp ở trạm sạc hoặc tại nhà. Mỗi bản phát hành gồm image của các service, model và có thể kèm thay đổi schema cấu hình; hệ điều hành của máy cũng phải được cập nhật.

Thiết bị nhận và áp dụng bản cập nhật container và hệ điều hành bằng cách nào để không bao giờ cập nhật khi máy đang làm việc, tự quay lại được khi bản mới lỗi, mà chủ thiết bị vẫn cài được bản do chính họ sửa?

## Yếu tố quyết định

- An toàn: không cập nhật khi tay máy đang chạy, đang sạc cho xe hay còn lệnh chờ. Cập nhật là thao tác liên quan an toàn, cần vai trò nâng quyền, xác thực lại và nhật ký kiểm toán.
- Mạng: không có cổng nào mở vào từ WAN ([IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033)).
- Toàn vẹn: thiết bị chỉ chạy bản phát hành có chữ ký; khoá ký riêng không bao giờ đi qua CI.
- Phục hồi: bản lỗi tự quay lại bản trước.
- Quyền tối thiểu: container không chạy `privileged`, rootfs chỉ đọc, `cap_drop: ALL`, user không phải root; core không có quyền điều khiển Docker.
- Bất biến: bản phát hành trỏ tới image theo digest chứ không theo tag, nên mỗi tham chiếu chỉ đúng một image.
- Giấy phép: thiết bị lắp ở nhà được coi là "User Product" theo mục 6 của [AGPL-3.0](https://opensource.org/license/agpl-v3). Khi thiết bị chỉ nhận bản có chữ ký, chủ thiết bị phải có cách cài bản đã sửa ([GPL FAQ](https://www.gnu.org/licenses/gpl-faq.html)).
- Phần cứng: cách cập nhật hệ điều hành phụ thuộc phần cứng đích; riêng Jetson phải chọn phương án A/B trước khi flash.
- Bảo trì: ưu tiên thành phần mã nguồn mở có người duy trì hơn code tự viết.

## Các phương án đã xét

Kênh đưa bản cập nhật tới thiết bị:

- A1. Thiết bị tự kéo qua HTTPS, xác thực bằng chứng chỉ thiết bị (mTLS).
- A2. Máy chủ đẩy bản cập nhật xuống thiết bị qua một cổng mở vào.

Thành phần thực hiện cập nhật container:

- B1. Dịch vụ cập nhật chạy trên host (updater); core chỉ trả lời có cho cập nhật hay không.
- B2. Core tự cập nhật qua Docker socket.
- B3. Công cụ tự cập nhật container có sẵn: [Watchtower](https://github.com/containrrr/watchtower).

Khung OTA cho hệ điều hành A/B:

- C1. Cơ chế OTA image-based của NVIDIA cho Jetson.
- C2. RAUC cộng hawkBit.
- C3. Mender.

## Kết quả quyết định

Chọn A1 và B1. A1 là phương án duy nhất không cần cổng mở vào thiết bị. B1 giữ core ngoài Docker socket mà core vẫn quyết định lúc nào được cập nhật; B2 buộc core truy cập Docker socket, còn B3 đã archive. Khung OTA cho hệ điều hành (nhóm C) chưa chọn, xem phần Khung OTA hệ điều hành bên dưới.

OTA thuộc phạm vi sản phẩm ngay từ bây giờ, không hoãn: cập nhật container được hiện thực cùng đợt hoàn thiện chức năng; OTA hệ điều hành được hiện thực ở đợt làm với phần cứng, sau spike chọn khung.

**Kênh cập nhật.** Thiết bị chủ động kéo bản cập nhật từ máy chủ cập nhật của dự án qua HTTPS (TLS 1.3, [RFC 9846](https://www.rfc-editor.org/info/rfc9846)), xác thực bằng chứng chỉ thiết bị (mTLS). Thiết bị không mở cổng vào nào.

**Release manifest** viết theo [JSON Schema](https://json-schema.org/specification), schema đặt trong `contracts/schemas/`. Manifest ghi:

- phiên bản của bản phát hành;
- digest của image `core`, `hmi`, `perception`;
- phiên bản và checksum của model;
- phiên bản schema cấu hình;
- phiên bản hệ điều hành tối thiểu.

Manifest ký bằng khoá riêng của Mr.Ròm, dùng [cosign](https://github.com/sigstore/cosign). Khoá riêng giữ offline, không bao giờ để trong CI. Thiết bị giữ khoá công khai; khoá công khai để kiểm chữ ký nằm ở `deploy/release/`.

**Cập nhật container** đi qua năm bước:

1. Dịch vụ cập nhật trên host (`deploy/host/updater/`) tải manifest, kiểm chữ ký và kéo trước các image.
2. Updater hỏi core qua socket nội bộ. Core (`robot-core/src/robot_core/ota/`) chỉ cho phép khi đủ cả bốn điều kiện:
   - tay máy đã về vị trí an toàn;
   - core đang ở SAFE_HOLD;
   - không có phiên sạc và đầu sạc không cắm vào xe;
   - không còn lệnh chờ.
3. Core chuyển sang trạng thái cập nhật và chặn mọi lệnh.
4. Updater sao lưu cấu hình, rồi chạy `docker compose up -d` với image theo digest mới ([Compose `image`](https://docs.docker.com/reference/compose-file/services/#image)).
5. Kiểm sức khoẻ: mọi service healthy và self-test qua trong thời hạn quy định. Không đạt thì updater tự quay lại manifest và cấu hình trước.

Core không được truy cập Docker socket. Bản sao lưu cấu hình (mỗi bản một thư mục đặt tên theo thời điểm UTC, ví dụ `20261111T084000Z/`) và release manifest trước, dùng để quay lại, nằm trong volume `ev-arm-state` (`/var/lib/ev-arm/state`). Thiết bị kiểm checksum và chữ ký của model trước khi nạp và giữ model trước để quay lại; chi tiết ở ADR 0015.

**Hệ điều hành A/B.** Hệ điều hành cập nhật theo hai phân vùng A/B, image có chữ ký, tự quay lại bản cũ khi khởi động lỗi, thiết bị chủ động kéo. Cấu hình OTA hệ điều hành đặt ở `deploy/os/`.

**Khung OTA hệ điều hành.** Status: proposed.

- Tiêu chí bắt buộc: image có chữ ký, hai phân vùng A/B, tự quay lại bản cũ khi khởi động lỗi, thiết bị chủ động kéo, mã nguồn mở.
- Ứng viên: C1, C2, C3.
- Đóng khi spike trên phần cứng thật chọn được một khung đạt đủ năm tiêu chí bắt buộc và kết quả được ghi thành quyết định chấp nhận. Spike cần kiểm kê phần cứng trước: Jetson nào, JetPack bản mấy, có PC x86 hay không. Trên Jetson, việc chọn phải xong trước khi flash.

**Sau cập nhật.** Nếu bản cập nhật động tới phần mềm hay cấu hình liên quan an toàn, thiết bị ở lại SAFE_HOLD; kỹ sư tại chỗ chạy checklist kiểm tra rút gọn rồi mới cho chạy tự động.

**Triển khai từng bước.** Mỗi bản phát hành chạy trên một thiết bị trước, rồi mới tới các thiết bị khác.

**Chuyển đổi cấu hình.** Schema cấu hình chỉ chuyển đổi theo chiều tiến, có sao lưu (`robot-core/src/robot_core/config/`). Hạ phiên bản thì khôi phục bản sao lưu.

**Chế độ developer.** Chủ thiết bị đăng ký khoá ký của riêng họ; khi chế độ này bật, thiết bị nhận manifest ký bằng khoá đó. Chế độ có nhật ký kiểm toán, và cách dùng được ghi trong hướng dẫn sử dụng (`docs/manual/`).

### Hệ quả

- Tốt, vì không có cổng nào mở vào thiết bị; kết nối cập nhật luôn do thiết bị mở, và hai phía xác thực lẫn nhau.
- Tốt, vì thiết bị chỉ cài bản có chữ ký hợp lệ, và manifest chỉ đúng image, model, schema cấu hình và hệ điều hành tối thiểu của từng bản phát hành.
- Tốt, vì cập nhật không bắt đầu khi tay máy đang chạy, đang sạc hay còn lệnh chờ.
- Tốt, vì bản container lỗi tự quay lại manifest và cấu hình trước, còn hệ điều hành mới khởi động lỗi thì tự quay lại bản cũ.
- Tốt, vì chỉ dịch vụ trên host làm việc với Docker; core không có quyền đó.
- Tốt, vì chủ thiết bị vẫn cài được bản do họ sửa, qua chế độ developer.
- Xấu, vì phải viết, kiểm và bảo trì thêm một dịch vụ chạy trên host.
- Xấu, vì mỗi bản phát hành phải được ký ngoài CI, bởi người giữ khoá offline.
- Xấu, vì sau bản cập nhật động tới phần liên quan an toàn, thiết bị phải chờ kỹ sư tại chỗ mới chạy tự động lại được.
- Xấu, vì hạ phiên bản khôi phục cấu hình từ bản sao lưu, nên thay đổi cấu hình làm sau bản sao lưu đó phải làm lại.
- Xấu, vì Jetson phải chờ chọn xong phương án A/B rồi mới flash được.
- Trung tính, vì khi bật chế độ developer, thiết bị nhận cả manifest không do Mr.Ròm ký; việc này có nhật ký kiểm toán.

### Xác nhận

- Commit type đổi hành vi ở scope `ota` phải có label Why, How, Test, Impact ([CONTRIBUTING.md](../../CONTRIBUTING.md), mục "Body"), nên mỗi thay đổi ghi lại cách đã kiểm.
- Test của luồng cập nhật container cho thấy:
  - manifest sai chữ ký hoặc không đúng schema bị từ chối;
  - thiếu một trong bốn điều kiện thì core từ chối cập nhật;
  - trong lúc cập nhật, core chặn mọi lệnh;
  - service không healthy hoặc self-test không qua trong thời hạn thì thiết bị quay lại manifest và cấu hình trước;
  - bản cập nhật động tới phần liên quan an toàn để thiết bị ở lại SAFE_HOLD;
  - manifest ký bằng khoá do chủ thiết bị đăng ký chỉ được nhận khi chế độ developer bật.
- Review file Compose chạy trên thiết bị: service `core` không gắn Docker socket, image tham chiếu theo digest.
- Khoá ký riêng không nằm trong repo và không có trong secret của CI.
- A/B hệ điều hành và việc tự quay lại khi khởi động lỗi chỉ kiểm được trên phần cứng thật: trong spike, rồi trên khung đã chọn.

## Ưu và nhược của từng phương án

- A1. Thiết bị tự kéo qua HTTPS, mTLS.
  - Tốt, vì không cần cổng mở vào thiết bị.
  - Tốt, vì thiết bị và máy chủ xác thực lẫn nhau bằng chứng chỉ.
  - Trung tính, vì lúc áp dụng bản mới do thiết bị quyết theo điều kiện của core, không do máy chủ.
- A2. Máy chủ đẩy qua cổng mở vào.
  - Tốt, vì máy chủ chủ động được lúc gửi bản cập nhật.
  - Xấu, vì phải mở cổng vào thiết bị, trái quy tắc không có cổng nào mở vào từ WAN.
- B1. Dịch vụ cập nhật trên host.
  - Tốt, vì core không cần quyền vào Docker socket.
  - Tốt, vì core vẫn quyết định có cho cập nhật hay không theo trạng thái của máy.
  - Xấu, vì là code tự viết chạy trên host, phải tự kiểm và bảo trì.
- B2. Core tự cập nhật qua Docker socket.
  - Tốt, vì không cần dịch vụ riêng trên host.
  - Xấu, vì core phải điều khiển được Docker daemon; daemon chạy bằng quyền root (trừ chế độ rootless) và chỉ người dùng tin cậy mới nên điều khiển nó ([Docker Engine security](https://docs.docker.com/engine/security/), mục "Docker daemon attack surface"). Core khi đó không còn chạy với quyền tối thiểu.
- B3. Watchtower.
  - Tốt, vì có sẵn, không phải tự viết.
  - Xấu, vì kho mã đã archive, không còn được duy trì.
- C1, C2, C3. Ưu nhược của ba ứng viên chưa được đánh giá; spike trên phần cứng thật sẽ đánh giá chúng theo năm tiêu chí bắt buộc. Tài liệu chính thức:
  - C1: [Jetson Linux Developer Guide, mục Image-Based Over-the-Air Update](https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html), chỉ dành cho Jetson;
  - C2: [RAUC](https://rauc.io/), phần cập nhật chạy trên thiết bị, cùng [hawkBit](https://github.com/eclipse-hawkbit/hawkbit), phía máy chủ quản lý việc triển khai bản cập nhật;
  - C3: [Mender](https://github.com/mendersoftware/mender).

## Thông tin thêm

- ADR liên quan: 0005 (phân bổ an toàn), 0007 (dữ liệu runtime nằm trong volume), 0011 (giấy phép, thoả thuận đóng góp, tài sản NC), 0015 (vòng đời model), 0016 (danh tính thiết bị, khoá ký, hỗ trợ từ xa).
- Cách đọc giấy phép làm cơ sở cho chế độ developer cần kiểm pháp lý trước khi giao thiết bị.
- Cách thiết bị kéo image chưa chốt và phải chốt trước khi hiện thực cập nhật container. Nếu image nằm private trên GHCR thì mỗi thiết bị phải giữ token GitHub, nên cần kiểm loại token và phạm vi quyền. Hướng khớp với kênh cập nhật ở trên: CI đẩy image lên GHCR, thiết bị kéo từ máy chủ cập nhật của dự án bằng mTLS.
- ADR này chưa định:
  - thời hạn kiểm sức khoẻ và nội dung self-test;
  - cách thiết bị biết một bản cập nhật có động tới phần mềm hay cấu hình liên quan an toàn hay không; manifest chưa có trường cho việc này;
  - nội dung checklist kiểm tra rút gọn sau cập nhật;
  - thiết bị làm gì khi hệ điều hành đang chạy cũ hơn phiên bản tối thiểu trong manifest;
  - bước nào trong luồng cập nhật cần người có vai trò nâng quyền xác nhận và xác thực lại;
  - điều kiện để bản phát hành đi tiếp từ thiết bị đầu tiên tới các thiết bị khác;
  - ai được bật chế độ developer và đăng ký khoá, sự kiện nào vào nhật ký kiểm toán, và chế độ này có áp dụng cho image hệ điều hành không;
  - PC x86 dùng khung nào nếu spike chọn C1, vốn chỉ dành cho Jetson;
  - máy chủ cập nhật nằm trong hay ngoài phạm vi repo.
