# 0002. Bố cục repo, ranh giới thành phần và thuật ngữ

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Repo chứa toàn bộ hệ thống tay máy sạc xe điện: lõi điều khiển viết bằng Python chạy trên thiết bị (Jetson hoặc PC Linux), giao diện vận hành viết bằng TypeScript, phần huấn luyện model chỉ chạy trên máy chủ train, cùng hợp đồng giao tiếp, cấu hình triển khai, tài liệu và manifest của dataset và model. Ba phần mã khác nhau về công cụ, dependency và nơi chạy, nhưng chung một phiên bản, một quy ước commit và một bộ kiểm tra.

Khung thư mục được dựng sẵn trước khi có mã. Cần chốt: thư mục nào được phép tồn tại và máy kiểm điều đó thế nào; mỗi thành phần nằm ở đâu và giới hạn tới đâu; các từ hệ thống, component, service, container, module mang nghĩa gì; tên thư mục, package và định danh ứng dụng đặt theo quy tắc nào.

## Yếu tố quyết định

- Mỗi phần mã cần thư mục riêng cho manifest, mã và test, vì công cụ khác nhau: `robot-core` và `training` dùng uv, `operator-ui` dùng pnpm.
- Ultralytics chỉ được nằm trong môi trường huấn luyện; thiết bị chạy model bằng ONNX Runtime.
- Scope của commit trỏ tới đường dẫn (bảng scope trong `CONTRIBUTING.md`), và `contracts/` cùng `robot-core/src/robot_core/ports/` là hợp đồng công khai, nên các đường dẫn này phải cố định.
- Bố cục phải do máy kiểm ở mỗi commit và trên CI, không dựa vào trí nhớ của người viết hay người review.
- Cấu trúc bên trong một package đổi theo mã; danh sách quá chặt buộc mỗi thay đổi mã phải sửa cả script lẫn ADR.
- Git không theo dõi thư mục rỗng.
- Theo chuẩn và tài liệu chính thức khi có (src layout của Python, test đặt ngoài mã ứng dụng, FHS cho đường dẫn trên thiết bị); chỗ chưa có chuẩn thì ghi rõ là lựa chọn của dự án.
- Các từ "component", "service", "container", "module" đều có nhiều nghĩa trong tài liệu kỹ thuật; repo cần một nghĩa cố định cho mỗi từ.

## Các phương án đã xét

- Khung dựng sẵn, thư mục cố định và thư mục mở do script kiểm
- Tạo thư mục khi cần, bố cục chỉ ghi trong tài liệu
- Khung dựng sẵn, script kiểm mọi thư mục ở mọi cấp

## Kết quả quyết định

Chọn phương án "Khung dựng sẵn, thư mục cố định và thư mục mở do script kiểm", vì đây là phương án duy nhất vừa để máy giữ bố cục ở mỗi commit, vừa để cấu trúc bên trong mỗi package đổi theo mã mà không phải sửa script hay ADR.

Thuật ngữ dùng trong repo:

- Hệ thống: toàn bộ sản phẩm.
- Component (thành phần): `robot-core`, `operator-ui`, `training`.
- Service: `core`, `hmi`, `perception` trong Docker Compose. Service `hmi` phục vụ bản build của `operator-ui`. `perception` hiện là một module của `robot-core`, sau này tách thành service.
- Container: một bản đang chạy của một service.
- Module/package: thư mục mã bên trong `robot-core/src/robot_core/`, ví dụ `mission/`, `motion/`.
- "Container" trong [mô hình C4](https://c4model.com/) khác với Docker container; tài liệu kiến trúc luôn ghi rõ "C4 container".
- Thuật ngữ robot theo [ISO 8373](https://committee.iso.org/standard/75539.html); mỗi mục có tiếng Việt và tiếng Anh.
- `docs/glossary.md` ghi các thuật ngữ trên cùng thuật ngữ robot.

Thành phần và ranh giới:

- `robot-core` là lõi chạy trên thiết bị: package Python `robot_core` với `pyproject.toml`, `uv.lock` và `.python-version` riêng, đóng thành image `ev-arm-core` chỉ dùng CPU và chạy thành service `core`. Bên trong, module chia theo miền; `ports/` khai giao diện tới thiết bị, `adapters/` hiện thực các giao diện đó cho từng thiết bị và cho mô phỏng, theo mô hình [ports and adapters](https://alistair.cockburn.us/hexagonal-architecture/).
- `operator-ui` là giao diện vận hành viết bằng TypeScript, một package của workspace pnpm, dùng chung `pnpm-lock.yaml` ở gốc repo. Bản build là file tĩnh do service `hmi` phục vụ. `operator-ui` giao tiếp với `robot-core` qua REST cho lệnh và một kênh WSS cho sự kiện, mô tả trong `contracts/` bằng OpenAPI 3.1 và AsyncAPI 3; `contracts/openapi.json` sinh từ `robot-core`, client của `operator-ui` sinh từ `contracts/`.
- `training` chỉ chạy trên máy chủ train, có `pyproject.toml` và `uv.lock` riêng, và là nơi duy nhất có Ultralytics. Đầu ra là model ONNX kèm model card, SHA-256 và chữ ký; manifest của model nằm ở `models/<tên>/`, weights nằm ngoài Git; thiết bị chạy model bằng ONNX Runtime.
- `perception` hiện là module `robot-core/src/robot_core/perception/`. Khi tách thành service, nó dùng GPU, với image `ev-arm-perception` build từ `deploy/docker/perception.Dockerfile`.
- Thư mục dùng chung, không thuộc thành phần nào: `contracts/` (hợp đồng giao tiếp), `deploy/` (Compose, Dockerfile, cấu hình host và trạm), `datasets/` và `models/` (manifest), `third_party/` (tài sản không phải code và giấy phép của chúng), `docs/`, `scripts/`, `.github/`, `.devcontainer/`.
- Mã Python của `robot-core` và `training` dùng src layout, mô tả trong [Python Packaging User Guide](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/); test của lõi nằm ở `robot-core/tests/`, ngoài package, theo cách bố trí "tests outside application code" của [pytest](https://docs.pytest.org/en/stable/explanation/goodpractices.html). Test của `operator-ui` đặt cạnh mã, dạng `*.test.tsx`.

Danh sách thư mục cho phép, đúng như `scripts/check_layout.py` kiểm:

- Script xét mọi thư mục cha của các file mà Git đang theo dõi và các file chưa theo dõi mà [quy tắc ignore của Git](https://git-scm.com/docs/gitignore) không bỏ qua (`.gitignore`, `.git/info/exclude`, file ignore toàn cục). Đường dẫn bị bỏ qua, ví dụ `node_modules/` hay `.venv/`, không bị kiểm.
- Thư mục cố định (tập `FIXED` trong script) được phép đúng với tên đó; bên trong nó chỉ được có thư mục con cũng có tên trong bảng dưới đây.
- Thư mục mở (tập `OPEN`) được phép cùng mọi thư mục con ở mọi độ sâu; cấu trúc bên trong do mã hay nội dung nó chứa quyết định.
- Mọi thư mục khác bị chặn, kể cả ở gốc repo.
- Script chỉ kiểm thư mục, không kiểm tên file.
- Thư mục còn rỗng giữ bằng `.gitkeep`. Khi thêm file thật đầu tiên vào thư mục thì xoá `.gitkeep` trong cùng commit; thư mục có `.gitkeep` cùng bất kỳ file hay thư mục con nào khác bị chặn.
- Muốn có thư mục mà script chưa cho phép thì sửa `FIXED` hoặc `OPEN` trong `scripts/check_layout.py` và bảng dưới đây trong cùng một commit. Thư mục con bên trong thư mục mở không cần sửa gì.

| Thư mục | Loại | Chứa |
| --- | --- | --- |
| `.devcontainer` | cố định | `devcontainer.json`: dev container Linux, tuỳ chọn |
| `.github` | cố định | `dependabot.yml` |
| `.github/workflows` | cố định | `ci.yaml` (kiểm tra), `release.yaml` (phát hành: tag, GitHub Release, image amd64 và arm64 kèm SBOM, provenance) |
| `contracts` | cố định | `openapi.json` sinh từ `robot-core`; `asyncapi.yaml` cho kênh WSS: telemetry, sự kiện, vòng đời lệnh |
| `contracts/schemas` | mở | JSON Schema: payload, cấu hình, release manifest, gói dữ liệu upload |
| `robot-core` | cố định | `pyproject.toml`, `uv.lock`, `.python-version` |
| `robot-core/src` | cố định | gốc của src layout |
| `robot-core/src/robot_core` | cố định | package `robot_core`, có `py.typed` |
| `robot-core/src/robot_core/gateway` | mở | app factory, REST, WSS, session, vai trò, kiểm toán |
| `robot-core/src/robot_core/mission` | mở | danh mục trạng thái, guard, dispatcher |
| `robot-core/src/robot_core/motion` | mở | director, kiểm segment, giám sát tiến trình |
| `robot-core/src/robot_core/arm` | mở | model tay máy và tool, FK, Jacobian, IK DLS, tính bằng Pinocchio |
| `robot-core/src/robot_core/perception` | mở | PnP, cổng bất định, fusion, detector; chạy model bằng ONNX Runtime |
| `robot-core/src/robot_core/calibration` | mở | hiệu chuẩn |
| `robot-core/src/robot_core/ports` | mở | giao diện tới thiết bị: ArmPort (segment), Rail, Io, Force, Presence, Evse, Perception |
| `robot-core/src/robot_core/adapters` | mở | hiện thực các port: `sim/`, `ur_rtde/`, `modbus/`, `realsense/`, `evse/` |
| `robot-core/src/robot_core/config` | mở | model có kiểu, schema, áp dụng nguyên tử, chuyển đổi phiên bản |
| `robot-core/src/robot_core/recording` | mở | MCAP, journal mất điện |
| `robot-core/src/robot_core/harvest` | mở | đồng ý, làm mờ, chọn khung, hàng đợi upload |
| `robot-core/src/robot_core/ota` | mở | điều kiện cập nhật, báo phiên bản đang chạy |
| `robot-core/src/robot_core/defaults` | mở | `arms/` (mỗi model tay máy một thư mục có `model.urdf` và `spec.yaml`), `tools/` (hồ sơ tool), `vehicles/` (danh mục xe và vị trí cổng sạc) |
| `robot-core/src/robot_core/locales` | mở | `vi.json`, `en.json` |
| `robot-core/src/robot_core/cli` | mở | lệnh `serve`, `calibrate`, `commission`, `selftest`, `admin`, `provision` |
| `robot-core/tests` | cố định | `conftest.py` |
| `robot-core/tests/unit` | mở | unit test, chạy mỗi lần push |
| `robot-core/tests/integration` | mở | test integration, chạy mỗi lần push |
| `robot-core/tests/sim` | mở | test mô phỏng, chạy mỗi lần push; `golden/` giữ trace tham chiếu |
| `robot-core/tests/hil` | mở | test hardware-in-the-loop có marker `hil`, chạy tay trên runner tự host |
| `operator-ui` | cố định | `package.json`, `index.html`, `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`, `eslint.config.js`, `.prettierrc.json` |
| `operator-ui/src` | cố định | mã TypeScript; client sinh từ `contracts/`; test `*.test.tsx` đặt cạnh mã |
| `operator-ui/src/app` | mở | khung ứng dụng |
| `operator-ui/src/features` | mở | mã theo từng tính năng |
| `operator-ui/src/shared` | mở | mã dùng chung |
| `training` | cố định | `pyproject.toml`, `uv.lock` |
| `training/src` | cố định | gốc của src layout |
| `training/src/training` | mở | tải dataset theo manifest, train, xuất ONNX, đánh giá, model card |
| `training/configs` | mở | cấu hình huấn luyện |
| `deploy` | cố định | `compose.yaml`, `compose.sim.yaml`, `compose.dev.yaml`, `compose.production.yaml`, `compose.gpu.yaml`, `.env.example` |
| `deploy/docker` | mở | `core.Dockerfile` (target runtime chỉ dùng CPU, đa kiến trúc, và target dev), `hmi.Dockerfile` (build bằng pnpm ra file tĩnh, phục vụ qua Caddy), `perception.Dockerfile` (GPU, làm sau) |
| `deploy/release` | mở | khoá công khai để kiểm chữ ký release |
| `deploy/host` | mở | `daemon.json`, udev, chrony, watchdog, firewall; `updater/` là dịch vụ cập nhật chạy trên host |
| `deploy/os` | mở | cấu hình OTA hệ điều hành, viết sau khi chọn khung OTA |
| `deploy/site` | mở | `station.example.json` |
| `datasets` | mở | mỗi dataset một thư mục `<tên>/` gồm manifest và datasheet; dữ liệu thật nằm trên máy chủ |
| `models` | mở | mỗi model một thư mục `<tên>/` gồm manifest và model card; weights nằm ngoài Git |
| `third_party` | cố định | `assets.yaml`: kê tài sản không phải code với nguồn, giấy phép, cờ `nc` |
| `third_party/licenses` | mở | văn bản giấy phép của tài sản đã dùng |
| `docs` | cố định | `README.md`, `glossary.md` |
| `docs/decisions` | mở | ADR, tên file `NNNN-title.md` |
| `docs/requirements` | mở | requirement có ID |
| `docs/safety` | mở | tài liệu an toàn |
| `docs/architecture` | mở | tài liệu kiến trúc |
| `docs/verification` | mở | tài liệu kiểm chứng |
| `docs/manual` | mở | hướng dẫn sử dụng |
| `scripts` | cố định | `bootstrap`, `check_layout.py`, `volume-backup.sh`, `volume-restore.sh` |

File ở gốc repo: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.gitignore`, `.gitattributes`, `.editorconfig`, `.dockerignore`, `.pre-commit-config.yaml`, `commitlint.config.mjs`, `.markdownlint.yaml`, `cliff.toml`, cùng `package.json`, `pnpm-workspace.yaml` và `pnpm-lock.yaml` của workspace pnpm. Script không kiểm danh sách này.

Đặt tên:

- Thư mục thành phần đặt tên theo sản phẩm, viết kebab-case: `robot-core`, `operator-ui`, `training`.
- Tên package Python là định danh nên không có gạch ngang: package của `robot-core` là `robot_core`, của `training` là `training`.
- File TypeScript trong `operator-ui`: `PascalCase.tsx` cho component React, `camelCase.ts` cho phần còn lại. Tên component React bắt đầu bằng chữ hoa, theo [tài liệu của React](https://react.dev/learn/your-first-component).
- ADR trong `docs/decisions/` đặt tên `NNNN-title.md`.
- Định danh ứng dụng là `ev-arm`. Nó là tên thư mục của ứng dụng dưới `/var/lib` theo [FHS](https://specifications.freedesktop.org/fhs/latest-single) (`/var/lib/ev-arm/`), tên project Compose, tiền tố biến môi trường `EV_ARM_`, và gốc tên image: `ghcr.io/romdev-hub/ev-arm-core`, `ghcr.io/romdev-hub/ev-arm-hmi`, `ghcr.io/romdev-hub/ev-arm-perception`.
- Tên thư mục thành phần, cách chia module theo miền, quy tắc tên file TypeScript và định danh `ev-arm` là lựa chọn của dự án ở chỗ chưa có chuẩn chung; giữ thư mục rỗng bằng `.gitkeep` là quy ước cộng đồng.

### Hệ quả

- Tốt, vì nhìn bảng là biết mã, test, hợp đồng, cấu hình triển khai và tài liệu của từng phần nằm ở đâu, và các scope trong `CONTRIBUTING.md` trỏ tới đường dẫn có sẵn.
- Tốt, vì Ultralytics và các dependency huấn luyện nằm riêng trong `training/`, không vào image chạy trên thiết bị.
- Tốt, vì một tag ứng với toàn bộ mã của một bản cài: lõi, giao diện, hợp đồng và cấu hình triển khai cùng một phiên bản.
- Xấu, vì thêm thư mục ở chỗ cố định cần một commit sửa cả script lẫn ADR này.
- Xấu, vì nhìn cây thư mục không biết phần nào đã có mã: thư mục chỉ có `.gitkeep` là chỗ giữ sẵn.

### Xác nhận

- `scripts/check_layout.py` chạy ở hook `check-layout` của pre-commit trong mỗi commit (`.pre-commit-config.yaml`, `always_run: true`) và trên CI ở bước `Pre-commit hooks on all files`. Gặp vi phạm, script in mỗi lỗi một dòng rồi thoát với mã 1: `directory not in the agreed layout: <thư mục>/` hoặc `remove .gitkeep: <thư mục>/ already has content`.
- Chạy tay ở gốc repo: `python scripts/check_layout.py`; không in gì và thoát với mã 0 là đạt.
- Script không kiểm tên file và không kiểm thư mục trong bảng còn tồn tại hay không.

## Ưu và nhược của từng phương án

- Khung dựng sẵn, thư mục cố định và thư mục mở do script kiểm
  - Tốt, vì thư mục lạ và `.gitkeep` sót bị chặn ở mỗi commit và trên CI.
  - Tốt, vì đường dẫn trong bảng scope và các hợp đồng công khai có chỗ cố định ngay từ đầu.
  - Tốt, vì bên trong thư mục mở, mã tự tổ chức mà không phải sửa script hay ADR.
  - Xấu, vì script chỉ kiểm thư mục, nên file đặt sai chỗ trong một thư mục được phép vẫn lọt.
  - Xấu, vì thêm thư mục ở chỗ cố định phải sửa script và ADR này trong cùng một commit.
  - Xấu, vì nhiều thư mục chỉ giữ chỗ bằng `.gitkeep` cho tới khi có nội dung.
- Tạo thư mục khi cần, bố cục chỉ ghi trong tài liệu
  - Tốt, vì repo không có thư mục giữ chỗ và không có script phải duy trì.
  - Xấu, vì bố cục chỉ được giữ bằng trí nhớ của người viết và người review; thư mục lạ vào repo mà không bị chặn.
  - Xấu, vì scope trong `CONTRIBUTING.md` có thể trỏ tới đường dẫn chưa có, hoặc mã nằm ở chỗ khác với bảng scope.
- Khung dựng sẵn, script kiểm mọi thư mục ở mọi cấp
  - Tốt, vì không thư mục nào vào repo mà không có tên trong ADR.
  - Xấu, vì mỗi thư mục con mới trong mã, ví dụ bên trong `gateway/`, đều phải sửa script và ADR, nên ADR đổi theo từng thay đổi mã.

## Thông tin thêm

Các quyết định gần với ADR này được ghi riêng:

- ADR 0003: kiến trúc bên trong `robot-core` theo ports and adapters.
- ADR 0006: hợp đồng giữa `operator-ui` và `robot-core` trong `contracts/`.
- ADR 0007: dữ liệu lúc chạy nằm trong volume, dưới `/var/lib/ev-arm/`.
- ADR 0010: file lớn và dữ liệu, gồm nội dung của `datasets/` và `models/`.
- ADR 0011: giấy phép và tài sản không phải code trong `third_party/`.
- ADR 0012: tay máy đa năng, gồm `robot-core/src/robot_core/defaults/arms/` và `robot-core/src/robot_core/defaults/tools/`.
- ADR 0013: cập nhật OTA, gồm `deploy/release/`, `deploy/host/updater/` và `deploy/os/`.
- ADR 0015: vòng đời model, từ `training/` tới thiết bị.

Chưa quyết định:

- Thêm hay bỏ một file ở gốc repo có cần sửa ADR này không; script không kiểm tên file.
- Thời điểm tách `perception` thành service, và khi tách thì mã có ở lại `robot-core/src/robot_core/perception/` hay không.
- Cách kiểm bảng thư mục trong ADR này khớp với `FIXED` và `OPEN` của script, cũng như cách kiểm ranh giới thành phần và cách dùng thuật ngữ; hiện chưa có bước tự động nào.
