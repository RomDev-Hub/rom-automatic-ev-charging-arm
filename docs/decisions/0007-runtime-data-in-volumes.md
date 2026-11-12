# 0007. Dữ liệu runtime nằm trong volume

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Trên thiết bị (Jetson hoặc PC Linux), hệ thống chạy bằng Docker Compose với các service `core`, `hmi` và về sau `perception`. Khi cập nhật, image được thay theo digest; kiểm sức khoẻ sau cập nhật không đạt thì thiết bị quay lại bản trước.

Trong lúc chạy, hệ thống tạo và sửa nhiều loại dữ liệu: cấu hình trạm, calibration, tài khoản người dùng, model tay máy custom, hồ sơ tool, journal mất điện, bản sao lưu cấu hình, release manifest của bản trước, bản ghi MCAP, khung ảnh chờ gửi về máy chủ, model học máy, khoá thiết bị, token và log. Cần chọn chỗ đặt các dữ liệu này sao cho chúng còn nguyên qua mỗi lần thay container hay image, sao lưu và khôi phục được, không làm đầy đĩa, và bí mật không nằm trong image hay repo.

## Yếu tố quyết định

- Cập nhật và quay lại đều tạo container mới từ image khác; dữ liệu phải giữ được qua mỗi lần như vậy.
- Container phải chạy được với rootfs chỉ đọc và user không phải root.
- Mỗi loại dữ liệu có vòng đời riêng: bản ghi MCAP có giới hạn dung lượng; khung ảnh chờ gửi bị xoá sau khi gửi xong hoặc sau 30 ngày; model học máy và release manifest giữ bản trước để quay lại; cấu hình được sao lưu trước khi cập nhật.
- Dữ liệu của thiết bị sao lưu và khôi phục được.
- Bí mật (khoá thiết bị, token) không nằm trong image hay repo.
- Log không được làm đầy đĩa của thiết bị.
- Dùng chuẩn và cơ chế có sẵn, gồm Filesystem Hierarchy Standard (FHS) và volume, secret, logging driver của Docker, thay vì tự đặt quy ước.

## Các phương án đã xét

1. Volume có tên cho từng loại dữ liệu, kèm secret của Compose cho bí mật và stdout cho log.
2. Bind mount thư mục của host.
3. Lớp ghi được của container.

## Kết quả quyết định

Chọn phương án 1. Volume là cơ chế lưu dữ liệu bền mà tài liệu Docker ưu tiên: dữ liệu còn nguyên khi container bị thay, và khác bind mount, không phụ thuộc cây thư mục hay hệ điều hành của host. Ghi vào lớp ghi được của container thì trái với rootfs chỉ đọc và mất dữ liệu ở mỗi lần cập nhật.

Định danh ứng dụng là `ev-arm`, một lựa chọn của dự án vì không có chuẩn nào quy định. Định danh này dùng làm thư mục FHS `/var/lib/ev-arm/` trong container, tên project Compose `ev-arm`, tiền tố biến môi trường `EV_ARM_`, và tên image `ghcr.io/romdev-hub/ev-arm-core`, `ghcr.io/romdev-hub/ev-arm-hmi`, `ghcr.io/romdev-hub/ev-arm-perception`.

| Dữ liệu | Nơi đặt trong container | Nội dung |
| --- | --- | --- |
| volume `ev-arm-config` | `/var/lib/ev-arm/config` | cấu hình trạm, calibration, tài khoản người dùng, model tay máy custom, hồ sơ tool |
| volume `ev-arm-state` | `/var/lib/ev-arm/state` | journal mất điện; bản sao lưu cấu hình, mỗi bản một thư mục mang tên thời điểm dạng `20261111T084000Z/`; release manifest của bản trước để quay lại |
| volume `ev-arm-recordings` | `/var/lib/ev-arm/recordings` | bản ghi MCAP, có giới hạn dung lượng |
| volume `ev-arm-harvest` | `/var/lib/ev-arm/harvest` | khung ảnh đã làm mờ chờ gửi, xoá sau khi gửi xong hoặc sau 30 ngày |
| volume `ev-arm-models` | `/var/lib/ev-arm/models` | model học máy đang dùng và bản trước, kèm checksum và chữ ký |
| secret của Compose | `/run/secrets/` | khoá thiết bị, token |
| log | stdout | dạng JSON; Docker giữ bằng logging driver `local`, driver này tự xoay vòng |

Mọi container chạy với rootfs chỉ đọc và user không phải root. Dữ liệu runtime chỉ nằm ở các chỗ trong bảng, không nằm trong image hay repo. Image chỉ chứa phần mềm và dữ liệu mặc định đi kèm, như `robot-core/src/robot_core/defaults/`. Với cấu hình và biến môi trường, repo chỉ giữ file mẫu (`deploy/site/station.example.json`, `deploy/.env.example`).

User chạy service `core` là `ev-arm`, UID 10001, GID 10001, tạo trong `deploy/docker/core.Dockerfile`. UID và GID cố định vì volume đã có dữ liệu giữ chủ sở hữu cũ (mục Hệ quả), nên image về sau đổi UID sẽ không ghi được vào volume đó; số trên 10000 để không trùng tài khoản thường của host, mà Debian và Ubuntu cấp từ 1000 trở lên.

Chỗ ghi tạm duy nhất ngoài các volume là `/tmp` của từng service, một tmpfs có giới hạn dung lượng khai trong `deploy/compose.yaml` (64 MiB với `core`): nằm trong RAM và mất khi container khởi động lại, nên không giữ được dữ liệu runtime nào.

Mỗi thư mục trong bảng đặt lại được bằng biến môi trường `EV_ARM_<TÊN>_DIR`, ví dụ `EV_ARM_RECORDINGS_DIR` thay cho `/var/lib/ev-arm/recordings`; biến không đặt thì dùng đường dẫn trong bảng. Khi chạy thẳng trên máy, không qua container (mức 1 trong `CONTRIBUTING.md`), nơi `/var/lib/ev-arm/` không dùng được, người phát triển đặt các biến này; robot-core không tự dò thư mục theo XDG Base Directory, để container và máy phát triển dùng chung một cơ chế.

### Hệ quả

- Ưu: thay container khi cập nhật hay quay lại không làm mất dữ liệu.
- Ưu: mỗi loại dữ liệu một volume, nên sao lưu, khôi phục, đo dung lượng hay xoá từng loại được mà không đụng loại khác.
- Ưu: rootfs chỉ đọc biến mọi lần ghi ra chỗ không được cấp thành lỗi ngay lúc chạy, thay vì để dữ liệu âm thầm mất ở lần cập nhật sau.
- Ưu: bí mật không nằm trong image, repo hay biến môi trường, và mỗi service chỉ thấy secret được cấp cho nó.
- Nhược: Compose mặc định ghép tên project vào tên volume (`ev-arm_<tên khai báo>`), nên mỗi volume phải khai thuộc tính `name` để có đúng tên trong bảng.
- Nhược: Docker chỉ chép nội dung và quyền sở hữu của thư mục trong image sang volume khi volume còn rỗng. Vì vậy image phải tạo sẵn từng thư mục mount, thuộc user chạy service; volume đã có dữ liệu thì giữ chủ sở hữu cũ, kể cả khi image sau đổi UID.
- Nhược: tên volume và biến `EV_ARM_*` thuộc hợp đồng công khai theo mục "Thay đổi không tương thích" của [`CONTRIBUTING.md`](../../CONTRIBUTING.md); đổi chúng là thay đổi không tương thích.
- Nhược: dữ liệu nằm trong vùng do Docker quản lý trên host; muốn xem hay chép phải qua lệnh Docker hoặc một container tạm.

### Xác nhận

- Đã có trong repo: `.gitignore` chặn `.env`, `*.mcap`, `*.onnx`, `*.pt`, `*.engine` và `*.log`; hook pre-commit `check-added-large-files` (file quá 1 MiB), `detect-private-key` và `gitleaks` chặn file lớn, khoá riêng và bí mật trước khi commit; CI chạy lại các hook này.
- Review file Compose và Dockerfile: mỗi service có `read_only: true` và user không phải root; volume khai `name` đúng như bảng; bí mật cấp qua thuộc tính `secrets`; logging driver là `local`.
- Kiểm container đang chạy: `docker inspect` cho thấy `HostConfig.ReadonlyRootfs` là `true` và mount chỉ gồm các volume trong bảng cùng secret; tiến trình chạy bằng UID khác 0.
- Chạy cả stack bằng Docker Compose (mức 2 trong `CONTRIBUTING.md`) với cùng thiết lập: service nào còn ghi ra chỗ không được cấp thì lỗi ngay.

## Ưu và nhược của từng phương án

### Volume có tên cho từng loại dữ liệu

- Ưu: tài liệu Docker gọi volume là cơ chế được ưu tiên để lưu dữ liệu bền của container. Volume do Docker quản lý, không phụ thuộc cây thư mục và hệ điều hành của host, nên cùng một khai báo chạy được trên thiết bị Linux lẫn Docker Desktop của máy dev.
- Ưu: sao lưu và chuyển sang máy khác dễ hơn bind mount; quản lý được bằng lệnh và API của Docker.
- Ưu: volume mới nhận sẵn nội dung và quyền sở hữu của thư mục trong image, hợp với user không phải root.
- Ưu: FHS dành thư mục con của `/var/lib` cho dữ liệu trạng thái của từng ứng dụng. Cấu hình ở đây do chính hệ thống ghi (áp dụng, sao lưu, khôi phục), nên không thuộc `/etc`, nơi FHS dành cho file cấu hình tĩnh.
- Ưu: secret của Compose chỉ cấp cho service được khai và mount thành file; tài liệu Compose cảnh báo truyền mật khẩu và API key qua biến môi trường có nguy cơ lộ.
- Ưu: logging driver mặc định `json-file` không xoay vòng log; driver `local` xoay vòng ngay từ mặc định và được tài liệu Docker khuyên dùng.
- Nhược: phải khai `name` cho từng volume và tạo sẵn thư mục mount với đúng chủ sở hữu trong image.
- Nhược: không có đường dẫn cố định trên host để xem hay chép dữ liệu trực tiếp.

### Bind mount thư mục của host

- Ưu: dữ liệu nằm ở đường dẫn cố định trên host, xem và chép được bằng công cụ của host.
- Nhược: phụ thuộc cây thư mục và hệ điều hành của host, nên khác nhau giữa thiết bị Linux và Docker Desktop trên Windows.
- Nhược: host phải tạo sẵn thư mục với chủ sở hữu khớp UID của user trong container; nội dung có sẵn trong image không được chép sang.

### Lớp ghi được của container

- Ưu: không phải khai báo gì.
- Nhược: dữ liệu mất khi container bị xoá, mà cập nhật và quay lại đều tạo container mới.
- Nhược: trái với rootfs chỉ đọc.
- Nhược: tiến trình khác, kể cả việc sao lưu, khó lấy dữ liệu ra.

## Thông tin thêm

Nguồn:

- Filesystem Hierarchy Standard 3.0, các mục `/etc`, `/run`, `/var/lib`: <https://specifications.freedesktop.org/fhs/latest-single>
- XDG Base Directory Specification: <https://specifications.freedesktop.org/basedir/latest/>
- Docker, lưu trữ và volume: <https://docs.docker.com/engine/storage/>, <https://docs.docker.com/engine/storage/volumes/>
- Docker Compose, dùng secret: <https://docs.docker.com/compose/how-tos/use-secrets/>
- Docker, cấu hình logging driver và driver `local`: <https://docs.docker.com/engine/logging/configure/>, <https://docs.docker.com/engine/logging/drivers/local/>
- Đặc tả file Compose cho volume và service (`name`, `read_only`, `user`, `tmpfs`, `logging`, `secrets`): <https://docs.docker.com/reference/compose-file/volumes/>, <https://docs.docker.com/reference/compose-file/services/>

ADR liên quan: 0008 (môi trường dev và phiên bản công cụ), 0010 (file lớn và dữ liệu), 0013 (cập nhật OTA), 0014 (dữ liệu gửi về máy chủ và quyền riêng tư), 0015 (vòng đời model), 0016 (danh tính thiết bị, khoá ký, hỗ trợ từ xa).

Chưa quyết định, kèm việc sẽ chốt từng điểm:

- Con số giới hạn dung lượng của `ev-arm-recordings` và cách áp giới hạn: chốt khi nối bộ ghi MCAP vào vòng giám sát.
- Thông số xoay vòng log, và có đặt thêm `local` làm driver mặc định của daemon trong `deploy/host/daemon.json` hay không: chốt khi viết `deploy/compose.production.yaml`, file triển khai cho thiết bị. `deploy/compose.yaml` đã khai driver `local` cho từng service; khi chưa đặt thông số, driver dùng mặc định của Docker: 5 file, mỗi file 20 MB, có nén.
- UID và GID của user chạy service `hmi`: chốt khi viết `deploy/docker/hmi.Dockerfile`.
- Nơi giữ file nguồn của secret trên host, và cách lệnh `provision` của CLI đặt khoá thiết bị vào đó: chốt khi làm lệnh `provision`.
- Chỗ đặt dữ liệu runtime của service `hmi` (Caddy), như chứng chỉ và khoá TLS; bảng trên chưa có dòng nào cho phần này: chốt khi làm TLS cho HMI.
- Volume nào được sao lưu, lịch sao lưu và nơi giữ bản sao: chốt khi viết `scripts/volume-backup.sh` và `scripts/volume-restore.sh`.
