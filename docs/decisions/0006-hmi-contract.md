# 0006. Hợp đồng giao tiếp HMI: REST, một kênh WSS, lỗi theo RFC 9457

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Giao diện vận hành (HMI) là component `operator-ui`, chạy trong trình duyệt. Service `hmi` dùng Caddy để lo TLS, phục vụ bản build của `operator-ui` và làm proxy tới service `core`, nơi chạy component `robot-core` (Python), có API viết bằng FastAPI. Qua HMI, người vận hành đăng nhập, theo dõi telemetry và sự kiện, gửi lệnh, đổi cấu hình, chạy tay (jog) và xem video từ camera.

Mạng của cell (khu vực làm việc của tay máy) tách riêng, chỉ host chạy core tới được. LAN của trạm chỉ thấy cổng HTTPS 443 của HMI, và không có cổng nào mở vào từ WAN ([IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033)). Vì vậy mọi trao đổi giữa trình duyệt và core đều đi qua cổng 443 này.

Phần mềm, kể cả HMI, và video không phải chức năng an toàn; chức năng an toàn nằm ở phần cứng (ADR 0005).

Cần quyết định: HMI và core trao đổi bằng giao thức nào, hợp đồng giữa hai bên mô tả bằng chuẩn nào và nằm ở đâu, lỗi báo ra sao, phiên đăng nhập giữ thế nào, và chạy tay cần ràng buộc gì.

## Yếu tố quyết định

- Dùng chuẩn của tổ chức tiêu chuẩn quốc tế, của chủ quản nền tảng hoặc đặc tả cộng đồng; chỗ chưa có chuẩn thì ghi rõ là lựa chọn của dự án.
- `robot-core` (Python) và `operator-ui` (TypeScript) dựa trên cùng một hợp đồng máy đọc được; hợp đồng lệch khỏi mã thì phải được phát hiện tự động.
- `contracts/` là hợp đồng công khai (CONTRIBUTING.md, mục "Thay đổi không tương thích"): thay đổi làm hỏng client hiện có phải được đánh dấu là không tương thích.
- Core đẩy telemetry, sự kiện và vòng đời lệnh tới HMI.
- Lỗi cần mã ổn định để HMI và bản dịch dùng chung.
- HMI là thứ duy nhất LAN của trạm thấy được, nên phiên đăng nhập và kênh đẩy phải theo hướng dẫn của OWASP ([WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html), [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)).
- Jog do người vận hành điều khiển trực tiếp từ HMI, nên không được chạy tiếp khi người đó đã buông tay.

## Các phương án đã xét

- REST cộng một kênh WSS: REST cho lệnh, truy vấn và cấu hình, mô tả bằng OpenAPI 3.1 sinh từ FastAPI; một kênh WSS cho telemetry, sự kiện và vòng đời lệnh, mô tả bằng AsyncAPI 3; lỗi theo RFC 9457; phiên bằng session cookie, không có token trên URL.
- OpenAPI 3.2.0 cho phần REST: như trên, nhưng mô tả phần REST bằng OpenAPI 3.2.0 thay cho 3.1.
- Token trên URL: như trên, nhưng xác thực bằng token đặt trên URL, chẳng hạn trong query string của URL kênh WSS, thay cho session cookie.

## Kết quả quyết định

Phương án được chọn: "REST cộng một kênh WSS", vì mọi phần có chuẩn đều dùng chuẩn mở, hợp đồng REST sinh từ chính mã nên CI phát hiện được lệch, và thông tin xác thực không nằm trên URL, đúng như OWASP khuyến nghị.

- REST cho lệnh, truy vấn và cấu hình. Hợp đồng REST là `contracts/openapi.json`, theo [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.1.html), sinh từ ứng dụng FastAPI (Pydantic v2) của `robot-core`; FastAPI sinh tài liệu OpenAPI 3.1.x ([FastAPI: First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)).
- Một kênh WSS duy nhất, tức WebSocket qua TLS theo [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455), mang telemetry, sự kiện và vòng đời lệnh: lệnh gửi qua REST, còn tiến trình của lệnh đi về trên kênh này. Kênh được mô tả bằng [AsyncAPI 3](https://www.asyncapi.com/docs/reference/specification/v3.0.0) trong `contracts/asyncapi.yaml`.
- Envelope của sự kiện dùng tên thuộc tính theo [CloudEvents](https://github.com/cloudevents/spec), cộng thuộc tính `sequence`. Đây là lựa chọn của dự án ở chỗ chưa có chuẩn.
- Lỗi theo [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (problem details, `application/problem+json`). Mỗi lỗi mang một mã ổn định, lấy từ danh mục mã lỗi và cảnh báo dùng chung cho phản hồi lỗi, cho bản dịch trong `locales/` (vi, en) và cho HMI.
- Phiên đăng nhập dùng session cookie có `Secure`, `HttpOnly` và `SameSite=Strict`. Không đặt token trên URL, kể cả URL của kênh WSS.
- Jog có deadman: jog chỉ chạy khi người vận hành đang giữ deadman; buông ra hoặc mất tín hiệu deadman thì jog dừng. Deadman này nằm trong phần mềm nên không phải chức năng an toàn.
- Video lên HMI dùng MJPEG ở bước đầu. Perception giữ toàn bộ camera, HMI chỉ xem, và video không bao giờ là tín hiệu an toàn. MJPEG là lựa chọn của dự án ở chỗ chưa có chuẩn.
- Hợp đồng nằm trong `contracts/`: `openapi.json`, `asyncapi.yaml`, và [JSON Schema](https://json-schema.org/specification) của payload trong `contracts/schemas/`. Client TypeScript của `operator-ui` sinh từ `contracts/` bằng [openapi-typescript](https://openapi-ts.dev/).

### Hệ quả

- Tốt, vì hợp đồng REST trong repo không thể lệch khỏi mã mà CI không biết.
- Tốt, vì HMI và bản dịch dựa vào mã lỗi ổn định, không dựa vào câu chữ của thông báo lỗi.
- Tốt, vì HMI chỉ mở và xác thực một kết nối WSS cho mọi dữ liệu đẩy, và `sequence` cho biết thứ tự của sự kiện.
- Xấu, vì chỉ phần REST có bước CI so hợp đồng với mã, nên `contracts/asyncapi.yaml` có thể lệch khỏi kênh WSS mà CI không thấy.

### Xác nhận

- CI sinh lại `contracts/openapi.json` từ `robot-core` và so diff với bản đã commit; có khác biệt thì CI không qua.
- Commit đụng `contracts/` hoặc route và WSS trong `robot-core/src/robot_core/gateway/` dùng scope `api`, phần session dùng scope `auth`. Thay đổi làm hỏng client hiện có của `contracts/` phải có cả `!` lẫn footer `BREAKING CHANGE:`, và commitlint chặn khi thiếu một trong hai (CONTRIBUTING.md).

## Ưu và nhược của từng phương án

### REST cộng một kênh WSS

- Tốt, vì FastAPI tự sinh tài liệu OpenAPI từ route và model Pydantic, phục vụ tại `/openapi.json`, nên không phải viết tay hợp đồng REST.
- Tốt, vì openapi-typescript sinh kiểu TypeScript từ OpenAPI 3.0 và 3.1, nên `operator-ui` và `robot-core` dùng chung một hợp đồng.
- Tốt, vì RFC 9457 cho lỗi một khuôn chung (`type`, `status`, `title`, `detail`, `instance`) và cho phép thêm member mở rộng; client phải bỏ qua member mở rộng mà nó không biết, nên thêm thông tin vào lỗi không làm hỏng client hiện có.
- Tốt, vì theo OWASP, `Secure` chỉ cho cookie đi qua kênh mã hoá, `HttpOnly` không cho script đọc cookie, `SameSite=Strict` không cho cookie đi kèm request từ site khác; không có token trên URL thì token không lọt vào log truy cập, lịch sử trình duyệt hay header `Referer`.
- Xấu, vì trình duyệt gửi cookie kèm bước bắt tay WebSocket, nên kênh WSS xác thực bằng cookie có nguy cơ bị chiếm từ site khác (Cross-Site WebSocket Hijacking); OWASP coi `SameSite` là lớp phòng thủ thêm và vẫn yêu cầu kiểm header `Origin` ở mỗi lần bắt tay.
- Xấu, vì phiên bản OpenAPI của hợp đồng phụ thuộc vào bản FastAPI sinh ra (3.1.x).

### OpenAPI 3.2.0 cho phần REST

- Tốt, vì [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) là bản đặc tả mới hơn 3.1.
- Xấu, vì FastAPI sinh OpenAPI 3.1.x, nên hợp đồng sinh từ mã không theo 3.2.0.

### Token trên URL

- Tốt, vì dễ làm: URL mang luôn thông tin xác thực, không cần cookie hay bước xác thực riêng sau khi bắt tay.
- Xấu, vì theo OWASP, token trên URL lọt vào log truy cập, lịch sử trình duyệt và header `Referer`.

## Thông tin thêm

- Quyết định này chưa chốt:
  - Envelope sự kiện: theo đủ đặc tả CloudEvents hay chỉ mượn tên thuộc tính; theo bản CloudEvents nào; thuộc tính nào bắt buộc; kiểu và phạm vi đánh số của `sequence` (CloudEvents có [extension `sequence`](https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/sequence.md) kiểu String, so theo thứ tự từ điển, nhưng chưa chốt có dùng extension này hay không); các trạng thái của vòng đời lệnh và cách gắn sự kiện với lệnh REST đã gửi. Các điểm này cần chốt khi viết `contracts/asyncapi.yaml`.
  - Mã lỗi: dạng mã; mã nằm ở member nào của problem details (RFC 9457 lấy URI ở `type` làm định danh chính của loại lỗi); danh mục đặt ở đâu; bên nào đổi mã thành thông báo vi, en.
  - Deadman của jog: tín hiệu đi trên REST hay WSS, chu kỳ gửi, và thời hạn chờ trước khi dừng.
  - Cách kiểm `contracts/asyncapi.yaml` khớp với kênh WSS trong mã.
  - Các biện pháp OWASP khác: kiểm header `Origin` theo allowlist ở mỗi lần bắt tay WSS; chống CSRF ngoài `SameSite=Strict`, vì OWASP coi SameSite là lớp phòng thủ thêm chứ không thay cho CSRF token; thời hạn của phiên.
  - Video: route phục vụ MJPEG, định dạng thay MJPEG về sau và điều kiện để đổi.
  - Tiền tố đường dẫn và cách đánh phiên bản của API.
- Không có phép so sánh nào giữa REST cộng WSS với các giao thức khác được ghi lại.
- `contracts/schemas/` còn chứa schema của cấu hình, release manifest và gói dữ liệu upload; các schema đó nằm ngoài quyết định này.
- Liên quan: ADR 0002 (bố cục repo, thuật ngữ component và service), ADR 0005 (phân bổ an toàn).
