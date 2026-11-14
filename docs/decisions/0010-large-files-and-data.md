# 0010. File lớn và dữ liệu nằm ngoài Git

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Hệ thống chạy model học máy bằng ONNX Runtime, như model keypoint cổng sạc và model làm mờ mặt người, biển số. Model keypoint được train offline trên máy chủ train, từ dataset gồm các khung hình thiết bị gửi về khi có đồng ý. Khi chạy, thiết bị ghi bản ghi MCAP. Tay máy dùng URDF sinh từ gói mô tả chính hãng của UR, còn twin 3D cần mesh; mỗi thứ có giấy phép riêng. Phần lớn các file này lớn và là nhị phân; một phần mang ràng buộc về quyền riêng tư hoặc giấy phép.

Dataset, weights, bản ghi và các file lớn khác nằm ở đâu, và repo giữ gì để vẫn biết một lần train dùng dataset nào, một thiết bị chạy model nào, mỗi tài sản lấy từ đâu và theo giấy phép gì?

## Yếu tố quyết định

- Chỉ những người được chỉ định mới được truy cập khung hình thu từ thiết bị; dữ liệu này mặc định lưu 24 tháng và phải xoá được theo yêu cầu (theo thiết bị, trạm hoặc khoảng thời gian), kể cả bản đã gán nhãn (ADR 0014).
- Ai nhận thiết bị hoặc bản cài đều được truy cập repo ở đúng tag đang chạy (ADR 0011), nên thứ gì nằm trong Git cũng tới tay họ. Dữ liệu đã vào lịch sử Git thì không gỡ được khỏi bản clone của người khác ([GitHub Docs: Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)).
- Train dùng dataset có phiên bản cố định, mô tả bằng manifest kèm checksum (ADR 0015).
- Model đóng gói dạng ONNX kèm model card, SHA-256, chữ ký và phiên bản SemVer. Release manifest ghi phiên bản và checksum của model; thiết bị kiểm checksum và chữ ký trước khi nạp (ADR 0013, ADR 0015). Danh tính của model vì thế không dựa vào Git.
- Tài sản không phải code có giấy phép riêng; có tài sản chỉ được dùng cho mục đích phi thương mại (ADR 0011).
- Máy kiểm thay cho trí nhớ: hook pre-commit chạy ở mỗi commit, CI chạy lại các hook.

## Các phương án đã xét

- Manifest trong repo, dữ liệu và weights ngoài Git
- Weights phát hành trong Git LFS
- Dataset và weights trong Git

## Kết quả quyết định

Chọn phương án "Manifest trong repo, dữ liệu và weights ngoài Git", vì dataset phải nằm ở nơi giới hạn được người truy cập và xoá được theo yêu cầu, điều mà lịch sử Git không làm được; còn model đã được định danh bằng phiên bản, SHA-256 và chữ ký, nên đưa weights vào Git LFS chỉ thêm một nơi lưu và một công cụ phải cài mà không thêm bảo đảm nào.

- Dữ liệu của dataset (ảnh, nhãn) nằm trên máy chủ của dự án, ngoài phạm vi repo. Mỗi dataset có thư mục `datasets/<name>/` chỉ chứa manifest (phiên bản cố định, checksum) và datasheet theo [Datasheets for Datasets](https://arxiv.org/abs/1803.09010). `training/` tải dataset theo manifest.
- Weights của model nằm ngoài Git, trên máy chủ. Mỗi model có thư mục `models/<name>/` chỉ chứa manifest và model card ghi dữ liệu, chỉ số, giấy phép, theo [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993).
- Dữ liệu sinh ra khi chạy nằm trong volume trên thiết bị (ADR 0007): bản ghi MCAP ở `ev-arm-recordings`, model đang dùng và bản trước ở `ev-arm-models`.
- Không dùng Git LFS.
- Tài sản không phải code (dataset, model, URDF, mesh) được kê trong `third_party/assets.yaml`, mỗi tài sản ghi nguồn, giấy phép và cờ `nc`; tài sản chỉ được dùng cho mục đích phi thương mại có `nc: true`. Văn bản giấy phép của tài sản đã dùng nằm trong `third_party/licenses/`, ví dụ BSD-3 của URDF.
- Repo chặn bằng hai lớp:
  - `.gitignore` bỏ qua `*.mcap`, `*.onnx`, `*.pt`, `*.engine`;
  - hook `check-added-large-files` trong `.pre-commit-config.yaml` chặn file thêm mới lớn hơn 1 MiB (`--maxkb=1024`).

### Hệ quả

- Ưu: clone repo và chạy CI không phải tải dataset hay weights.
- Ưu: nguồn và giấy phép của mọi tài sản không phải code tra được ở một file, kể cả tài sản nằm ngoài Git.
- Nhược: manifest cũ có thể trỏ tới dữ liệu đã hết hạn lưu hoặc đã bị xoá theo yêu cầu; khi đó không train lại được đúng phiên bản cũ.
- Nhược: mỗi dataset, model hay tài sản mới phải kèm manifest, datasheet hoặc model card, và một mục trong `third_party/assets.yaml`.

### Xác nhận

- `.gitignore` giữ các file `*.mcap`, `*.onnx`, `*.pt`, `*.engine` chưa theo dõi khỏi `git status` và `git add .`; nó không áp cho file đã theo dõi và không chặn `git add -f` ([gitignore](https://git-scm.com/docs/gitignore), [git add](https://git-scm.com/docs/git-add)).
- Hook `check-added-large-files` chạy ở mỗi commit và chặn file đang được stage để thêm mới mà lớn hơn 1 MiB. Hook chỉ xét file thêm mới ([pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks#check-added-large-files)): file đã theo dõi lớn dần quá 1 MiB không bị chặn, và bước `pre-commit run --all-files` trên CI, chạy khi không có file nào đang stage, không kiểm lại kích thước.
- Không có kiểm tra tự động nào giới hạn nội dung của `datasets/<name>/` và `models/<name>/`: `scripts/check_layout.py` để hai thư mục này mở, còn ảnh hay file nhãn nhỏ hơn 1 MiB không khớp mẫu nào trong `.gitignore`. Phần này kiểm khi review: commit thêm dataset hoặc model chỉ chứa manifest cùng datasheet hoặc model card, và tài sản mới có mục trong `third_party/assets.yaml`.

## Ưu và nhược của từng phương án

### Manifest trong repo, dữ liệu và weights ngoài Git

- Ưu: đáp ứng yêu cầu giới hạn người truy cập và xoá theo yêu cầu, vì dataset chỉ nằm trên máy chủ.
- Ưu: khớp cách model tới thiết bị: model được nhận ra bằng phiên bản, SHA-256 và chữ ký trong manifest, không phụ thuộc nơi lưu file.
- Nhược: cần máy chủ của dự án còn giữ đúng phiên bản mà manifest ghi; checkout một commit không kèm dataset hay weights.

### Weights phát hành trong Git LFS

Dataset vẫn nằm trên máy chủ; riêng weights của các bản model phát hành được commit qua Git LFS. Git LFS thay file lớn bằng file con trỏ trong Git và lưu nội dung trên máy chủ LFS, ví dụ GitHub ([Git LFS](https://git-lfs.com/)).

- Ưu: checkout một commit là có weights của bản phát hành tương ứng.
- Nhược: weights nằm thêm ở một nơi ngoài máy chủ train, phải giữ khớp với phiên bản và checksum trong release manifest.
- Nhược: máy không cài Git LFS chỉ nhận file con trỏ.
- Nhược: dung lượng và băng thông Git LFS trên GitHub có hạn mức miễn phí, vượt thì tính tiền ([GitHub Docs: Git Large File Storage billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)).

### Dataset và weights trong Git

- Ưu: một nơi lưu duy nhất, không cần máy chủ hay công cụ thêm.
- Nhược: ai nhận thiết bị cũng được truy cập repo, nên không giới hạn được người xem dữ liệu.
- Nhược: dữ liệu đã commit nằm lại trong lịch sử; gỡ ra phải viết lại lịch sử và vẫn còn trong bản clone của người khác, nên không đáp ứng được yêu cầu xoá.
- Nhược: mỗi phiên bản dataset hay weights làm repo nặng thêm vĩnh viễn; mọi bản clone và CI tải hết.

## Thông tin thêm

- Quyết định liên quan: ADR 0002 (bố cục repo, gồm `datasets/`, `models/`, `third_party/`), ADR 0007 (dữ liệu runtime trong volume), ADR 0011 (giấy phép, tài sản phi thương mại), ADR 0013 (cập nhật OTA, release manifest), ADR 0014 (dữ liệu gửi về máy chủ), ADR 0015 (vòng đời model).
- Chưa có quyết định:
  - các trường của manifest dataset và manifest model ngoài phiên bản và checksum; chốt khi thêm dataset hoặc model đầu tiên;
  - schema của `third_party/assets.yaml` ngoài nguồn, giấy phép và `nc`, và việc dataset, model do dự án tự tạo có kê ở đó không; chốt khi thêm mục đầu tiên;
  - mesh của UR cho twin 3D: giấy phép chưa kiểm, nơi lưu chưa định, trong khi file lớn hơn 1 MiB không commit được; chốt trước khi đưa mesh vào dùng;
  - mẫu `.gitignore` cho ảnh và nhãn của dataset, và có cho hook kích thước xét mọi file (`--enforce-all`) để CI cũng kiểm hay không;
  - nơi đặt và cách sao lưu máy chủ giữ dataset và weights, vốn nằm ngoài repo.
