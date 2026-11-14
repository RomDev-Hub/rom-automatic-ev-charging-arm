# 0016. Danh tính thiết bị, khoá ký và hỗ trợ từ xa

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Thiết bị gồm tay máy và máy host chạy Docker trên Jetson hoặc PC Linux, lắp ở trạm sạc hoặc ở nhà. Thiết bị tự kéo bản cập nhật từ máy chủ cập nhật của dự án (ADR 0013) và, khi có đồng ý, gửi dữ liệu train về máy chủ dữ liệu (ADR 0014). Hai máy chủ cần biết chắc mình đang làm việc với thiết bị nào; thiết bị cần biết chắc bản cập nhật và model nhận về do ai phát hành.

Thiết bị lắp ở nhà được tính là "User Product" theo mục 6 của AGPLv3. Khi bản cập nhật có chữ ký, người nhận thiết bị vẫn phải có cách tự cài bản đã sửa.

Vì không có cổng nào mở vào thiết bị từ WAN, hỗ trợ từ xa không thể đi vào qua một cổng mở sẵn. Gửi tình trạng thiết bị về máy chủ giúp theo dõi từ xa, nhưng camera của thiết bị nhìn thấy cả người và xe.

Cần quyết định: thiết bị chứng minh danh tính bằng gì; ai giữ khoá ký bản phát hành và khoá ký model; chủ thiết bị tự cài bản đã sửa bằng cách nào; hỗ trợ từ xa vào thiết bị bằng đường nào; thiết bị gửi tình trạng của mình về máy chủ tới mức nào.

## Yếu tố quyết định

- Không có cổng nào mở vào thiết bị từ WAN; mọi kết nối tới máy chủ do thiết bị chủ động mở. Mạng của thiết bị lấy [IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033) làm chuẩn tham chiếu.
- Máy chủ cập nhật và máy chủ dữ liệu xác thực từng thiết bị bằng chứng chỉ thiết bị qua mTLS, trên [TLS 1.3 (RFC 9846)](https://www.rfc-editor.org/info/rfc9846).
- Thiết bị chỉ cài bản cập nhật có release manifest ký hợp lệ và chỉ nạp model có chữ ký hợp lệ (ADR 0013, ADR 0015).
- Khoá ký không bao giờ nằm trong CI.
- Người nhận thiết bị tự cài được bản đã sửa ([AGPLv3](https://opensource.org/license/agpl-v3), mục 6).
- Việc bật đường vào thiết bị từ xa và việc cho thiết bị nhận bản không do Mr.Ròm ký đều có nhật ký kiểm toán.
- Gửi dữ liệu ra khỏi thiết bị mặc định tắt và chỉ gửi phần cần thiết, như với dữ liệu train (ADR 0014).

## Các phương án đã xét

- Danh tính thiết bị:
  - A1. Cặp khoá riêng sinh trên từng thiết bị, chứng chỉ do CA của dự án cấp
  - A2. Token truy cập chép vào từng thiết bị, ví dụ token GitHub để kéo image private từ GHCR
- Nơi giữ khoá ký release và khoá ký model:
  - B1. Mr.Ròm giữ offline
  - B2. Secret trong CI, CI tự ký sau khi build
- Cách chủ thiết bị cài bản đã sửa:
  - C1. Chế độ developer: chủ thiết bị đăng ký khoá ký của riêng mình
  - C2. Thiết bị chỉ nhận chữ ký của Mr.Ròm
- Hỗ trợ từ xa:
  - D1. Mặc định không có; khi cần, kỹ sư tại chỗ bật một đường hầm chiều ra có hạn giờ
  - D2. Một cổng vào từ WAN mở sẵn cho người hỗ trợ
- Gửi tình trạng thiết bị về máy chủ:
  - E1. Mặc định tắt; khi bật chỉ gửi tóm tắt sức khoẻ, không kèm ảnh
  - E2. Mặc định bật, gửi cả ảnh từ camera

## Kết quả quyết định

Phương án được chọn: A1, B1, C1, D1 và E1, vì chỉ các phương án này đáp ứng đủ các yếu tố quyết định; mỗi phương án còn lại vi phạm ít nhất một yếu tố.

- Danh tính thiết bị:
  - Mỗi thiết bị có một ID và một cặp khoá riêng. Cặp khoá sinh ngay trên thiết bị khi provisioning, bằng lệnh `provision` của CLI trong `robot-core/src/robot_core/cli/`.
  - Chứng chỉ thiết bị do CA của dự án cấp. Root CA giữ offline.
  - Có danh sách thu hồi chứng chỉ. Khoá thiết bị đổi hằng năm.
  - Thiết bị dùng chứng chỉ này khi kết nối mTLS tới máy chủ cập nhật và máy chủ dữ liệu.
  - Trong container, khoá thiết bị nằm ở `/run/secrets/`, đường dẫn mà [secret của Docker Compose](https://docs.docker.com/compose/how-tos/use-secrets/) dùng.
- Khoá ký:
  - Mr.Ròm giữ offline khoá ký release và khoá ký model. Các khoá này không bao giờ nằm trong CI.
  - Release manifest ký bằng khoá ký release, với công cụ [cosign](https://github.com/sigstore/cosign) dùng khoá riêng. Thiết bị giữ khoá công khai để kiểm chữ ký; khoá công khai này nằm trong repo ở `deploy/release/`.
  - Model đóng gói kèm SHA-256 và chữ ký bằng khoá ký model; thiết bị kiểm cả hai trước khi nạp (ADR 0015).
- Chế độ developer: chủ thiết bị đăng ký được khoá ký của riêng mình. Khi chế độ này bật, thiết bị nhận release manifest ký bằng khoá đó. Chế độ developer có nhật ký kiểm toán và được mô tả trong hướng dẫn sử dụng.
- Hỗ trợ từ xa:
  - Mặc định không có.
  - Khi cần, kỹ sư tại chỗ bật một đường hầm chiều ra, từ thiết bị tới máy chủ của dự án. Đường hầm có hạn giờ và được ghi nhật ký kiểm toán.
- Gửi tình trạng thiết bị về máy chủ: mặc định tắt. Khi bật, thiết bị chỉ gửi tóm tắt sức khoẻ, không kèm ảnh.

### Hệ quả

- Tích cực: khoá của một thiết bị bị lộ thì chỉ thiết bị đó bị ảnh hưởng; thu hồi chứng chỉ của nó không đụng tới thiết bị khác.
- Tích cực: khoá bí mật của thiết bị không phải đi qua kênh truyền nào khi provisioning, vì nó sinh ngay trên thiết bị.
- Tích cực: chiếm được CI cũng không ký được bản phát hành hay model mà thiết bị chấp nhận.
- Tích cực: khi không có người tại chỗ bật đường hầm thì không có đường nào vào thiết bị từ xa; đường hầm đã bật cũng tự hết hạn.
- Tiêu cực: dự án phải vận hành CA: giữ root offline, cấp chứng chỉ khi provisioning, phát hành danh sách thu hồi và đổi khoá thiết bị hằng năm.
- Tiêu cực: mỗi bản phát hành và mỗi model cần một bước ký do Mr.Ròm làm, ngoài CI.
- Tiêu cực: khi chế độ developer bật, thiết bị chạy được bản không do Mr.Ròm ký.
- Tiêu cực: hỗ trợ từ xa luôn cần một người có mặt tại thiết bị, và cần một máy chủ của dự án làm đầu kia của đường hầm.
- Tiêu cực: mặc định máy chủ không biết tình trạng thiết bị; khi bật cũng chỉ thấy bản tóm tắt.

### Xác nhận

- Không có khoá bí mật nào trong repo hay CI: hook `detect-private-key` và `gitleaks` chặn khi commit, CI chạy lại các hook này, và mỗi thay đổi ở workflow CI được review để chắc không có bước ký hay secret chứa khoá ký. `deploy/release/` chỉ chứa khoá công khai.
- Test của dịch vụ cập nhật (`deploy/host/updater/`): release manifest không có chữ ký hợp lệ bị từ chối; manifest ký bằng khoá do chủ thiết bị đăng ký chỉ được nhận khi chế độ developer bật, kèm dòng nhật ký kiểm toán.
- Kiểm trên thiết bị vừa cài: hỗ trợ từ xa và gửi tình trạng đều tắt, không có cổng nào mở vào từ WAN; đường hầm tự đóng khi hết hạn giờ và việc bật nó có dòng nhật ký kiểm toán; bản tóm tắt sức khoẻ không chứa ảnh.

## Ưu và nhược của từng phương án

### Danh tính thiết bị

- A1. Cặp khoá sinh trên thiết bị, chứng chỉ do CA của dự án cấp:
  - Ưu: khoá bí mật không phải đi qua kênh truyền nào; mỗi thiết bị thu hồi được riêng.
  - Ưu: dùng thẳng làm chứng chỉ client cho mTLS tới máy chủ của dự án.
  - Nhược: phải vận hành CA, danh sách thu hồi và việc đổi khoá hằng năm.
- A2. Token truy cập chép vào từng thiết bị:
  - Ưu: không phải vận hành CA.
  - Nhược: token sinh ở nơi khác rồi chép vào thiết bị; với token GitHub, loại token và phạm vi quyền còn phải kiểm.
  - Nhược: token không dùng làm chứng chỉ client cho mTLS được.

### Nơi giữ khoá ký

- B1. Mr.Ròm giữ offline:
  - Ưu: chiếm được CI cũng không ký được bản mà thiết bị chấp nhận.
  - Nhược: mỗi bản phát hành và mỗi model mới cần Mr.Ròm ký, ngoài CI.
- B2. Secret trong CI:
  - Ưu: ký tự động ngay sau khi build.
  - Nhược: ai chiếm được CI hoặc đọc được secret của nó thì ký được bản cài cho mọi thiết bị.

### Cài bản đã sửa

- C1. Chế độ developer:
  - Ưu: người nhận thiết bị tự cài được bản đã sửa mà thiết bị vẫn kiểm chữ ký, đúng với cách đọc AGPLv3 mục 6 nêu ở trên.
  - Nhược: thiết bị có thêm một đường để chạy bản không do Mr.Ròm ký; chế độ này cần nhật ký kiểm toán và phần hướng dẫn riêng.
- C2. Chỉ nhận chữ ký của Mr.Ròm:
  - Ưu: thiết bị chỉ chạy bản do Mr.Ròm ký.
  - Nhược: người nhận thiết bị không tự cài được bản đã sửa, trái với cách đọc AGPLv3 mục 6 nêu ở trên.

### Hỗ trợ từ xa

- D1. Đường hầm chiều ra do kỹ sư tại chỗ bật:
  - Ưu: không mở cổng vào nào; đường vào chỉ có khi người tại chỗ bật, tự hết hạn và có nhật ký kiểm toán.
  - Nhược: cần người có mặt tại thiết bị và một máy chủ của dự án làm đầu kia của đường hầm.
- D2. Cổng vào từ WAN mở sẵn:
  - Ưu: hỗ trợ được bất cứ lúc nào, không cần người tại chỗ.
  - Nhược: mở cổng vào từ WAN, trái với yếu tố quyết định đầu tiên.

### Gửi tình trạng thiết bị

- E1. Mặc định tắt, chỉ gửi tóm tắt, không kèm ảnh:
  - Ưu: mặc định không có dữ liệu tình trạng nào rời thiết bị; khi bật cũng không có ảnh người hay xe.
  - Nhược: chẩn đoán từ xa chỉ dựa vào bản tóm tắt, và chỉ khi tính năng được bật.
- E2. Mặc định bật, gửi cả ảnh:
  - Ưu: máy chủ thấy đầy đủ tình trạng, kể cả hình ảnh.
  - Nhược: ảnh có thể chứa mặt người và biển số rời thiết bị khi chưa có đồng ý, trái với cách xử lý dữ liệu ở ADR 0014.

## Thông tin thêm

- ADR liên quan: 0011 (giấy phép, thoả thuận đóng góp), 0013 (cập nhật OTA), 0014 (dữ liệu gửi về máy chủ và quyền riêng tư), 0015 (vòng đời model).
- Chuẩn tham chiếu cho chứng chỉ và danh sách thu hồi: [RFC 5280](https://www.rfc-editor.org/rfc/rfc5280).
- Phần còn ở trạng thái đề xuất: đường kéo image private. Nếu thiết bị kéo image thẳng từ GHCR thì mỗi thiết bị phải giữ token GitHub; hướng hiện tại là thiết bị kéo image qua máy chủ cập nhật của dự án bằng mTLS, nên không giữ token GitHub. Phần này đóng khi đã kiểm loại token và phạm vi quyền mà GHCR đòi cho image private, trước khi hiện thực cập nhật container (ADR 0013).
- Cách đọc AGPLv3 mục 6 ở trên (thiết bị lắp ở nhà là "User Product") cần người có chuyên môn pháp lý kiểm trước khi giao thiết bị.
- ADR này chưa quy định:
  - cách cấp ID thiết bị, thuật toán khoá và thời hạn chứng chỉ;
  - cách CA cấp chứng chỉ khi root giữ offline (có CA trung gian hay không), cách đổi khoá hằng năm, nơi và nhịp phát hành danh sách thu hồi;
  - nơi giữ khoá bí mật của thiết bị trên host;
  - cách sao lưu, thu hồi và thay khoá ký release, khoá ký model và khoá công khai trên thiết bị; công cụ và định dạng chữ ký model;
  - cách chủ thiết bị đăng ký khoá, bật và tắt chế độ developer, và vai trò được phép làm việc đó;
  - công nghệ đường hầm, thời hạn mặc định, vai trò được bật đường hầm và ai ở phía máy chủ được dùng nó;
  - nội dung, nhịp gửi và nơi nhận bản tóm tắt sức khoẻ, và ai được bật tính năng này.
