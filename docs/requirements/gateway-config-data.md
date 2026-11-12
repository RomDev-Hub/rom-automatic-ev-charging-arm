# Requirement: gateway, xác thực, cấu hình, dữ liệu, cập nhật và dòng lệnh

Requirement của bảy vùng: GW (gateway), AUTH (xác thực), CFG (cấu hình), REC (ghi dữ liệu), HRV (harvest), OTA (cập nhật) và CLI (dòng lệnh). ID, các cột, trạng thái và phương pháp kiểm chứng theo [README](README.md).

- Mã kết quả và mã lỗi (`cmd.*`, `err.*`, `gate.*`, `safehold.*`) là định danh dùng chung cho mã nguồn, hợp đồng trong `contracts/`, bản ghi và bản dịch trong `locales/`. Requirement ghi "mã riêng" khi cần một mã chưa có tên; tên đặt trong danh mục mã lỗi và cảnh báo (ADR 0006).
- Đường dẫn dữ liệu trên thiết bị là đường dẫn trong container (ADR 0007).
- Chuẩn được dẫn chiếu có địa chỉ ở mục "Chuẩn dẫn chiếu" cuối file.
- ADR liên quan: [0005](../decisions/0005-safety-allocation.md) (phân bổ an toàn), [0006](../decisions/0006-hmi-contract.md) (hợp đồng HMI), [0007](../decisions/0007-runtime-data-in-volumes.md) (dữ liệu runtime), [0013](../decisions/0013-ota-updates.md) (cập nhật OTA), [0014](../decisions/0014-data-upload-and-privacy.md) (dữ liệu gửi về máy chủ), [0015](../decisions/0015-model-lifecycle.md) (vòng đời model), [0016](../decisions/0016-device-identity-and-keys.md) (danh tính thiết bị, khoá ký, hỗ trợ từ xa).

## Định nghĩa dùng chung

### Vai trò

Mỗi tài khoản có một hoặc nhiều vai trò. Vai trò bảo trì là vai trò nâng quyền mà ADR 0005 đòi cho thao tác liên quan an toàn.

| Vai trò | Được làm |
| --- | --- |
| vận hành | xem telemetry, sự kiện, video và tình trạng của máy; gửi các lệnh vận hành mà requirement của vùng MIS và MOT giao cho người vận hành: bắt đầu và huỷ phiên sạc, Dừng, tạm giữ, chạy lại, các lệnh xác nhận, gỡ chốt |
| bảo trì | mọi việc của vai trò vận hành; lệnh cấu hình, nhập và khôi phục cấu hình; chế độ bảo trì và chạy tay; thao tác liên quan an toàn; bật và thu hồi đồng ý thu dữ liệu; bật đường hầm hỗ trợ từ xa và việc gửi tình trạng thiết bị; xác nhận checklist kiểm tra rút gọn sau cập nhật; đọc nhật ký kiểm toán |
| quản trị | tạo tài khoản, đổi vai trò và khoá tài khoản; đọc nhật ký kiểm toán |

### Từ dùng chung

- Phiên đăng nhập: phiên của một tài khoản sau khi đăng nhập, giữ phía máy chủ và gắn với trình duyệt bằng session cookie; khác với phiên sạc của một xe.
- Phiên chạy: một lần chạy của `robot-core`, từ lúc khởi động tới lúc tắt; mỗi phiên chạy có một ID (REQ-REC-013).
- Thao tác liên quan an toàn: đổi nhóm ngưỡng an toàn và giới hạn của ứng dụng, đổi model tay máy hoặc hồ sơ tool, bật đầu ra chuyển động, và cập nhật (xác nhận áp bản cập nhật, bật hoặc tắt chế độ developer, đăng ký khoá ký), kể cả khi thay đổi đi qua lệnh nhập hay khôi phục cấu hình (ADR 0005).
- Xác thực lại: người dùng nhập lại mật khẩu của chính mình ngay trước thao tác (REQ-AUTH-012).
- Nhật ký kiểm toán: bản ghi bền, chỉ thêm, cho biết ai đã làm thao tác nào, lúc nào, với phạm vi nào và kết quả ra sao (REQ-AUTH-013).
- Problem details: phản hồi lỗi theo RFC 9457, kiểu nội dung `application/problem+json`.
- Giá trị mặc định: giá trị đi kèm phần mềm trong `robot-core/src/robot_core/defaults/`, dùng khi cấu hình trạm không khai giá trị khác.
- Bundle cấu hình: file xuất từ cấu hình trạm, gồm các nhóm cấu hình đã chọn kèm checksum, dùng để nhập lại vào cùng trạm hay trạm khác (REQ-CFG-013).
- Journal mất điện: file ghi trạng thái vận hành tối thiểu để lần khởi động sau biết tay máy ở đâu và đầu sạc có thể còn trong cổng hay không; requirement của vùng MIS gọi nó là dấu vết vận hành.
- Dịch vụ cập nhật: dịch vụ chạy trên host, ngoài Docker Compose, mã ở `deploy/host/updater/` (ADR 0013).

## GW: gateway

### Hợp đồng và kênh

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-GW-001 | Hệ thống phải mô tả mọi route REST (lệnh, truy vấn, cấu hình) trong `contracts/openapi.json` theo OpenAPI 3.1, sinh từ chính ứng dụng FastAPI của `robot-core`; CI sinh lại file này và không qua khi nó khác bản đã commit. | Client của `operator-ui` sinh từ hợp đồng; hợp đồng lệch khỏi mã phải bị phát hiện tự động. | integration, inspection | bắt buộc | ADR 0006 |
| REQ-GW-002 | Hệ thống phải phát telemetry, sự kiện và vòng đời lệnh tới HMI trên đúng một kênh WebSocket qua TLS (WSS), mô tả trong `contracts/asyncapi.yaml` theo AsyncAPI 3; hệ thống không mở kênh đẩy nào khác tới HMI. | HMI chỉ mở và xác thực một kết nối cho mọi dữ liệu đẩy. | integration, inspection | bắt buộc | ADR 0006 |
| REQ-GW-003 | Hệ thống phải mô tả payload của mọi route REST và mọi thông điệp WSS bằng JSON Schema trong `contracts/schemas/`, và mọi payload hệ thống gửi đi phải hợp lệ theo schema của nó. | `robot-core` và `operator-ui` dựa trên cùng một hợp đồng máy đọc được. | unit, integration | bắt buộc | ADR 0006 |
| REQ-GW-004 | Hệ thống phải gửi mọi payload REST và WSS dưới dạng JSON hợp lệ theo RFC 8259; số không hữu hạn (NaN, +∞, −∞) ở mọi độ sâu được gửi thành `null`, nghĩa là không đo được. | JSON không biểu diễn được NaN hay vô cực; một số hỏng làm client không đọc được cả gói. | unit | bắt buộc | ADR 0006 |
| REQ-GW-005 | Hệ thống phải bọc mỗi thông điệp WSS trong một envelope dùng tên thuộc tính của CloudEvents cho định danh, nguồn, loại và thời điểm của thông điệp, cộng thuộc tính `sequence`; trên cùng một kết nối, thông điệp phát sau có `sequence` lớn hơn thông điệp phát trước. | HMI phân loại được thông điệp và biết thứ tự của chúng. | unit, integration | bắt buộc | ADR 0006 |
| REQ-GW-006 | Hệ thống không được nhận lệnh vận hành, lệnh cấu hình hay lệnh chuyển động qua kênh WSS; các lệnh này chỉ đi qua REST. | Lệnh qua REST có hợp đồng OpenAPI, kiểm quyền và kết quả riêng cho từng yêu cầu. | unit, integration | bắt buộc | ADR 0006 |
| REQ-GW-007 | Với mỗi lệnh đã nhận qua REST, hệ thống phải phát trên kênh WSS các sự kiện vòng đời của lệnh, và client phải gắn được mỗi sự kiện với đúng lệnh đã gửi. | Lệnh gửi qua REST, còn tiến trình của lệnh đi về trên kênh WSS. | unit, integration | bắt buộc | ADR 0006, REQ-MIS-012 |
| REQ-GW-008 | Hệ thống phải phát trên kênh WSS ngay khi xảy ra, không chờ chu kỳ telemetry kế, các sự kiện: chuyển pha (trạng thái cũ, trạng thái mới, mã lý do, tham số), lệnh chuyển động bị chặn (mã, tham số), lỗi, và đổi mức giám sát (mức mới, mã lý do). | Telemetry theo chu kỳ có thể bỏ sót một trạng thái chỉ kéo dài trong một nhịp. | unit, SIM | bắt buộc | ADR 0006, REQ-MIS-002, REQ-REC-007 |
| REQ-GW-009 | Hệ thống không được trả header CORS cho origin nằm ngoài danh sách origin khai trong cấu hình; danh sách mặc định rỗng, tức không nhận yêu cầu cross-origin nào. | HMI được phục vụ cùng origin qua service `hmi`; chỉ khi phát triển mới cần mở cho origin khác. | unit | bắt buộc | ADR 0006 |
| REQ-GW-010 | Hệ thống phải chỉ cho LAN của trạm tới REST và kênh WSS qua cổng HTTPS 443 của service `hmi`, nơi lo TLS và làm proxy tới service `core`; service `core` không được mở cổng ra mạng của trạm, và không cổng nào được mở vào từ WAN. | Mọi trao đổi giữa trình duyệt và `core` đi qua một cổng có TLS; cookie `Secure` cần kênh mã hoá. | integration, inspection | bắt buộc | ADR 0006 |

### Lệnh và lỗi

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-GW-011 | Hệ thống phải khai trong hợp đồng kiểu tham số riêng của từng lệnh REST, và từ chối lệnh có tham số thiếu, sai kiểu hoặc ngoài miền trước khi lệnh tới module miền, bằng problem details với mã `cmd.bad_params` kèm danh sách trường sai. | Tham số sai bị chặn ở biên, không gây ngoại lệ bên trong module miền. | unit | bắt buộc | ADR 0006 |
| REQ-GW-012 | Hệ thống phải từ chối lệnh không có trong hợp đồng bằng problem details với mã `cmd.unknown`. | Client phân biệt lệnh không tồn tại với lệnh bị từ chối vì trạng thái của máy. | unit | bắt buộc | ADR 0006 |
| REQ-GW-013 | Hệ thống phải trả cho mỗi lệnh được nhận một mã kết quả ổn định (`cmd.*`) kèm tham số và trạng thái FSM sau khi xử lý; câu chữ hiển thị do HMI dịch từ mã qua `locales/` (vi, en). | Mã dịch được và so được trong test; câu văn thì không. | unit | bắt buộc | ADR 0006, REQ-MIS-012 |
| REQ-GW-014 | Hệ thống phải trả mọi lỗi của REST bằng problem details, với mã HTTP đúng loại lỗi (chưa đăng nhập, thiếu quyền, không tìm thấy, xung đột với trạng thái, tham số sai, lỗi nội bộ, chưa sẵn sàng) và một mã ổn định lấy từ danh mục mã lỗi kèm tham số; phản hồi không được chứa traceback hay chi tiết nội bộ. | HMI và bản dịch dựa vào mã ổn định; chi tiết nội bộ không được lộ ra mạng của trạm. | unit, integration | bắt buộc | ADR 0006 |
| REQ-GW-015 | Khi xử lý một lệnh gặp ngoại lệ không lường trước, hệ thống phải trả problem details với mã HTTP 500 và mã lỗi nội bộ riêng, không dùng `cmd.bad_params`, ghi log kèm traceback, và phát sự kiện lệnh thất bại trên kênh WSS. | Lỗi của hệ thống không được hiện ra như lỗi tham số của người gửi. | unit | bắt buộc | ADR 0006, REQ-GW-007 |

### Telemetry

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-GW-016 | Hệ thống phải phát telemetry trên kênh WSS với chu kỳ mặc định 40 ms (25 Hz); mỗi gói gồm các khối: thời điểm và nguồn dữ liệu (đo thật hay mô phỏng); pha và trạng thái `SAFE_HOLD`; mức giám sát và khoảng hở; phiên sạc; bãi, bay, hàng đợi điều phối và danh mục xe; chuyển động, động học và mô-men; tay máy, ray, I/O, cảm biến hiện diện và kênh lực; camera và perception; lỗi giả lập đang bật; tình trạng của cấu hình trạm, bản ghi và log; phiên bản đang chạy. | HMI dựng mọi màn hình từ telemetry; nội dung từng khối do requirement của vùng sở hữu khối đó quy định. | unit, SIM | bắt buộc | ADR 0006 |
| REQ-GW-017 | Khi dựng một khối của telemetry bị lỗi, hệ thống phải vẫn phát các khối khác, đánh dấu khối lỗi là không khả dụng kèm mã lỗi và ghi log; khi không dựng được cả gói, hệ thống không phát gói hỏng mà giữ gói hợp lệ gần nhất cùng thời điểm dựng của gói đó. | Một khối hỏng không được làm HMI mất toàn bộ trạng thái; thời điểm dựng cho HMI nhận ra dữ liệu cũ. | unit | bắt buộc | ADR 0006 |
| REQ-GW-018 | Hệ thống phải ngắt kết nối WSS của client không nhận kịp một thông điệp trong mặc định 0,25 s; việc gửi tới một client không được làm chậm việc phát tới client khác hay vòng giám sát. | Một trình duyệt chậm không được kéo trễ HMI khác hay vòng giám sát. | unit, integration | bắt buộc | ADR 0006 |
| REQ-GW-019 | Hệ thống phải trả bản chụp telemetry mới nhất qua một route REST, cùng schema với gói telemetry trên kênh WSS. | Công cụ dòng lệnh và script đọc được trạng thái mà không cần mở kênh WSS. | unit | bắt buộc | ADR 0006, REQ-AUTH-006 |

### Khởi động, sức khoẻ và tắt

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-GW-020 | Hệ thống không được kết nối thiết bị, ghi file hay chạy luồng, task nền khi import package `robot_core` hay khi tạo ứng dụng bằng app factory; các việc này chỉ bắt đầu ở bước khởi động của ứng dụng. | Test và công cụ import được mã mà không kéo theo thiết bị. | unit, inspection | bắt buộc | ADR 0003 |
| REQ-GW-021 | Hệ thống phải dựng mọi module và adapter trong app factory theo cấu hình đã kiểm, với adapter thật hay adapter mô phỏng được chọn tường minh trong cấu hình; khi thiết bị đã cấu hình không kết nối được lúc khởi động, hệ thống vẫn khởi động, báo thiết bị mất kết nối và không thay nó bằng adapter mô phỏng. | Chạy mô phỏng thay cho thiết bị thật đã mất làm người vận hành tin vào trạng thái không có thật. | unit, integration | bắt buộc | ADR 0003, ADR 0005, REQ-MOT-024 |
| REQ-GW-022 | Khi khởi động, hệ thống phải nạp cấu hình trạm (REQ-CFG-002), dựng adapter và chạy vòng giám sát trước khi nhận yêu cầu REST hay kết nối WSS nào. | Lệnh đến trước khi cấu hình và adapter sẵn sàng sẽ chạy trên trạng thái chưa xác định. | unit, integration | bắt buộc | REQ-MIS-013 |
| REQ-GW-023 | Hệ thống phải trả `/api/health` với mã 200 chỉ khi vòng giám sát đã chạy một nhịp trong 1 s vừa qua, port của tay máy đã kết nối và không chốt lỗi, và thư viện động học đã nạp; trường hợp còn lại trả 503 kèm tên các phép kiểm trượt; route này không cần đăng nhập và không trả dữ liệu vận hành nào khác. | Healthcheck của Docker và bước kiểm sức khoẻ sau cập nhật dựa vào trạng thái thật của máy, không vào một hằng số. | unit, integration | bắt buộc | ADR 0013, REQ-OTA-011 |
| REQ-GW-024 | Khi nhận SIGTERM, trước khi tiến trình thoát, hệ thống phải yêu cầu mọi cơ cấu chấp hành dừng qua port, đóng kết nối thiết bị, ghi xong và đóng bản ghi MCAP, ghi dấu tắt sạch vào journal mất điện (REQ-REC-003) và nhả camera. | Dừng có kiểm soát, và lần khởi động sau biết lần tắt trước là sạch. | unit, integration | bắt buộc | ADR 0005 |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-GW-025 | Hệ thống phải gán cho mỗi lệnh REST một ID; client gửi kèm lệnh thời hạn hiệu lực, khoá chống lặp và phiên bản trạng thái mà client đã thấy; lệnh hết hạn hay dựa trên phiên bản trạng thái đã cũ bị từ chối, lệnh gửi lặp cùng khoá chỉ chạy một lần; vòng đời lệnh gồm các trạng thái chờ, đã nhận, bị từ chối, hết hạn, chưa rõ và đã hoàn tất về vật lý. | Lệnh gửi lại khi mạng chập chờn không được chạy hai lần; lệnh dựa trên trạng thái cũ không được chạy. | unit, integration | đề xuất | ADR 0006, REQ-GW-007 |
| REQ-GW-026 | Hệ thống phải gắn cho mỗi ước lượng trong telemetry nguồn, cờ hợp lệ, tuổi (s) và miền đồng hồ của dấu thời gian. | Số hợp lệ về kiểu chưa chắc là số đo tin cậy; HMI cần biết số từ đâu và cũ bao nhiêu. | unit | đề xuất | ADR 0006 |
| REQ-GW-027 | Hệ thống phải phát trong telemetry các giá trị đang có hiệu lực của nhóm ngưỡng an toàn và giới hạn của ứng dụng (REQ-CFG-011). | Người vận hành thấy máy đang chạy với ngưỡng nào. | unit | đề xuất | ADR 0005 |

## AUTH: xác thực

### Tài khoản và phiên đăng nhập

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-AUTH-001 | Hệ thống phải quản lý tài khoản người dùng, mỗi tài khoản có một hoặc nhiều vai trò trong bảng "Vai trò"; tài khoản bị khoá không đăng nhập được, và các phiên đăng nhập đang mở của nó bị huỷ. | Mỗi thao tác gắn với một người và một vai trò, nên phân quyền và kiểm toán được. | unit, integration | bắt buộc | ADR 0005 |
| REQ-AUTH-002 | Hệ thống phải lưu mật khẩu chỉ dưới dạng băm argon2id (RFC 9106), với tham số không thấp hơn mức tối thiểu của OWASP: 19 MiB bộ nhớ, 2 lượt lặp, 1 luồng. | File tài khoản bị lộ không làm lộ mật khẩu. | unit, inspection | bắt buộc | — |
| REQ-AUTH-003 | Hệ thống không được có tài khoản hay mật khẩu mặc định; tài khoản quản trị đầu tiên chỉ được tạo bằng lệnh `admin create` chạy trên thiết bị (REQ-CLI-006). | Mật khẩu mặc định là lỗ hổng phổ biến của thiết bị lắp tại chỗ. | integration, inspection | bắt buộc | — |
| REQ-AUTH-004 | Khi đăng nhập thành công, hệ thống phải tạo một phiên đăng nhập phía máy chủ với định danh mới, sinh bằng bộ sinh số ngẫu nhiên an toàn mật mã, và gửi định danh đó trong session cookie có `Secure`, `HttpOnly` và `SameSite=Strict`; đăng xuất huỷ phiên phía máy chủ. | Cookie chỉ đi qua kênh mã hoá, script không đọc được và không đi kèm yêu cầu từ site khác; định danh mới ở mỗi lần đăng nhập chống cố định phiên. | unit, integration | bắt buộc | ADR 0006 |
| REQ-AUTH-005 | Hệ thống không được nhận hay phát thông tin xác thực (mật khẩu, định danh phiên, token) trên URL, kể cả query string của URL kênh WSS. | Thông tin trên URL lọt vào log truy cập, lịch sử trình duyệt và header `Referer`. | unit, inspection | bắt buộc | ADR 0006 |
| REQ-AUTH-006 | Hệ thống phải đòi phiên đăng nhập hợp lệ cho mọi route REST và mọi lần bắt tay WSS, trừ route đăng nhập và `/api/health`; yêu cầu REST không có phiên hợp lệ nhận problem details mã HTTP 401 với mã `err.auth.required`, còn bắt tay WSS không có phiên hợp lệ bị từ chối trước khi nâng cấp kết nối. | Không route nào, kể cả nhập và khôi phục cấu hình, nhận yêu cầu từ một máy chưa đăng nhập trong mạng của trạm. | unit, integration | bắt buộc | ADR 0005, ADR 0006 |
| REQ-AUTH-007 | Hệ thống phải kiểm vai trò của phiên đăng nhập cho từng route và từng lệnh theo bảng "Vai trò"; phiên thiếu vai trò nhận problem details mã HTTP 403 với mã lỗi riêng, và hệ thống không thực hiện gì. | Người chỉ có vai trò vận hành không đổi được cấu hình hay chạy tay. | unit, integration | bắt buộc | ADR 0005 |
| REQ-AUTH-008 | Hệ thống phải trả cho phiên đăng nhập hiện tại: tài khoản, vai trò, thời điểm phiên hết hạn và thời điểm hết hiệu lực của lần xác thực lại gần nhất; route này không trả mật khẩu, định danh phiên hay token, và trả giống nhau cho mọi client, kể cả client chạy trên chính host. | HMI hiển thị đúng quyền của người đang dùng mà không cần thông tin bí mật. | unit | bắt buộc | ADR 0006 |
| REQ-AUTH-009 | Hệ thống không được có cấu hình, biến môi trường hay cờ dòng lệnh nào tắt xác thực hoặc bỏ kiểm vai trò của API. | Công tắc tắt xác thực bỏ qua mọi ràng buộc về vai trò và xác thực lại của thao tác liên quan an toàn. | integration, inspection | bắt buộc | ADR 0005 |
| REQ-AUTH-010 | Hệ thống không được ghi mật khẩu, định danh phiên, token hay khoá riêng vào log, telemetry hay bản ghi MCAP. | Log và bản ghi được chép đi để chẩn đoán; bí mật trong đó là bí mật đã lộ. | unit, inspection | bắt buộc | ADR 0007 |

### Thao tác liên quan an toàn và nhật ký kiểm toán

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-AUTH-011 | Hệ thống phải thực hiện thao tác liên quan an toàn chỉ khi phiên đăng nhập có vai trò bảo trì và có lần xác thực lại còn hiệu lực; thiếu một trong hai thì từ chối với mã lỗi riêng cho từng trường hợp; mỗi lần thực hiện ghi một dòng nhật ký kiểm toán. | Thao tác liên quan an toàn có thể nới giới hạn hoặc đổi cách tay máy chuyển động. | unit, integration | bắt buộc | ADR 0005, REQ-ARM-014 |
| REQ-AUTH-012 | Hệ thống phải xác thực lại bằng mật khẩu của chính tài khoản đang đăng nhập; một lần xác thực lại chỉ có hiệu lực cho phiên đăng nhập đó, trong mặc định 300 s. | Một phiên bị bỏ ngỏ trên máy dùng chung không đủ để làm thao tác liên quan an toàn. | unit | bắt buộc | ADR 0005 |
| REQ-AUTH-013 | Hệ thống phải ghi mỗi dòng nhật ký kiểm toán với thời điểm UTC, tài khoản, vai trò, thao tác, tham số hoặc phạm vi, và kết quả; nhật ký không chứa mật khẩu, định danh phiên hay khoá; nhật ký còn nguyên qua khởi động lại, cập nhật và quay lại bản trước; API không có đường nào sửa hay xoá dòng đã ghi. | Nhật ký kiểm toán chỉ có giá trị khi đủ thông tin, bền và không sửa được qua chính hệ thống. | unit, integration | bắt buộc | ADR 0005, ADR 0007 |
| REQ-AUTH-014 | Hệ thống phải ghi nhật ký kiểm toán cho: mọi thao tác liên quan an toàn; mọi lần nhập và khôi phục cấu hình; bật đồng ý thu dữ liệu (REQ-HRV-002); bật đường hầm hỗ trợ từ xa (REQ-AUTH-019); kết quả cập nhật và mỗi lần quay lại bản trước (REQ-OTA-008); xác nhận checklist sau cập nhật (REQ-OTA-014); mỗi lần đổi model học máy (REQ-OTA-013); tạo tài khoản, đổi vai trò và khoá tài khoản. | Mỗi thay đổi ảnh hưởng tới an toàn, quyền riêng tư hay quyền truy cập đều truy được người làm. | unit, integration | bắt buộc | ADR 0005, ADR 0013, ADR 0014, ADR 0015, ADR 0016 |
| REQ-AUTH-015 | Hệ thống phải cho người có vai trò quản trị hoặc bảo trì đọc nhật ký kiểm toán qua API, lọc theo khoảng thời gian, tài khoản và loại thao tác. | Nhật ký phải đọc lại được, kể cả để xác nhận mỗi phiên bản model chạy trên một thiết bị trước khi tới thiết bị khác. | unit | bắt buộc | ADR 0015 |

### Danh tính thiết bị và hỗ trợ từ xa

Vận hành CA của dự án (giữ root offline, cấp chứng chỉ, phát hành danh sách thu hồi) nằm ngoài các thành phần trong repo; ADR 0016 quy định phần đó.

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-AUTH-016 | Hệ thống phải định danh mỗi thiết bị bằng một ID và một cặp khoá sinh ngay trên thiết bị khi provisioning (REQ-CLI-007); khoá riêng không rời thiết bị và nằm trong container ở `/run/secrets/`; chứng chỉ của thiết bị do CA của dự án cấp. | Khoá riêng không đi qua kênh truyền nào; lộ khoá của một thiết bị thì chỉ thu hồi chứng chỉ của thiết bị đó. | integration, inspection | bắt buộc | ADR 0007, ADR 0016 |
| REQ-AUTH-017 | Hệ thống phải dùng chứng chỉ thiết bị làm chứng chỉ client khi kết nối tới máy chủ cập nhật và máy chủ dữ liệu qua TLS 1.3, và kiểm chứng chỉ của máy chủ theo CA của dự án, từ chối kết nối khi không khớp. | Hai phía xác thực lẫn nhau; thiết bị không nhận bản cập nhật hay gửi dữ liệu cho máy chủ giả. | integration | bắt buộc | ADR 0013, ADR 0014, ADR 0016 |
| REQ-AUTH-018 | Hệ thống phải đổi cặp khoá và chứng chỉ của thiết bị ít nhất mỗi năm một lần; cặp khoá mới cũng sinh trên thiết bị. | Giới hạn thời gian một khoá bị lộ còn dùng được. | integration | bắt buộc | ADR 0016 |
| REQ-AUTH-019 | Hệ thống không được có đường vào thiết bị từ xa theo mặc định; chỉ khi người có vai trò bảo trì bật tại trạm, thiết bị mới mở một đường hầm chiều ra tới máy chủ của dự án; đường hầm tự đóng khi hết thời hạn đặt lúc bật, và mỗi lần bật ghi một dòng nhật ký kiểm toán. | Không có cổng nào mở vào thiết bị từ WAN; đường vào chỉ có khi người tại chỗ cho phép và tự hết hạn. | integration, inspection | bắt buộc | ADR 0016 |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-AUTH-020 | Ở mỗi lần bắt tay WSS, hệ thống phải kiểm header `Origin` theo danh sách cho phép và từ chối bắt tay khi không khớp. | Trình duyệt gửi cookie kèm bắt tay WebSocket; OWASP coi `SameSite` chỉ là lớp phòng thủ thêm trước Cross-Site WebSocket Hijacking. | unit, integration | đề xuất | ADR 0006 |
| REQ-AUTH-021 | Hệ thống phải chống CSRF cho mọi yêu cầu REST làm đổi trạng thái bằng một biện pháp ngoài `SameSite=Strict`, theo hướng dẫn của OWASP. | OWASP coi `SameSite` là lớp phòng thủ thêm, không thay cho biện pháp chống CSRF. | unit, integration | đề xuất | ADR 0006 |
| REQ-AUTH-022 | Hệ thống phải huỷ phiên đăng nhập sau một khoảng không có thao tác (giá trị ứng viên 30 min) và sau một thời hạn tuyệt đối kể từ lúc đăng nhập (giá trị ứng viên 12 h). | Phiên bỏ ngỏ trên máy dùng chung không được dùng mãi. | unit | đề xuất | ADR 0006 |

## CFG: cấu hình

### File cấu hình trạm

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-001 | Hệ thống phải lưu cấu hình trạm trong một file JSON ở volume `ev-arm-config` (`/var/lib/ev-arm/config`); file hợp lệ theo JSON Schema trong `contracts/schemas/` và mang phiên bản schema; repo chỉ giữ file mẫu `deploy/site/station.example.json`. | Cấu hình còn nguyên khi thay container; schema cấu hình là hợp đồng công khai. | unit, inspection | bắt buộc | ADR 0007 |
| REQ-CFG-002 | Khi khởi động, hệ thống phải nạp cấu hình trạm: chưa có file thì chạy với giá trị mặc định; file không đọc được hay không hợp lệ (REQ-CFG-008) thì đổi tên thành `<tên file>.corrupt.<thời điểm UTC>.json`, chạy với giá trị mặc định và báo lỗi nạp; file có phiên bản schema mới hơn bản hệ thống hiểu thì để nguyên, chạy với giá trị mặc định, báo lỗi nạp và không ghi đè file đó trừ khi người có vai trò bảo trì nhập hay khôi phục cấu hình. | File hỏng không chặn khởi động nhưng được giữ lại để xem và khôi phục; file của một bản phần mềm mới hơn không bị ghi đè ngầm. | unit, integration | bắt buộc | ADR 0007, REQ-MIS-013 |
| REQ-CFG-003 | Hệ thống phải ghi file cấu hình trạm một cách nguyên tử: ghi ra file tạm trong cùng thư mục, `fsync`, rồi đổi tên đè lên file cũ; file ghi kèm phiên bản schema và thời điểm lưu. | Mất điện giữa lúc ghi không để lại file cấu hình nửa cũ nửa mới. | unit, integration | bắt buộc | ADR 0007 |
| REQ-CFG-004 | Hệ thống phải lưu cấu hình trạm ngay sau mỗi thay đổi được nhận và kiểm kết quả ghi; lệnh chỉ trả thành công khi đã lưu xong, còn khi ghi lỗi thì lệnh trả lỗi với mã riêng và lỗi được báo qua telemetry. | Người bảo trì không được tin là cấu hình đã lưu trong khi lần khởi động sau chạy cấu hình khác. | unit | bắt buộc | — |
| REQ-CFG-005 | Hệ thống phải phát qua telemetry tình trạng của cấu hình trạm: đường dẫn file, file có tồn tại không, thời điểm lưu gần nhất, lỗi nạp và lỗi lưu gần nhất. | Người vận hành thấy ngay cấu hình có được nạp và lưu đúng không. | unit | bắt buộc | ADR 0006 |
| REQ-CFG-006 | Hệ thống phải lấy mọi giá trị mặc định của cấu hình (ngưỡng, giới hạn, hình học trạm, keepout, ray, danh mục xe, camera) từ một nguồn duy nhất có schema trong `robot-core/src/robot_core/defaults/`; repo không được có file giới hạn hay file cấu hình mặc định nào ngoài nguồn đó. | Một file giới hạn mà mã không đọc, với số khác số đang chạy, làm người đọc tin sai vào giới hạn của máy. | inspection, unit | bắt buộc | ADR 0005 |
| REQ-CFG-007 | Hệ thống phải chia cấu hình trạm thành các nhóm, mỗi nhóm có mô tả và schema riêng: danh mục và hồ sơ xe; bố cục bãi; hình học trạm; keepout; ray; I/O; đầu ra chuyển động; model tay máy và hồ sơ tool; bay đang có xe; camera (nguồn, trạng thái, hiệu chuẩn, camera đang chọn); ngưỡng an toàn và giới hạn của ứng dụng. | Kiểm, xuất, nhập và khôi phục làm theo từng nhóm. | unit, inspection | bắt buộc | — |

### Kiểm và áp

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-008 | Hệ thống phải kiểm toàn bộ một thay đổi cấu hình, gồm schema, biên cứng, ràng buộc chéo và quy tắc thu hẹp (REQ-CFG-009), trước khi áp; có một mục không đạt thì không áp gì và trả mọi lý do kèm mã và tham số; đạt hết thì áp tất cả cùng lúc; quy tắc này áp cho lệnh cấu hình, nhập, khôi phục và lần nạp lúc khởi động. | Áp từng phần rồi bỏ qua phần hỏng để lại một cấu hình chưa ai kiểm. | unit, integration | bắt buộc | ADR 0005 |
| REQ-CFG-009 | Hệ thống phải từ chối mọi cấu hình đặt một giới hạn an toàn hay giới hạn của ứng dụng rộng hơn giá trị mặc định đi kèm phần mềm; schema khai cho mỗi giới hạn chiều được phép thu hẹp. | Cấu hình trạm chỉ được thu hẹp giới hạn, không được nới. | unit | bắt buộc | ADR 0005 |
| REQ-CFG-010 | Hệ thống phải coi việc đổi nhóm ngưỡng an toàn và giới hạn của ứng dụng, nhóm model tay máy và hồ sơ tool, hay nhóm đầu ra chuyển động là thao tác liên quan an toàn (REQ-AUTH-011), kể cả khi thay đổi đi qua nhập hay khôi phục cấu hình; thay đổi các nhóm khác cần vai trò bảo trì. | Nhập một bundle cấu hình không được là đường vòng để đổi cấu hình an toàn. | unit, integration | bắt buộc | ADR 0005, REQ-ARM-014 |
| REQ-CFG-011 | Hệ thống phải có trong nhóm ngưỡng an toàn và giới hạn của ứng dụng: khoảng hở dừng (mặc định 0,80 m, chỉ được tăng); khoảng hở giảm tốc (mặc định 1,60 m, chỉ được tăng, luôn lớn hơn khoảng hở dừng); giới hạn lực (mặc định 100 N, chỉ được giảm); lực chạm đáy (mặc định 35 N, luôn nhỏ hơn giới hạn lực); nhiệt độ chân sạc tối đa (mặc định 85 °C, chỉ được giảm); ngưỡng tuổi khung của camera cổ tay (mặc định 150 ms, chỉ được giảm); thời gian phiên sạc tối đa (mặc định 14 400 s); thời hạn di chuyển tới điểm chờ (mặc định 60 s); mỗi giá trị có biên cứng trong schema. | Requirement của mission và motion đọc các giá trị này từ một nhóm cấu hình đã kiểm. | unit | bắt buộc | ADR 0005, REQ-MIS-035, REQ-MIS-039, REQ-MIS-043, REQ-MIS-053, REQ-MIS-054, REQ-MIS-073, REQ-MIS-074 |
| REQ-CFG-012 | Hệ thống phải cho chạy thử một thay đổi cấu hình hay một bundle cấu hình: trả kết quả đạt hay không, các lý do chặn, các cảnh báo, phần khác so với cấu hình đang chạy và các nhóm bị đụng, mà không đổi gì. | Người bảo trì xem trước tác động trước khi áp. | unit | bắt buộc | — |

### Xuất, nhập, sao lưu và khôi phục

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-013 | Hệ thống phải xuất cấu hình đang chạy, theo các nhóm được chọn trong mọi nhóm của REQ-CFG-007, thành một bundle cấu hình gồm định danh loại, phiên bản bundle, nội dung từng nhóm kèm mô tả, và checksum SHA-256 của nội dung; bundle xuất ra phải nhập lại được vào cùng phiên bản phần mềm. | Sao cấu hình sang trạm khác hay giữ lại để khôi phục. | unit, integration | bắt buộc | — |
| REQ-CFG-014 | Hệ thống phải trả qua API danh sách nhóm cấu hình kèm mô tả, cho biết nhóm nào thuộc thao tác liên quan an toàn và trạng thái nào của máy cho phép đổi hay nhập. | HMI và công cụ biết trước nhóm nào cần xác thực lại và lúc nào được nhập. | unit | bắt buộc | REQ-MIS-072 |
| REQ-CFG-015 | Khi nhập một bundle cấu hình, hệ thống phải: kiểm định danh loại, phiên bản bundle, tên nhóm và nội dung từng nhóm theo REQ-CFG-008; sao lưu cấu hình đang chạy (REQ-CFG-016); áp mọi nhóm theo thứ tự phụ thuộc; rồi tính lại số bay phục vụ được, và khi số đó ít hơn trước lúc nhập thì tự khôi phục cấu hình trước và trả mã lý do riêng; checksum không khớp chỉ sinh cảnh báo. | Bundle sai không được làm trạm mất bay đang phục vụ được; bundle sửa tay vẫn nhập được khi qua mọi phép kiểm. | unit, integration | bắt buộc | ADR 0005, REQ-MIS-072, REQ-MIS-080 |
| REQ-CFG-016 | Trước mỗi lần nhập, khôi phục cấu hình hay cập nhật, hệ thống phải sao lưu cấu hình đang chạy, kèm hiệu chuẩn camera, hand-eye và model tay máy custom, vào volume `ev-arm-state` (`/var/lib/ev-arm/state`), mỗi bản một thư mục đặt tên theo thời điểm UTC dạng `20261111T084000Z/`. | Khôi phục và quay lại bản trước cần bản sao lưu đầy đủ, nằm ngoài volume cấu hình. | unit, integration | bắt buộc | ADR 0007, ADR 0013 |
| REQ-CFG-017 | Hệ thống phải liệt kê qua API tối đa 20 bản sao lưu gần nhất, mỗi bản kèm danh sách file. | Người bảo trì chọn được bản để khôi phục. | unit | bắt buộc | — |
| REQ-CFG-018 | Hệ thống phải khôi phục cấu hình từ một bản sao lưu chọn theo ID, hoặc từ bản mới nhất khi không chọn, theo REQ-CFG-008, và trả danh sách nhóm đã khôi phục cùng các nhóm không có trong bản sao lưu. | Có đường quay về một cấu hình đã chạy đúng. | unit, integration | bắt buộc | REQ-MIS-072 |
| REQ-CFG-019 | Khi nạp cấu hình có phiên bản schema cũ hơn, hệ thống phải sao lưu file gốc rồi chuyển đổi lên phiên bản hiện tại; hệ thống không bao giờ chuyển đổi schema theo chiều lùi, và khi hạ phiên bản phần mềm thì lấy lại cấu hình từ bản sao lưu. | Chuyển đổi một chiều có sao lưu thì hạ phiên bản không phải đoán ngược dữ liệu. | unit, integration | bắt buộc | ADR 0013 |

### Trạm, ray và bãi

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-020 | Hệ thống phải cấu hình ray gồm: có ray hay không, loại driver, vị trí cố định của đế khi không có ray (mặc định 5,0 m), biên hành trình nhỏ nhất và lớn nhất (mặc định 0,50 m và 18,00 m) và vị trí home; lệnh đổi cấu hình ray tạo lại driver, áp ngay và lưu cấu hình; loại driver chưa có adapter bị từ chối với mã riêng. | Ray là cấu hình của từng trạm, không phải hằng số trong mã. | unit, SIM | bắt buộc | REQ-MIS-072, REQ-MOT-013, REQ-MOT-019 |
| REQ-CFG-021 | Khi nhận lệnh khoá ray tại chỗ (`lock_rail_here`), hệ thống phải đặt cấu hình ray thành không có driver với biên nhỏ nhất và lớn nhất bằng vị trí ray đo được, tính lại kết luận phục vụ được của xe và lưu cấu hình. | Trạm có ray mà chưa có drive vẫn dùng được tay máy ở một vị trí cố định. | unit, SIM | bắt buộc | REQ-MIS-072, REQ-MIS-080 |
| REQ-CFG-022 | Hệ thống phải cấu hình bố cục bãi song song hoặc vuông góc (mặc định vuông góc); lệnh đổi bố cục tạo lại danh sách bay, tính lại kết luận phục vụ được, giữ nguyên trạng thái FSM, lưu cấu hình và trả số bay phục vụ được trên tổng số bay. | Bố cục quyết định vị trí bay và cách xe đỗ. | unit, SIM | bắt buộc | REQ-MIS-072, REQ-MIS-080, REQ-ARM-012 |
| REQ-CFG-023 | Hệ thống phải mô tả hình học trạm bằng các khoá có kiểu, biên cứng, giá trị mặc định và cờ cần khởi động lại, gồm: tên trạm; kích thước và tâm bãi; trục và độ cao gốc của ray, tốc độ, gia tốc và vị trí home của ray; kích thước, khoảng cách và vị trí bay của từng bố cục; dung sai đỗ về vị trí và góc; vị trí bánh xe theo tỉ lệ kích thước xe; chiều dài tool không thuộc hình học trạm mà lấy từ hồ sơ tool. | Mỗi trạm có hình học riêng; khoá ảnh hưởng mô hình động học chỉ có hiệu lực sau khi khởi động lại. | unit, inspection | bắt buộc | REQ-MOT-013, REQ-ARM-004 |
| REQ-CFG-024 | Khi nhận lệnh đổi hình học trạm, hệ thống phải kiểm từng trường theo biên và các ràng buộc chéo (các bay không chồng nhau, bay nằm trong bãi, bay không cắt hành lang của ray, vạch sơn nằm trong bay, bánh trước ở trước bánh sau, ray nằm trong bãi), áp cả thay đổi hoặc không áp gì, trả mã kèm tham số cho từng trường bị từ chối, báo các khoá cần khởi động lại, tạo lại danh sách bay và lưu cấu hình. | Hình học sai làm tay máy tính đường đi tới chỗ không có thật. | unit | bắt buộc | REQ-MIS-072, REQ-MIS-080 |
| REQ-CFG-025 | Khi nhận lệnh đặt lại hình học trạm, hệ thống phải đưa hình học về giá trị mặc định, tạo lại danh sách bay và lưu cấu hình. | Có đường quay về một hình học đã biết. | unit | bắt buộc | REQ-MIS-072 |
| REQ-CFG-026 | Hệ thống phải trả qua API danh mục khoá hình học (nhóm, kiểu, biên, giá trị mặc định, giá trị hiện tại, cờ cần khởi động lại) để HMI dựng ô nhập, cùng thông tin bãi (tên, chiều rộng, chiều sâu, tâm). | HMI không chép biên và kiểu của từng khoá vào mã của mình. | unit | bắt buộc | ADR 0006 |
| REQ-CFG-027 | Hệ thống phải cấu hình keepout gồm: đệm của vỏ bao xe, độ co của vỏ khi rảnh và khi đang làm việc, tâm và tỉ lệ phủ của vỏ, bán kính vùng miễn trừ quanh cổng sạc và quanh thân đầu sạc, cách miễn trừ và các pha được miễn trừ, tỉ lệ lõi không bao giờ được miễn trừ; mỗi khoá có biên cứng; lệnh đổi keepout trả danh sách lý do khi bị từ chối và lưu cấu hình khi được nhận. | Vỏ bao xe là đầu vào của phép kiểm va chạm. | unit | bắt buộc | REQ-MIS-072, REQ-MOT-020, REQ-MOT-023 |
| REQ-CFG-028 | Hệ thống phải có trong giá trị mặc định danh sách camera gồm camera cổ tay `ARM-C01` và hai camera toàn cảnh `GLOBAL-C01` (ToF), `GLOBAL-C02` (RGB); khi danh sách camera trong cấu hình trạm không có camera cổ tay, hệ thống dùng danh sách mặc định và báo cảnh báo. | Camera cổ tay là bắt buộc để tìm và căn cổng sạc. | unit | bắt buộc | REQ-MIS-074 |

### Xe và cổng sạc

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-029 | Hệ thống phải có trong `robot-core/src/robot_core/defaults/vehicles/` danh mục 12 xe, mỗi xe gồm hãng và model, kích thước, phía có cổng sạc, loại đầu sạc, vị trí cổng trên thân xe và thông số pin, kèm nguồn gốc số liệu (mặc định là ước lượng). | Kết luận phục vụ được và đường tiếp cận dựa trên kích thước xe và vị trí cổng. | unit, inspection | bắt buộc | REQ-MIS-079 |
| REQ-CFG-030 | Hệ thống phải nhận hồ sơ đo của từng xe (kích thước, vị trí cổng), kiểm theo schema và biên trước khi áp, lưu trong cấu hình trạm với nguồn gốc là số đo, và dùng hồ sơ đó thay cho số ước lượng của cùng xe. | Số đo tại trạm chính xác hơn số ước lượng của danh mục. | unit | bắt buộc | — |
| REQ-CFG-031 | Hệ thống phải có trong giá trị mặc định mô hình hình học của đầu sạc CCS2 (khung, thân, hốc) kèm cờ cho biết số liệu là đo hay ước lượng, và báo các loại đầu sạc chưa có mô hình (CHAdeMO, GB/T, NACS) là chưa có mô hình. | Phép kiểm va chạm và căn trục dùng hình học của đầu sạc. | unit | bắt buộc | REQ-MOT-023 |
| REQ-CFG-032 | Hệ thống phải tính tư thế cổng sạc trong khung thế giới, gồm vị trí, pháp tuyến và hướng then, từ vị trí cổng trên thân xe, độ nghiêng bề mặt thân, tư thế đỗ và độ nghiêng của xe. | Điểm chờ, căn trục và cắm đều tính theo tư thế này. | unit | bắt buộc | — |
| REQ-CFG-033 | Hệ thống phải tính vị trí và góc yaw của xe trong bay theo bố cục: bố cục song song theo vạch hông và chặn bánh; bố cục vuông góc chọn hướng đỗ theo phía có cổng sạc của xe. | Mô phỏng và kết luận phục vụ được cần biết xe đỗ ở đâu trong bay. | unit, SIM | bắt buộc | — |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CFG-034 | Khi cấu hình trạm có lỗi nạp (REQ-CFG-002), hệ thống không được rời `SAFE_HOLD` cho tới khi người có vai trò bảo trì nhập hay khôi phục được một cấu hình hợp lệ, hoặc xác nhận chạy với giá trị mặc định. | Hình học và danh mục mặc định có thể không khớp trạm thật. | unit, SIM | đề xuất | ADR 0005, REQ-MIS-015 |
| REQ-CFG-035 | Hệ thống phải gắn cho mỗi bundle cấu hình đã duyệt mã băm, người duyệt và thời điểm duyệt, và đánh dấu bundle mất hiệu lực khi phiên bản phần mềm, model tay máy, hồ sơ tool hay hiệu chuẩn mà bundle dựa vào thay đổi. | Cấu hình được duyệt cho một tổ hợp phần mềm và phần cứng có thể sai khi tổ hợp đó đổi. | unit | đề xuất | ADR 0005 |

## REC: ghi dữ liệu

### Journal mất điện

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-REC-001 | Hệ thống phải ghi journal mất điện vào một file JSON trong volume `ev-arm-state` (`/var/lib/ev-arm/state`), gồm: thời điểm UTC, pha, cờ nghi đầu sạc trong cổng kèm lý do, góc khớp, vị trí ray, bay đang phục vụ và dấu tắt sạch. | Lần khởi động sau cần biết tay máy ở đâu và đầu sạc có thể còn trong cổng hay không. | unit, inspection | bắt buộc | ADR 0007, REQ-MIS-023 |
| REQ-REC-002 | Hệ thống phải ghi journal mất điện một cách nguyên tử (file tạm cùng thư mục, `fsync`, đổi tên đè) ngay khi pha hay cờ nghi đầu sạc trong cổng đổi, và mỗi 5 s trong lúc còn lại; hệ thống không ghi journal ở mỗi nhịp giám sát. | Mất điện lúc nào cũng để lại một journal đọc được và mới; ghi ở mỗi nhịp tạo tải ghi đĩa không cần thiết. | unit, integration | bắt buộc | ADR 0007 |
| REQ-REC-003 | Hệ thống phải ghi dấu tắt sạch vào journal chỉ ở bước tắt có kiểm soát (REQ-GW-024), và lần ghi journal đầu tiên sau khi khởi động phải xoá dấu đó. | Phân biệt lần tắt có kiểm soát với mất điện hay tiến trình bị dừng đột ngột. | unit | bắt buộc | REQ-MIS-014 |
| REQ-REC-004 | Khi khởi động, hệ thống phải đọc journal mất điện trước khi rời `BOOT` và đưa cho FSM kết quả: có journal hay không, đọc được hay không, lần tắt trước có sạch không, pha và cờ nghi đầu sạc trong cổng đã ghi; journal thiếu hay hỏng không được làm dừng bước khởi động. | FSM quyết định cờ nghi đầu sạc trong cổng và mã `safehold.*` từ kết quả này. | unit, SIM | bắt buộc | ADR 0005, REQ-MIS-013, REQ-MIS-014 |

### Bản ghi MCAP

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-REC-005 | Hệ thống phải mở bản ghi MCAP trước khi vòng giám sát bắt đầu, mỗi phiên chạy một file trong volume `ev-arm-recordings` (`/var/lib/ev-arm/recordings`), gồm kênh telemetry và kênh sự kiện; việc ghi chạy nền, không chặn vòng giám sát. | Bản ghi có từ nhịp giám sát đầu tiên để chẩn đoán sự cố. | unit, integration | bắt buộc | ADR 0007, ADR 0010, REQ-REC-013 |
| REQ-REC-006 | Hệ thống phải ghi MCAP theo đặc tả MCAP, mỗi kênh mã hoá JSON kèm JSON Schema; `log_time` là giờ của host lúc ghi, `publish_time` là giờ của thiết bị nguồn đã quy đổi sang giờ của host, và bằng `log_time` khi nguồn không có giờ riêng. | Công cụ đọc MCAP hiểu được nội dung; hai mốc giờ cho thấy độ trễ giữa thiết bị và host. | unit | bắt buộc | — |
| REQ-REC-007 | Hệ thống phải ghi vào kênh sự kiện của MCAP mọi chuyển pha (trạng thái cũ, trạng thái mới, mã lý do, tham số), lệnh chuyển động bị chặn (mã, tham số), lỗi và đổi mức giám sát (mức mới, mã lý do), cùng nội dung với sự kiện trên kênh WSS (REQ-GW-008). | Bản ghi cho biết vì sao máy đổi trạng thái, không chỉ là đã đổi. | unit, SIM | bắt buộc | REQ-MIS-002, REQ-MIS-003 |
| REQ-REC-008 | Hệ thống phải ghi telemetry vào MCAP với tần số nền 2 Hz, tăng lên 30 Hz trong 7 s sau mỗi sự kiện, và ghi kèm 3 s telemetry trước sự kiện lấy từ bộ đệm. | Đủ chi tiết quanh sự cố mà dung lượng vẫn nhỏ lúc máy chạy bình thường. | unit | bắt buộc | — |
| REQ-REC-009 | Hệ thống phải đưa dữ liệu cần ghi qua một hàng đợi giới hạn 2000 gói; hàng đầy thì bỏ gói cũ nhất, đếm số gói bị bỏ và không chặn nơi gửi. | Đĩa chậm không được làm trễ vòng giám sát. | unit | bắt buộc | — |
| REQ-REC-010 | Hệ thống phải ngừng ghi một file MCAP khi file đạt giới hạn dung lượng (mặc định 200 MB) và báo lỗi qua tình trạng bản ghi. | Một phiên chạy dài không được làm đầy volume. | unit | bắt buộc | ADR 0007 |
| REQ-REC-011 | Hệ thống phải cho bật hay tắt việc ghi MCAP bằng cấu hình (biến môi trường `EV_ARM_RECORD`); thiếu thư viện MCAP hoặc mở file lỗi thì tắt việc ghi và báo lý do; tình trạng bản ghi (bật hay tắt, đường dẫn, số gói đã ghi, số gói bị bỏ, độ dài hàng đợi, lỗi) được phát qua telemetry. | Người vận hành biết sự cố có được ghi lại hay không. | unit | bắt buộc | ADR 0006 |

### Log và phiên chạy

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-REC-012 | Hệ thống phải ghi log ra stdout dưới dạng JSON, mỗi dòng gồm thời điểm UTC, mức, nguồn, nội dung và ID phiên chạy; tiến trình không tự ghi file log, việc giữ và xoay vòng log do logging driver `local` của Docker đảm nhận. | Log không làm đầy đĩa và nối được với bản ghi MCAP của cùng phiên chạy. | unit, inspection | bắt buộc | ADR 0007, REQ-AUTH-010 |
| REQ-REC-013 | Hệ thống phải cấp cho mỗi phiên chạy một ID duy nhất, có trong mọi dòng log, trong tên file MCAP và trong telemetry. | Nối log, bản ghi và telemetry của cùng một lần chạy khi chẩn đoán. | unit | bắt buộc | — |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-REC-014 | Hệ thống phải báo qua telemetry khi ghi journal mất điện thất bại, kèm thời điểm của lần ghi thành công gần nhất. | Journal không ghi được thì lần khởi động sau dựa vào trạng thái cũ mà không ai biết. | unit | đề xuất | ADR 0005 |
| REQ-REC-015 | Khi tổng dung lượng các file MCAP trong `ev-arm-recordings` vượt giới hạn cấu hình, hệ thống phải xoá file cũ nhất, không bao giờ xoá file đang ghi. | Volume bản ghi có giới hạn dung lượng; con số và cách áp chưa chốt. | unit | đề xuất | ADR 0007 |
| REQ-REC-016 | Hệ thống phải giữ trong bộ nhớ 2000 dòng nhật ký vận hành gần nhất, với các mức `INFO`, `WARN`, `ERROR` và `COMMAND`, và phát 25 dòng mới nhất qua telemetry. | HMI hiển thị diễn biến gần đây mà không cần đọc log của Docker. | unit | đề xuất | ADR 0006 |
| REQ-REC-017 | Hệ thống phải ghi vào bản ghi MCAP khung hình của camera cổ tay quanh mỗi sự kiện. | Hình ảnh giúp chẩn đoán lần cắm thất bại; khung có thể chứa người và biển số, mà ADR 0014 không quy định bản ghi MCAP. | unit | đề xuất | ADR 0007, ADR 0014 |

## HRV: harvest

Phía máy chủ dữ liệu (người được truy cập, thời hạn lưu mặc định 24 tháng, xoá theo yêu cầu, gán nhãn) nằm ngoài các thành phần trong repo; ADR 0014 quy định phần đó.

### Đồng ý

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-HRV-001 | Hệ thống phải để việc thu dữ liệu train ở trạng thái tắt theo mặc định; khi không có đồng ý đang hiệu lực, hệ thống không được chọn khung nào, ghi khung nào vào `ev-arm-harvest` hay gửi khung nào đi. | Không khung nào rời thiết bị khi người tại chỗ chưa chủ động bật. | unit | bắt buộc | ADR 0014 |
| REQ-HRV-002 | Hệ thống phải cho chỉ người có vai trò bảo trì bật đồng ý, kèm phạm vi bay và khoảng thời gian (bắt đầu, kết thúc); mỗi lần bật ghi một dòng nhật ký kiểm toán gồm người bật, thời điểm và phạm vi. | Mỗi lần bật để lại dấu vết người chịu trách nhiệm. | unit, integration | bắt buộc | ADR 0014, REQ-AUTH-014 |
| REQ-HRV-003 | Hệ thống phải cho thu hồi đồng ý; từ lúc thu hồi, hoặc từ lúc hết khoảng thời gian đã chọn, hệ thống không chọn thêm khung nào theo đồng ý đó. | Đồng ý thu hồi được và có thời hạn. | unit | bắt buộc | ADR 0014 |
| REQ-HRV-004 | Hệ thống phải chỉ chọn khung thuộc phạm vi bay và khoảng thời gian của một đồng ý đang hiệu lực. | Dữ liệu chỉ được thu ở nơi và lúc người tại chỗ đã cho phép. | unit | bắt buộc | ADR 0014 |

### Chọn khung và làm mờ

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-HRV-005 | Hệ thống phải chỉ chọn: khung có kết quả nhận dạng kém tin cậy hơn ngưỡng cấu hình, khung của lần cắm thất bại hoặc phải thử lại, và một mẫu ngẫu nhiên mỗi ngày không vượt mức trần cấu hình. | Chỉ gửi lượng dữ liệu cần để model tốt lên ở các ca nó còn sai. | unit | bắt buộc | ADR 0014 |
| REQ-HRV-006 | Hệ thống phải gắn cho mỗi khung được chọn: thời điểm, bay, lý do chọn, chỉ số nhận dạng (sai số chiếu lại, tỉ lệ inlier, khoảng cách Mahalanobis), nội tham số camera, tư thế cổng ước lượng và phiên bản model nhận dạng. | Máy chủ train cần biết khung được chọn vì sao và trong điều kiện nào. | unit | bắt buộc | ADR 0014, ADR 0015 |
| REQ-HRV-007 | Hệ thống phải cắt khung về vùng cổng sạc khi tư thế cổng ước lượng cho phép. | Giảm lượng dữ liệu gửi đi và phần ảnh có thể chứa người hay biển số. | unit | bắt buộc | ADR 0014 |
| REQ-HRV-008 | Hệ thống phải phát hiện mặt người và biển số trong khung được chọn và làm mờ chúng trước khi ghi khung xuống đĩa; khung chưa làm mờ không bao giờ được ghi xuống đĩa hay gửi đi. | Mặt người và biển số không được lưu hay gửi đi ở dạng nhận ra được. | unit, integration | bắt buộc | ADR 0014 |
| REQ-HRV-009 | Khi bộ làm mờ không chạy được hoặc độ tin cậy của kết quả thấp hơn ngưỡng cấu hình, hệ thống phải bỏ khung đó, không ghi gì xuống đĩa và đếm số khung bị bỏ. | Không chắc đã làm mờ đủ thì không giữ khung. | unit | bắt buộc | ADR 0014 |
| REQ-HRV-010 | Hệ thống phải làm mờ bằng một model học máy có giấy phép cho phép, chạy trên ONNX Runtime và được kê trong `third_party/assets.yaml` cùng nguồn và giấy phép. | Model chạy trên thiết bị đi theo mọi bản cài. | inspection | bắt buộc | ADR 0010, ADR 0011, ADR 0014 |

### Lưu và gửi

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-HRV-011 | Hệ thống phải giữ khung đã làm mờ chờ gửi trong volume `ev-arm-harvest` (`/var/lib/ev-arm/harvest`), ghi file ảnh trước rồi mới ghi mục tương ứng vào sổ hàng đợi, và nạp lại hàng đợi khi khởi động. | Mất điện giữa chừng không để lại mục sổ trỏ tới ảnh không có; hàng đợi còn nguyên qua khởi động lại. | unit, integration | bắt buộc | ADR 0007 |
| REQ-HRV-012 | Hệ thống phải xoá khung ngay sau khi gửi thành công, và xoá khung chưa gửi được khi khung đã nằm trên thiết bị 30 ngày. | Dữ liệu chỉ được giữ trong thời hạn có giới hạn. | unit | bắt buộc | ADR 0007, ADR 0014 |
| REQ-HRV-013 | Hệ thống phải gửi khung lên máy chủ dữ liệu bằng kết nối HTTPS do thiết bị mở, với TLS 1.3 và chứng chỉ thiết bị (REQ-AUTH-017), theo gói dữ liệu mô tả bằng JSON Schema trong `contracts/schemas/`; thiết bị không mở cổng nào nhận kết nối từ WAN. | Định dạng gói dữ liệu upload là hợp đồng công khai; việc gửi không cần cổng mở vào. | unit, integration | bắt buộc | ADR 0014, ADR 0016 |
| REQ-HRV-014 | Khi đường truyền đứt giữa lúc gửi, hệ thống phải gửi tiếp từ chỗ đã dừng ở lần sau, không gửi lại từ đầu. | Đường truyền từ trạm về máy chủ có thể đứt giữa chừng. | unit, integration | bắt buộc | ADR 0014 |
| REQ-HRV-015 | Hệ thống phải giới hạn băng thông gửi dữ liệu ở mức cấu hình. | Việc gửi không chiếm hết đường truyền của trạm. | integration | bắt buộc | ADR 0014 |
| REQ-HRV-016 | Hệ thống phải phát qua telemetry và API tình trạng thu dữ liệu: đồng ý đang bật hay tắt, cùng phạm vi, khoảng thời gian và người bật; số khung đã thu, đang chờ gửi và bị bỏ do làm mờ; kết quả lần gửi gần nhất; phiên bản model nhận dạng đang chạy; siêu dữ liệu của các khung gần nhất. | Người bảo trì thấy việc thu dữ liệu đang làm gì. | unit | bắt buộc | ADR 0006, ADR 0014 |
| REQ-HRV-017 | Hệ thống không được train, tinh chỉnh hay đổi phiên bản model nhận dạng trên thiết bị; phiên bản model chỉ đổi khi một model có chữ ký tới qua cơ chế cập nhật (REQ-OTA-013). | Model mới phải qua đánh giá trên tập test cố định trước khi chạy ở hiện trường. | unit, inspection | bắt buộc | ADR 0014, ADR 0015 |

### Tình trạng thiết bị

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-HRV-018 | Hệ thống phải để việc gửi tình trạng thiết bị về máy chủ ở trạng thái tắt theo mặc định; khi người có vai trò bảo trì bật, thiết bị chỉ gửi bản tóm tắt sức khoẻ, không kèm ảnh hay khung video, qua kết nối HTTPS do thiết bị mở với chứng chỉ thiết bị. | Mặc định không có dữ liệu tình trạng nào rời thiết bị; khi bật cũng không có ảnh người hay xe. | unit, integration | bắt buộc | ADR 0016 |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-HRV-019 | Khi đồng ý bị thu hồi, hệ thống phải xoá các khung chưa gửi đã thu theo đồng ý đó; khung thu theo một đồng ý hết hạn tự nhiên vẫn được gửi. | Thu hồi đồng ý có hiệu lực cả với dữ liệu đã thu mà chưa rời thiết bị. | unit | đề xuất | ADR 0014 |
| REQ-HRV-020 | Hệ thống phải ghi một dòng nhật ký kiểm toán cho mỗi lần thu hồi đồng ý, gồm người thu hồi, thời điểm và phạm vi. | Biết ai đã dừng việc thu dữ liệu và lúc nào. | unit | đề xuất | ADR 0014 |

## OTA: cập nhật

Máy chủ cập nhật và việc ký bản phát hành nằm ngoài các thành phần chạy trên thiết bị; ADR 0013 quy định phần đó, trong đó mỗi bản phát hành chạy trên một thiết bị trước rồi mới tới các thiết bị khác.

### Kênh, manifest và chữ ký

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-001 | Hệ thống phải tự kéo bản cập nhật từ máy chủ cập nhật của dự án bằng kết nối HTTPS do thiết bị mở, với TLS 1.3 và chứng chỉ thiết bị (REQ-AUTH-017); thiết bị không mở cổng nào nhận kết nối vào. | Không có cổng nào mở vào thiết bị từ WAN. | integration, inspection | bắt buộc | ADR 0013 |
| REQ-OTA-002 | Hệ thống phải mô tả release manifest bằng JSON Schema trong `contracts/schemas/`, gồm: phiên bản của bản phát hành; digest của image `core`, `hmi`, `perception`; phiên bản và checksum của model; phiên bản schema cấu hình; phiên bản hệ điều hành tối thiểu. | Manifest chỉ đúng từng thành phần của một bản phát hành. | unit, inspection | bắt buộc | ADR 0013 |
| REQ-OTA-003 | Hệ thống phải kiểm chữ ký cosign và schema của release manifest bằng khoá công khai giữ trên thiết bị, trước mọi bước khác của cập nhật; manifest sai chữ ký hay sai schema bị từ chối, thiết bị giữ nguyên bản đang chạy và ghi log lý do. | Thiết bị chỉ chạy bản phát hành có chữ ký hợp lệ. | unit, integration | bắt buộc | ADR 0013, ADR 0016 |
| REQ-OTA-004 | Hệ thống không được để khoá ký release hay khoá ký model trong repo hay trong secret của CI; `deploy/release/` chỉ chứa khoá công khai. | Chiếm được CI cũng không ký được bản mà thiết bị chấp nhận. | inspection | bắt buộc | ADR 0013, ADR 0016 |
| REQ-OTA-005 | Hệ thống phải tham chiếu mọi image trong release manifest và trong file Compose chạy trên thiết bị theo digest, không theo tag. | Mỗi tham chiếu chỉ đúng một image. | unit, inspection | bắt buộc | ADR 0013 |

### Cập nhật container

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-006 | Hệ thống phải tải manifest, kiểm chữ ký và kéo trước mọi image của bản mới bằng dịch vụ cập nhật, trước khi hỏi `core` có cho cập nhật không. | Máy chỉ ngừng làm việc trong lúc thay container. | integration | bắt buộc | ADR 0013 |
| REQ-OTA-007 | Khi dịch vụ cập nhật hỏi qua socket nội bộ, hệ thống phải cho phép cập nhật chỉ khi đủ cả bốn điều kiện: tay máy ở tư thế cất, FSM ở `SAFE_HOLD`, không có phiên sạc và cờ nghi đầu sạc trong cổng đang tắt, không còn lệnh chờ; thiếu điều kiện nào thì từ chối kèm mã riêng cho điều kiện đó; socket này không mở ra mạng. | Không bao giờ cập nhật khi tay máy đang chạy, đang sạc cho xe hay còn lệnh chờ. | unit, SIM | bắt buộc | ADR 0005, ADR 0013, REQ-MIS-023 |
| REQ-OTA-008 | Hệ thống không được áp một bản cập nhật khi chưa có xác nhận của người có vai trò bảo trì với lần xác thực lại còn hiệu lực (REQ-AUTH-011); lần xác nhận, kết quả cập nhật và mỗi lần quay lại bản trước đều ghi nhật ký kiểm toán. | Cập nhật là thao tác liên quan an toàn. | unit, integration | bắt buộc | ADR 0005, ADR 0013 |
| REQ-OTA-009 | Khi đã cho phép cập nhật, hệ thống phải vào chế độ cập nhật và từ chối mọi lệnh với mã riêng cho tới khi cập nhật xong hoặc đã quay lại bản trước. | Không lệnh nào chạy giữa lúc thay container. | unit, integration | bắt buộc | ADR 0013 |
| REQ-OTA-010 | Hệ thống phải sao lưu cấu hình (REQ-CFG-016) rồi mới khởi chạy lại các service bằng `docker compose up -d` với image theo digest của manifest mới. | Luôn có cấu hình để quay lại. | integration | bắt buộc | ADR 0013 |
| REQ-OTA-011 | Sau khi thay container, hệ thống phải kiểm mọi service healthy và self-test qua trong thời hạn cấu hình; không đạt thì tự quay lại release manifest của bản trước, giữ trong volume `ev-arm-state`, cùng cấu hình đã sao lưu. | Bản lỗi tự quay lại bản trước, không chờ người. | integration | bắt buộc | ADR 0007, ADR 0013, REQ-GW-023, REQ-CLI-008 |
| REQ-OTA-012 | Hệ thống không được cho service `core` truy cập Docker socket; chỉ dịch vụ cập nhật trên host làm việc với Docker. | Ai điều khiển được Docker daemon thì có quyền tương đương root trên host. | integration, inspection | bắt buộc | ADR 0013 |
| REQ-OTA-013 | Hệ thống phải kiểm SHA-256 và chữ ký của model học máy trước khi nạp; không khớp thì không nạp và model đang dùng tiếp tục chạy; volume `ev-arm-models` (`/var/lib/ev-arm/models`) giữ cả model đang dùng và bản trước để quay lại; mỗi lần đổi model ghi một dòng nhật ký kiểm toán. | Thiết bị chỉ nạp model nguyên vẹn, đúng nguồn, và luôn có bản trước để quay lại. | unit, integration | bắt buộc | ADR 0007, ADR 0013, ADR 0015 |

### Sau cập nhật

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-014 | Sau một bản cập nhật động tới phần mềm hay cấu hình liên quan an toàn, hệ thống phải ở lại `SAFE_HOLD` và không chạy tự động cho tới khi người có vai trò bảo trì xác nhận đã chạy xong checklist kiểm tra rút gọn tại chỗ. | Phần liên quan an toàn đã đổi phải được kỹ sư tại chỗ kiểm trước khi máy chạy tự động. | unit, SIM | bắt buộc | ADR 0005, ADR 0013 |

### Hệ điều hành

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-015 | Hệ thống phải cập nhật hệ điều hành theo hai phân vùng A/B bằng image có chữ ký do thiết bị chủ động kéo, tự quay lại phân vùng đã chạy trước đó khi hệ điều hành mới khởi động lỗi, dùng một khung OTA mã nguồn mở; cấu hình của phần này nằm ở `deploy/os/`. | Hệ điều hành lỗi sau cập nhật không làm thiết bị mất khả năng khởi động. | HIL | bắt buộc | ADR 0013 |

### Chế độ developer

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-016 | Hệ thống phải có chế độ developer: chủ thiết bị đăng ký được khoá ký của riêng mình; khi chế độ bật, thiết bị nhận release manifest ký bằng khoá đó; khi chế độ tắt, manifest ký bằng khoá đó bị từ chối. | Người nhận thiết bị tự cài được bản đã sửa mà thiết bị vẫn kiểm chữ ký. | unit, integration | bắt buộc | ADR 0011, ADR 0013, ADR 0016 |
| REQ-OTA-017 | Hệ thống phải coi việc bật, tắt chế độ developer và việc đăng ký khoá là thao tác liên quan an toàn (REQ-AUTH-011), và báo trạng thái của chế độ qua telemetry. | Khi chế độ bật, thiết bị chạy được bản không do Mr.Ròm ký. | unit, integration | bắt buộc | ADR 0005, ADR 0013, ADR 0016 |
| REQ-OTA-018 | Hệ thống phải có hướng dẫn dùng chế độ developer trong `docs/manual/`. | Chủ thiết bị cần biết cách tự cài bản đã sửa. | inspection | bắt buộc | ADR 0011, ADR 0013 |

### Phiên bản đang chạy

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-019 | Hệ thống phải báo qua API và telemetry phiên bản đang chạy (SemVer lấy từ tag Git lúc build), commit, phiên bản schema telemetry và phiên bản schema cấu hình; các giá trị này được ghi vào gói lúc build, không lấy bằng cách gọi Git lúc chạy, và giá trị không có thì báo `unknown`. | Trang Giới thiệu của HMI và người hỗ trợ cần biết đúng bản đang chạy. | unit | bắt buộc | ADR 0009, ADR 0011 |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-OTA-020 | Hệ thống phải từ chối cài bản phát hành có phiên bản hệ điều hành tối thiểu cao hơn hệ điều hành đang chạy, và báo cần cập nhật hệ điều hành trước. | Image mới có thể cần tính năng mà hệ điều hành đang chạy chưa có. | unit, integration | đề xuất | ADR 0013 |
| REQ-OTA-021 | Hệ thống phải đọc từ release manifest việc bản phát hành có động tới phần mềm hay cấu hình liên quan an toàn hay không (REQ-OTA-014). | Thiết bị cần biết khi nào phải ở lại `SAFE_HOLD` sau cập nhật. | unit | đề xuất | ADR 0013 |
| REQ-OTA-022 | Hệ thống phải kéo image qua máy chủ cập nhật của dự án bằng mTLS, để thiết bị không phải giữ token của registry. | Token trên từng thiết bị là bí mật phải cấp, giới hạn quyền và thu hồi riêng. | integration | đề xuất | ADR 0016 |

## CLI: dòng lệnh

Lệnh và cờ CLI là hợp đồng công khai theo mục "Thay đổi không tương thích" của [CONTRIBUTING.md](../../CONTRIBUTING.md).

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CLI-001 | Hệ thống phải có lệnh `serve` chạy `robot-core` (REST, kênh WSS và vòng giám sát) qua app factory, với địa chỉ và cổng nghe đặt bằng biến môi trường. | Một lệnh chạy hệ thống, cả trong container lẫn khi chạy thẳng trên máy. | integration | bắt buộc | ADR 0002 |
| REQ-CLI-002 | Hệ thống phải đặt tên mọi biến môi trường của mình với tiền tố `EV_ARM_`, và kê mọi biến đó trong `deploy/.env.example`. | Tiền tố theo định danh ứng dụng `ev-arm`; biến môi trường là hợp đồng công khai. | unit, inspection | bắt buộc | ADR 0007 |
| REQ-CLI-003 | Hệ thống phải chạy được cả hệ với adapter mô phỏng bằng lệnh `serve` cùng cấu hình chọn adapter mô phỏng, và bằng `deploy/compose.sim.yaml`. | Test SIM, demo và phát triển ở mức chạy 1, 2 không cần thiết bị. | integration, SIM | bắt buộc | ADR 0003, REQ-GW-021 |
| REQ-CLI-004 | Hệ thống phải có lệnh con của `calibrate` hiệu chuẩn nội tham số camera bằng bàn cờ, lấy ảnh từ camera hay từ thư mục ảnh, và lưu kết quả qua module calibration; kích thước bàn cờ, cỡ ô và số góc chụp tối thiểu mặc định lấy từ cùng cấu hình hiệu chuẩn mà module calibration dùng. | Hai nơi khai cỡ ô khác nhau làm sai tỉ lệ của mọi phép đo sau đó. | unit, HIL | bắt buộc | — |
| REQ-CLI-005 | Hệ thống phải có lệnh con của `calibrate` hiệu chuẩn hand-eye bằng bia ArUco chọn theo ID marker với ít nhất 10 tư thế, lấy FK từ hệ thống đang chạy qua API có đăng nhập (REQ-GW-019), rồi giải và lưu kết quả; lệnh dừng khi chưa có nội tham số đo được. | Hand-eye tính trên nội tham số chưa đo cho kết quả sai. | unit, HIL | bắt buộc | REQ-AUTH-006 |
| REQ-CLI-006 | Hệ thống phải có lệnh `admin create` tạo tài khoản có vai trò quản trị ngay trên thiết bị; mật khẩu được nhập qua dấu nhắc hay stdin, không qua đối số dòng lệnh. | Không có mật khẩu mặc định; đối số dòng lệnh lộ trong lịch sử shell và danh sách tiến trình. | unit, integration | bắt buộc | REQ-AUTH-003 |
| REQ-CLI-007 | Hệ thống phải có lệnh `provision` sinh ID và cặp khoá của thiết bị ngay trên thiết bị, tạo yêu cầu cấp chứng chỉ gửi CA của dự án, cài chứng chỉ được cấp, và đặt khoá riêng vào nơi giữ secret mà service `core` nhận qua `/run/secrets/`; khoá riêng không được in ra hay ghi ra chỗ nào khác. | Khoá thiết bị sinh tại chỗ và chỉ nằm ở nơi giữ secret. | integration | bắt buộc | ADR 0007, ADR 0016, REQ-AUTH-016 |
| REQ-CLI-008 | Hệ thống phải có lệnh `selftest` chạy bộ self-test của thiết bị, cũng là bộ mà bước kiểm sức khoẻ sau cập nhật dùng (REQ-OTA-011); lệnh in kết quả từng phép kiểm, thoát với mã khác 0 khi có phép kiểm trượt, và ghi rõ self-test không phải bằng chứng về chức năng an toàn. | Kỹ sư tại chỗ kiểm được thiết bị bất cứ lúc nào bằng đúng phép kiểm của quy trình cập nhật. | integration | bắt buộc | ADR 0005, ADR 0013 |

### Đề xuất

| ID | Yêu cầu | Lý do | Kiểm chứng | Trạng thái | Liên quan |
| --- | --- | --- | --- | --- | --- |
| REQ-CLI-009 | Hệ thống phải có lệnh `commission` dẫn kỹ sư qua lần nối đầu tiên với tay máy thật, mỗi bước chờ người xác nhận: kiểm nút dừng khẩn cấp, chế độ điều khiển từ xa của controller, đối chiếu số đọc, sức khoẻ kết nối, lệnh giữ yên tại chỗ, rồi một chuyển động nhỏ 1° ở một khớp cổ tay với hệ số tốc độ 0,10; có tuỳ chọn bỏ qua bước chuyển động. | Lần nối đầu tiên với tay máy thật cần từng bước có người xác nhận. | HIL | đề xuất | ADR 0004, ADR 0005 |

## Chuẩn dẫn chiếu

- [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.1.html): hợp đồng REST (REQ-GW-001).
- [AsyncAPI 3](https://www.asyncapi.com/docs/reference/specification/v3.0.0): hợp đồng của kênh WSS (REQ-GW-002).
- [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455): WebSocket (REQ-GW-002).
- [JSON Schema](https://json-schema.org/specification): payload, cấu hình trạm, release manifest, gói dữ liệu upload (REQ-GW-003, REQ-CFG-001, REQ-OTA-002, REQ-HRV-013).
- [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259): ngữ pháp số của JSON không có NaN hay vô cực (REQ-GW-004).
- [CloudEvents](https://github.com/cloudevents/spec): tên thuộc tính của envelope (REQ-GW-005).
- [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457): problem details (REQ-GW-011 tới REQ-GW-015).
- [IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033): chuẩn tham chiếu cho mạng của thiết bị, không có cổng mở vào từ WAN (REQ-GW-010, REQ-AUTH-019, REQ-OTA-001).
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html): thuộc tính cookie, định danh phiên, thông tin xác thực trên URL, thời hạn phiên (REQ-AUTH-004, REQ-AUTH-005, REQ-AUTH-022).
- [OWASP WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html): xác thực lúc bắt tay, kiểm `Origin` (REQ-AUTH-006, REQ-AUTH-020).
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html): `SameSite` là lớp phòng thủ thêm (REQ-AUTH-021).
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html): tham số tối thiểu của argon2id (REQ-AUTH-002).
- [RFC 9106](https://www.rfc-editor.org/rfc/rfc9106): argon2id (REQ-AUTH-002).
- [RFC 9846](https://www.rfc-editor.org/info/rfc9846): TLS 1.3 (REQ-AUTH-017, REQ-HRV-013, REQ-OTA-001).
- [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280): chứng chỉ X.509 của thiết bị (REQ-AUTH-016, REQ-AUTH-018).
- [MCAP](https://mcap.dev/spec): định dạng bản ghi, `log_time` và `publish_time` (REQ-REC-006).
- [Docker Compose, secret](https://docs.docker.com/compose/how-tos/use-secrets/): khoá thiết bị ở `/run/secrets/` (REQ-AUTH-016, REQ-CLI-007).
- [Docker, logging driver `local`](https://docs.docker.com/engine/logging/drivers/local/): giữ và xoay vòng log (REQ-REC-012).
- [Docker Engine security](https://docs.docker.com/engine/security/): quyền của người điều khiển Docker daemon (REQ-OTA-012).
- [cosign](https://github.com/sigstore/cosign): ký và kiểm release manifest (REQ-OTA-003).
- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): phiên bản đang chạy (REQ-OTA-019).
