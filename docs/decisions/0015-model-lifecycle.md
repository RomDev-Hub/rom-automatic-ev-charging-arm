# 0015. Vòng đời model nhận dạng: train offline, kiểm trên tập test cố định, đóng gói có chữ ký

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Trong ADR này, "model" là model nhận dạng (ML) của module perception, không phải model tay máy ở ADR 0012.

Module perception (`robot-core/src/robot_core/perception/`) nhận dạng cổng sạc trên ảnh camera và tính tư thế của cổng. Phần nhận dạng dùng một model keypoint của cổng sạc do dự án tự train, vì model train sẵn trên bộ dữ liệu phổ thông như COCO không nhận ra cổng sạc. Dữ liệu train do module harvest (`robot-core/src/robot_core/harvest/`) thu trên thiết bị khi có đồng ý, được làm mờ ngay trên thiết bị rồi gán nhãn trên máy chủ (ADR 0014).

Model sẽ được train lại khi có thêm dữ liệu. Một bản mới có thể kém hơn bản đang chạy: nếu model đổi ngay ngoài hiện trường mà không được đo trên một tập test riêng thì không biết được điều đó; nếu không có phiên bản thì cũng không biết thiết bị đang chạy model nào, train từ dữ liệu nào.

Vấn đề: model được train, kiểm, đóng gói và đưa lên thiết bị theo quy trình nào để mỗi lần đổi model đều đo được, truy được nguồn gốc, kiểm được trên thiết bị và quay lại được?

## Yếu tố quyết định

- Mỗi model mới phải được đo trên một tập test riêng, không dùng để train, trước khi chạy ở hiện trường.
- Truy được nguồn gốc: model train từ dữ liệu nào, đạt chỉ số nào, theo giấy phép nào.
- Thiết bị chỉ nạp model nguyên vẹn và đúng nguồn.
- Model kém phải quay lại được, và lúc đầu chỉ ảnh hưởng một thiết bị.
- Ultralytics (AGPL-3.0) chỉ nằm trong môi trường train. Repo theo AGPL-3.0-or-later, và thoả thuận đóng góp ở `CONTRIBUTING.md` giữ cho Mr.Ròm quyền đổi giấy phép hay thương mại hoá về sau.
- Dữ liệu đã xoá theo yêu cầu không được dùng cho lần train sau (ADR 0014).
- Dữ liệu và weights nằm ngoài Git; repo chỉ giữ manifest (ADR 0010).
- ML không phải chức năng an toàn (ADR 0005), nhưng đổi model vẫn phải để lại dấu vết kiểm toán.

## Các phương án đã xét

- Train offline trên máy chủ train, kiểm trên tập test cố định, đóng gói có chữ ký, triển khai từng bước
- Học online ngay trong tiến trình trên thiết bị

## Kết quả quyết định

Phương án được chọn: "Train offline trên máy chủ train, kiểm trên tập test cố định, đóng gói có chữ ký, triển khai từng bước", vì đây là phương án duy nhất đo mỗi model trên một tập test riêng trước khi nó chạy ở hiện trường, đồng thời cho thiết bị kiểm model trước khi nạp và quay lại được bản trước.

- **Train:**
  - chỉ chạy trên máy chủ train;
  - component `training/` có `pyproject.toml` và lock riêng (`training/uv.lock`), và là chỗ duy nhất trong repo có Ultralytics; nó tải dataset theo manifest, train, xuất ONNX, đánh giá và viết model card;
  - đầu vào là dataset có phiên bản cố định: `datasets/<name>/` trong repo giữ manifest kèm checksum và datasheet, dữ liệu thật nằm trên máy chủ;
  - dataset và model của bên thứ ba dùng để train, kể cả checkpoint khởi đầu, được kê trong `third_party/assets.yaml` (nguồn, giấy phép, cờ `nc`) theo ADR 0011.
- **Tập test cố định:**
  - đóng băng và có phiên bản;
  - không bao giờ dùng để train;
  - chỉ đổi qua ADR.
- **Cổng chấp nhận:** chỉ số đo trên tập test cố định không được kém model đang chạy và phải đạt ngưỡng ghi trong ADR này. Model không qua cổng thì không được phát hành.
- **Ngưỡng của cổng chấp nhận** (Status: proposed): ADR này chưa ghi chỉ số nào được dùng và ngưỡng là bao nhiêu. Phần này đóng khi Mr.Ròm cập nhật ADR này với tên chỉ số, giá trị ngưỡng và phiên bản tập test cố định mà ngưỡng áp dụng, rồi chuyển phần này sang chấp nhận. Việc đó phải xong trước khi model đầu tiên được triển khai lên thiết bị, vì model đầu tiên không có model đang chạy để so, nên với nó cổng chỉ còn ngưỡng.
- **Đóng gói:** mỗi model phát hành gồm:
  - file ONNX;
  - model card ghi dữ liệu (dataset train và tập test, kèm phiên bản), chỉ số và giấy phép;
  - SHA-256 của file ONNX;
  - chữ ký bằng khoá ký model; khoá này do Mr.Ròm giữ offline (ADR 0016);
  - phiên bản SemVer của model.
- **Lưu trữ:** `models/<name>/` trong repo giữ manifest và model card. Weights (file ONNX, `.pt`) nằm trên máy chủ, ngoài Git, không dùng Git LFS; `.gitignore` chặn `*.onnx` và `*.pt` (ADR 0010).
- **Triển khai:**
  - model tới thiết bị qua cơ chế cập nhật ở ADR 0013: release manifest có chữ ký ghi phiên bản và checksum của model;
  - triển khai từng bước: chạy trên một thiết bị trước, rồi mới tới các thiết bị khác;
  - thiết bị kiểm checksum và chữ ký trước khi nạp; không khớp thì không nạp;
  - thiết bị giữ model trước để quay lại được: volume `ev-arm-models` (`/var/lib/ev-arm/models`) chứa model đang dùng và bản trước, kèm checksum và chữ ký (ADR 0007).
- **Chạy trên thiết bị:** module perception chạy model bằng ONNX Runtime (MIT); không image nào chạy trên thiết bị có Ultralytics.
- **Kiểm toán:** model không phải chức năng an toàn, nhưng mỗi lần đổi model đều ghi nhật ký kiểm toán.

### Hệ quả

- Tốt, vì mỗi model mới được đo trên cùng một tập test với model đang chạy, nên trước khi triển khai đã biết nó tốt hơn hay kém đi.
- Tốt, vì manifest và model card cho biết mỗi model train từ phiên bản dataset nào, đạt chỉ số nào, theo giấy phép nào; nhờ vậy cũng biết model nào đã train trên dữ liệu về sau bị xoá theo yêu cầu.
- Tốt, vì thiết bị chỉ nạp model nguyên vẹn, đúng nguồn, luôn có bản trước để quay lại, và một model kém lúc đầu chỉ ảnh hưởng một thiết bị.
- Tốt, vì phần chạy trên thiết bị không phụ thuộc thư viện train.
- Trung tính, vì model train bằng Ultralytics, kể cả fine-tune từ checkpoint của Ultralytics, thuộc AGPL-3.0 dù chạy bằng ONNX Runtime. Repo theo AGPL-3.0-or-later nên không vướng; muốn thương mại hoá thì phải có Enterprise License của Ultralytics, hoặc train từ đầu một model có giấy phép cho phép, không dùng mã hay checkpoint của Ultralytics.
- Trung tính, vì model đã train không gỡ được dữ liệu bị xoá về sau, nên chính sách dữ liệu phải ghi rõ điều này (ADR 0014); yêu cầu xoá chạm vào khung thuộc tập test cố định thì tập test phải đổi, tức là cần một ADR.
- Xấu, vì cần máy chủ train và cả chuỗi thu thập, gán nhãn, train, đánh giá, ký, triển khai; cải tiến tới thiết bị chậm hơn so với học ngay trên thiết bị.
- Xấu, vì model nào cũng phải ký bằng khoá Mr.Ròm giữ offline, nên thiếu Mr.Ròm thì không phát hành được model.
- Xấu, vì tập test chỉ đổi qua ADR nên thêm tình huống mới vào tập test chậm; mỗi lần đổi tập test, model đang chạy phải được đo lại trên tập mới thì mới so được.

### Xác nhận

- Cổng chấp nhận: model card của mỗi phiên bản ghi chỉ số đo trên tập test cố định kèm phiên bản tập test, chỉ số của model đang chạy trên cùng tập và ngưỡng; Mr.Ròm đối chiếu các số này trước khi ký.
- Repo: chỉ `training/pyproject.toml` và `training/uv.lock` được khai Ultralytics, kiểm khi review mỗi thay đổi dependency; `.gitignore` chặn `*.onnx` và `*.pt`, hook `check-added-large-files` chặn file trên 1 MiB, nên weights và dữ liệu không vào được Git.
- Thiết bị: test của phần nạp model cho thấy model sai checksum hoặc sai chữ ký bị từ chối, model đang dùng vẫn chạy, và volume `ev-arm-models` giữ cả bản trước.
- Triển khai: nhật ký kiểm toán có một dòng cho mỗi lần đổi model và cho thấy mỗi phiên bản chạy trên một thiết bị trước khi tới các thiết bị khác.

## Ưu và nhược của từng phương án

### Train offline trên máy chủ train, kiểm trên tập test cố định, đóng gói có chữ ký, triển khai từng bước

- Tốt, vì mọi model được đo trên cùng một tập test không dùng để train, trước khi tới thiết bị.
- Tốt, vì mỗi model có phiên bản, SHA-256, chữ ký và model card, nên truy được nguồn gốc và thiết bị kiểm được trước khi nạp.
- Tốt, vì có bản trước để quay lại và lúc đầu chỉ một thiết bị chạy model mới.
- Tốt, vì Ultralytics chỉ nằm ở máy chủ train; thiết bị chỉ cần ONNX Runtime.
- Xấu, vì cần máy chủ train, gán nhãn và bước ký bằng khoá offline, nên model mới tới thiết bị chậm hơn.

### Học online ngay trong tiến trình trên thiết bị

Model tự cập nhật ngay trên thiết bị từ dữ liệu vừa thu, trong lúc hệ thống đang chạy.

- Tốt, vì model học ngay từ dữ liệu tại chỗ, không cần máy chủ train hay bước phát hành.
- Xấu, vì không có đánh giá trên tập test riêng, nên không biết model sau mỗi lần học tốt hơn hay kém đi.
- Xấu, vì model đổi ngay ngoài hiện trường, không có phiên bản cố định để ký, kiểm checksum hay quay lại.
- Xấu, vì thư viện train phải chạy trên thiết bị, trái với yêu cầu chỉ để Ultralytics trong môi trường train.

## Thông tin thêm

- ADR liên quan: 0005 (phân bổ an toàn), 0007 (dữ liệu runtime nằm trong volume), 0010 (file lớn và dữ liệu), 0011 (giấy phép, thoả thuận đóng góp, tài sản NC), 0012 (tay máy đa năng), 0013 (cập nhật OTA), 0014 (dữ liệu gửi về máy chủ và quyền riêng tư), 0016 (danh tính thiết bị, khoá ký, hỗ trợ từ xa).
- Còn mở, ADR này chưa quyết:
  - chỉ số và ngưỡng của cổng chấp nhận (phần đề xuất ở trên);
  - tiêu chí để một phiên bản model đi từ thiết bị đầu tiên sang các thiết bị khác;
  - khi nào quay lại model trước: tự động theo dấu hiệu nào, hay do người vận hành quyết định;
  - quy tắc tăng MAJOR, MINOR, PATCH cho phiên bản model;
  - định dạng manifest của dataset, tập test và model; định dạng chữ ký model, công cụ ký, và nơi thiết bị giữ khoá công khai để kiểm chữ ký model;
  - chế độ developer của cơ chế cập nhật (ADR 0013) cho chủ thiết bị dùng khoá ký riêng cho release manifest; chưa quyết chữ ký model có nhận khoá đó hay không;
  - model làm mờ mặt và biển số (ADR 0014) sẽ chọn theo giấy phép và độ chính xác; chưa quyết nó có theo vòng đời này hay không.
- Việc weights train bằng Ultralytics thuộc AGPL-3.0 là cách đọc giấy phép, khớp với trang giấy phép của Ultralytics, và còn cần kiểm pháp lý.
- Xem lại ADR này khi tính tới thương mại hoá, vì khi đó weights train bằng Ultralytics cần Enterprise License hoặc phải thay bằng model có giấy phép cho phép.
- Nguồn:
  - MADR 4.0: <https://adr.github.io/madr/>
  - Model card: Mitchell và cộng sự, "Model Cards for Model Reporting", <https://arxiv.org/abs/1810.03993>
  - Datasheet cho dataset: Gebru và cộng sự, "Datasheets for Datasets", <https://arxiv.org/abs/1803.09010>
  - Semantic Versioning: <https://semver.org/>
  - ONNX: <https://onnx.ai/>
  - ONNX Runtime: <https://onnxruntime.ai/>
  - SHA-256 theo FIPS 180-4 (Secure Hash Standard): <https://csrc.nist.gov/pubs/fips/180-4/upd1/final>
  - Giấy phép của Ultralytics (AGPL-3.0, Enterprise License): <https://www.ultralytics.com/license>
  - AGPL-3.0: <https://opensource.org/license/agpl-v3>
