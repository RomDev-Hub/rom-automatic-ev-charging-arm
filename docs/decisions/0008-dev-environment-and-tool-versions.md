# 0008. Môi trường dev ba mức và phiên bản công cụ

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Repo gồm mã Python (`robot-core`, `training`), HMI viết bằng TypeScript (`operator-ui`) và image Docker cho cả amd64 lẫn arm64 (Jetson). Người phát triển dùng Windows, macOS hoặc Linux; máy phát triển chính chạy Windows. Cần chốt: trình quản lý gói JavaScript nào và cài nó ra sao; ghim phiên bản Node thế nào mà không đụng tới dự án khác trên cùng máy; Python bản nào và quản lý môi trường Python bằng công cụ gì; khi phát triển thì mã chạy ở đâu; CI kiểm trên những hệ điều hành nào.

Phần lớn câu trả lời phụ thuộc vào hai thư viện: [ur_rtde](https://gitlab.com/sdurobotics/ur_rtde), thư viện giao tiếp RTDE với controller UR mà chỉ adapter UR dùng, và [Pinocchio](https://github.com/stack-of-tasks/pinocchio), thư viện động học có tên gói `pin` trên PyPI. Dữ kiện đã kiểm ngày 2026-11-11 và 2026-11-12:

- ur_rtde 1.6.5 chỉ có wheel cho CPython 3.7–3.12, trên Linux x86_64, Linux i686 và Windows; không có wheel arm64, nên trên arm64 luôn phải build từ source ([PyPI](https://pypi.org/project/ur-rtde/)).
- `pin` 4.1.0 có wheel cho Python 3.10–3.14 trên Linux x86_64, Linux aarch64 và macOS; không có wheel Windows ([PyPI](https://pypi.org/project/pin/)).
- conda-forge có Pinocchio 4.1.0 cho win-64, linux-64, linux-aarch64 và osx, với Python 3.10–3.14, nhưng không có gói ur_rtde ([conda-forge](https://prefix.dev/channels/conda-forge/packages/pinocchio)).
- numpy 2.5 và scipy 1.18 cần Python 3.12 trở lên ([numpy](https://pypi.org/project/numpy/), [scipy](https://pypi.org/project/scipy/)); onnxruntime 1.31.1 có wheel cho Python 3.11–3.14 trên Windows, Linux x86_64, Linux aarch64 và macOS ([onnxruntime](https://pypi.org/project/onnxruntime/)).
- Python 3.12 chỉ còn nhận bản vá bảo mật, tới 2028-10; Python 3.14 còn nhận bản vá lỗi tới 2027-10 ([Python Developer's Guide](https://devguide.python.org/versions/), [endoflife.date](https://endoflife.date/python)).
- Node 26 là bản LTS ([Node.js](https://nodejs.org/en/about/previous-releases)). Corepack còn ở mức thử nghiệm trong Node 24 và không còn đi kèm Node từ bản 25 ([Corepack](https://nodejs.org/docs/latest-v24.x/api/corepack.html)).
- Với repo public, GitHub không tính phút cho runner chuẩn, kể cả runner Linux arm64 và runner Windows ([GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions)).

## Yếu tố quyết định

- Image `core` chạy trên cả amd64 và arm64, nên bản Python được chọn phải dùng được với mọi thư viện trên cả hai kiến trúc.
- Bản Python còn được vá lỗi càng lâu càng tốt.
- Phiên bản Node và pnpm khai ở một chỗ trong repo; Node có sẵn trên máy giữ nguyên để dự án khác vẫn dùng bản của chúng.
- Cài gói JavaScript an toàn ngay từ mặc định, không dựa vào việc nhớ bật tuỳ chọn.
- Phần lớn việc Python không cần Linux; mỗi người kiểm tới mức máy của mình cho phép.
- Không chạy job CI khi thay đổi không cần tới nó, để CI trả kết quả sớm và không dùng runner vô ích.
- Cấu hình Git của repo này không làm đổi hành vi của repo khác trên cùng máy.

## Các phương án đã xét

- Trình quản lý gói JavaScript:
  - pnpm
  - npm
- Cách cài pnpm:
  - `npm install -g pnpm@<bản chính xác>`
  - Corepack
- Nguồn Node cho dự án:
  - pnpm tự tải Node theo `devEngines.runtime`
  - trình quản lý phiên bản Node đọc `.nvmrc`, ví dụ fnm
- Phiên bản Python:
  - 3.14
  - 3.12
- Công cụ quản lý môi trường Python:
  - uv
  - pixi cộng conda-forge
- Nơi chạy mã khi phát triển:
  - ba mức: thẳng trên máy, trong Docker, trên PC Linux hoặc Jetson qua SSH
  - mọi mã Python chạy trong dev container Linux

## Kết quả quyết định

Phương án được chọn: pnpm, cài bằng `npm install -g`; Node do pnpm tải theo `devEngines.runtime`; Python 3.14; uv; ba mức chạy. Mỗi lựa chọn đáp ứng các yếu tố quyết định tốt hơn phương án còn lại của nó (xem mục "Ưu và nhược của từng phương án").

- JavaScript:
  - Dùng pnpm dòng 12.x, ghim đúng một bản đã phát hành ít nhất 3 ngày trong `devEngines.packageManager` của `package.json`, với `onFail: error` ([pnpm](https://pnpm.io/package_json#devenginespackagemanager)). Dòng 11.28.x là phương án lùi, cùng định dạng lockfile.
  - Cài bằng `npm install -g pnpm@<bản chính xác>`, không dùng Corepack.
  - `pnpm-workspace.yaml` đặt `minimumReleaseAge: 4320` và `trustPolicy: no-downgrade`, giữ mặc định `strictDepBuilds` và `blockExoticSubdeps`. Dependency cần chạy script build được duyệt bằng `pnpm approve-builds`, kết quả ghi vào `allowBuilds`.
  - CI và Docker cài bằng `pnpm install --frozen-lockfile`. pnpm chỉ chạy trên máy phát triển, trên CI và trong stage build; thiết bị chỉ nhận file tĩnh của HMI.
- Node: dùng Node 26 LTS, do pnpm tự tải theo `devEngines.runtime` với `onFail: download`; bản chính xác và checksum ghim trong `pnpm-lock.yaml` ([pnpm](https://pnpm.io/package_json#devenginesruntime)). Không dùng trình quản lý phiên bản Node, không có `.nvmrc`.
- Python: 3.14. Phiên bản ghim trong `robot-core/.python-version` ([uv](https://docs.astral.sh/uv/concepts/python-versions/#python-version-files)).
  - Status: accepted.
  - Quy tắc đóng phần này: ur_rtde 1.6.5 build được từ source trên Python 3.14 cho cả amd64 và arm64 thì chấp nhận 3.14, không được thì chấp nhận 3.12. Spike ngày 2026-11-12 build được trên cả hai kiến trúc.
  - Kết quả spike: ur_rtde 1.6.5 build từ sdist trên CPython 3.14.10 cho `linux/amd64` và `linux/arm64`, trong image nền `python:3.14-slim` (Debian 13 trixie); trên cả hai kiến trúc, `rtde_control`, `rtde_receive`, `rtde_io`, `dashboard_client` và `script_client` import được. Spike không chạy ur_rtde với URSim; phần đó do test integration ở mức 2 kiểm (ADR 0004).
  - PyPI không có wheel cp313, cp314 hay aarch64 cho ur_rtde 1.6.5, nên mọi image dùng Python 3.14 đều build ur_rtde từ source. Bước build mất khoảng 5 phút trên amd64 và khoảng 56 phút trên arm64 chạy giả lập bằng QEMU (Docker Desktop trên máy x86_64, 6 job song song đặt qua `CMAKE_BUILD_PARALLEL_LEVEL`).
  - Bản arm64 của image `core` build trên runner arm64 của GitHub (`ubuntu-24.04-arm`), không qua QEMU: giả lập QEMU chậm hơn nhiều so với build trên máy cùng kiến trúc ([Docker](https://docs.docker.com/build/building/multi-platform/)), còn runner arm64 dùng được cho repo private và tính vào phút miễn phí ([GitHub Changelog](https://github.blog/changelog/2026-01-29-arm64-standard-runners-are-now-available-in-private-repositories), [GitHub Docs](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)).
  - Stage build của image `core` cần mạng và `git`: CMake của ur_rtde kéo pybind11 v2.13.6 từ GitHub bằng `git` lúc build.
  - Các gói mà ur_rtde cần để build (setuptools, setuptools_scm, pybind11) ghim phiên bản bằng file constraints: `setup.py` của ur_rtde import `distutils.version`, mà từ Python 3.12 `distutils` không còn trong thư viện chuẩn ([PEP 632](https://peps.python.org/pep-0632/)), nên lệnh import này chỉ chạy được nhờ bản `distutils` đi kèm setuptools; không ghim thì mỗi lần build lấy setuptools mới nhất.
  - Target runtime của image `core` cần thư viện dùng chung Boost.Thread, trên Debian 13 trixie là gói `libboost-thread1.83.0`: mọi module của ur_rtde liên kết tới `libboost_thread.so.1.83.0` và không cần thư viện Boost nào khác.
- Công cụ Python:
  - [uv](https://docs.astral.sh/uv/) quản lý môi trường; lock bằng `uv.lock`.
  - Build backend hatchling cộng [hatch-vcs](https://github.com/ofek/hatch-vcs), phiên bản lấy từ tag Git. Khi build trong Docker, phiên bản truyền vào qua biến pretend-version của [setuptools-scm](https://setuptools-scm.readthedocs.io/en/latest/overrides/).
  - Lint bằng ruff, kiểm kiểu bằng mypy, độ dài dòng 88 ([mặc định của ruff](https://docs.astral.sh/ruff/settings/#line-length)).
  - [pre-commit](https://pre-commit.com/) 4.7 trở lên, cài bằng `uv tool install pre-commit`.

Mã chạy và được kiểm ở ba mức; mỗi người làm tới mức máy của mình cho phép:

| Mức | Chạy ở đâu | Dùng để kiểm |
| --- | --- | --- |
| 1 | Thẳng trên máy Windows, macOS hoặc Linux, bằng uv và pnpm | unit test, adapter mô phỏng, API, mission, HMI |
| 2 | Docker Desktop (WSL2) hoặc Docker Engine | cả stack bằng `deploy/compose.dev.yaml`, test integration, test cần Pinocchio, adapter UR nối với bộ mô phỏng URSim |
| 3 | PC Linux hoặc Jetson, làm việc qua SSH; máy cần Docker Engine và NVIDIA Container Toolkit | test với phần cứng thật và GPU |

- pre-commit, ruff và commitlint chạy thẳng trên máy.
- Dev container (`.devcontainer/`) là tuỳ chọn, dành cho người muốn làm việc trong môi trường Linux.
- `pin` và `ur_rtde` khai kèm [environment marker](https://packaging.python.org/en/latest/specifications/dependency-specifiers/#environment-markers) `sys_platform == 'linux'`, nên `uv sync` trên Windows và macOS không cài hai gói này.
- Test cần Pinocchio gọi [`pytest.importorskip`](https://docs.pytest.org/en/stable/how-to/skipping.html), nên tự bỏ qua trên máy thiếu gói; job Linux của CI coi việc bỏ qua đó là lỗi.
- CI lấy job Linux làm cổng chốt. Job Windows kiểm mức 1 và chỉ chạy khi đổi file Python hoặc HMI.
- Cấu hình Git: trên Windows, cấp máy chỉ đặt `core.longpaths=true`; các thiết lập `core.autocrlf=false`, `gpg.format=ssh`, `commit.gpgsign=true`, `tag.gpgSign=true`, `user.signingkey` và `gpg.ssh.allowedSignersFile` đặt trong `.git/config` của repo, để không ép ký hay đổi cách xử lý xuống dòng ở repo khác trên cùng máy.

### Hệ quả

- Ưu: lỡ gõ `npm install` trong repo thì báo lỗi ngay.
- Ưu: người chỉ có máy Windows hoặc macOS vẫn làm được unit test, adapter mô phỏng, API, mission và HMI mà không cần Docker.
- Nhược: trên máy không phải Linux, test cần Pinocchio bị bỏ qua ở mức 1; muốn kiểm đủ thì chạy mức 2 hoặc dựa vào job Linux của CI. Marker `sys_platform == 'linux'` loại cả `pin` trên macOS, dù PyPI có wheel macOS.
- Nhược: mọi máy Linux, kể cả amd64, phải build ur_rtde từ source, vì không có wheel cho Python trên 3.12; mỗi lần build cần trình biên dịch C/C++, CMake, `git`, thư viện Boost (system, thread, program_options) và mạng.
- Nhược: lỗi chỉ xảy ra trên Windows, trong thay đổi không đụng file Python hay HMI, thì CI không bắt được.
- Nhược: trên Windows, store dùng chung của pnpm chỉ có tác dụng trong cùng một ổ đĩa.

### Xác nhận

- `package.json` khai `devEngines.packageManager` (pnpm bản chính xác, `onFail: error`) và `devEngines.runtime` (Node 26, `onFail: download`); `pnpm-lock.yaml` ghim bản Node kèm checksum. Chạy `npm install` trong repo phải báo lỗi.
- CI cài đúng bản pnpm đọc từ `devEngines.packageManager.version` rồi chạy `pnpm install --frozen-lockfile`; lockfile lệch với `package.json` thì CI dừng.
- `.pre-commit-config.yaml` khai `minimum_pre_commit_version: "4.7.0"`, nên bản pre-commit cũ hơn báo lỗi thay vì chạy hook; CI chạy hook bằng pre-commit 4.7.0.
- Khi có mã Python, `.pre-commit-config.yaml` thêm hook ruff và `uv lock --check`; job Linux của CI thất bại nếu có test cần Pinocchio bị bỏ qua; job Windows chạy test mức 1 khi đổi file Python hoặc HMI.
- Phần phiên bản Python đã được xác nhận bằng spike ghi ở mục Kết quả quyết định; `robot-core/.python-version` ghi đúng bản đã chốt.

## Ưu và nhược của từng phương án

- pnpm (chọn):
  - Ưu: an toàn ngay từ mặc định: script build của dependency chưa được duyệt làm lệnh cài thất bại, bản mới phải phát hành đủ 1 ngày mới được cài, dependency gián tiếp lấy từ git hay tarball bị chặn ([pnpm](https://pnpm.io/supply-chain-security)).
  - Ưu: `node_modules` không phẳng, nên HMI không import được gói chưa khai báo.
  - Ưu: chỉ có một lockfile, ở gốc workspace.
  - Trung tính: không chuẩn nào ưu tiên npm hay pnpm; Vite, GitHub Actions, Dependabot và Renovate hỗ trợ cả hai.
  - Nhược: không đi kèm Node, phải cài thêm trên từng máy.
- npm:
  - Ưu: đi kèm Node.
  - Trung tính: npm 11.16 trở lên có cơ chế bảo vệ tương tự, nhưng phải tự bật.
  - Nhược: `node_modules` phẳng, nên mã import được cả gói chưa khai báo.
- `npm install -g pnpm@<bản chính xác>` (chọn):
  - Ưu: không phụ thuộc Corepack.
  - Nhược: máy cần sẵn Node.js 18 trở lên và npm ([pnpm](https://pnpm.io/installation)).
- Corepack:
  - Nhược: còn thử nghiệm trong Node 24 và không còn đi kèm Node từ bản 25.
- pnpm tự tải Node theo `devEngines.runtime` (chọn):
  - Ưu: phiên bản Node khai ở một chỗ, cạnh phiên bản pnpm; bản chính xác và checksum nằm trong lockfile.
  - Ưu: không cần thêm công cụ; Node có sẵn trên máy giữ nguyên.
- Trình quản lý phiên bản Node đọc `.nvmrc`, ví dụ fnm:
  - Ưu: dự án khác trên máy vẫn dùng bản Node của chúng.
  - Nhược: mỗi máy phải cài thêm một công cụ; phiên bản Node nằm ở `.nvmrc`, tách khỏi chỗ khai pnpm.
- Python 3.14 (chọn):
  - Ưu: còn nhận bản vá lỗi tới 2027-10.
  - Ưu: `pin` 4.1.0 và onnxruntime 1.31.1 có wheel cho 3.14; numpy 2.5 và scipy 1.18 chỉ cần Python 3.12 trở lên.
  - Trung tính: wheel ur_rtde cho Windows chỉ tới 3.12, nhưng mức 1 không cần ur_rtde: chỉ adapter UR dùng nó, và adapter này chạy ở mức 2–3 trên Linux.
  - Nhược: ur_rtde 1.6.5 không có wheel cho 3.14, nên trên mọi kiến trúc đều phải build từ source; spike build được trên cả amd64 và arm64.
- Python 3.12:
  - Ưu: ur_rtde 1.6.5 có wheel cho 3.12 trên Linux x86_64 và Windows.
  - Nhược: chỉ còn nhận bản vá bảo mật, tới 2028-10.
  - Nhược: trên arm64 vẫn phải build ur_rtde từ source, vì không bản Python nào có wheel arm64.
- uv (chọn):
  - Ưu: lấy gói từ PyPI, nơi có ur_rtde cả dạng wheel lẫn source.
  - Ưu: một công cụ lo cả lockfile, môi trường và việc cài pre-commit.
  - Nhược: PyPI không có wheel Pinocchio cho Windows, nên trên Windows test động học phải chạy qua Docker (mức 2).
- [pixi](https://pixi.prefix.dev/latest/) cộng conda-forge:
  - Ưu: conda-forge có Pinocchio cho win-64, nên test động học chạy được thẳng trên Windows.
  - Nhược: conda-forge không có gói ur_rtde, nên gói này vẫn phải lấy từ nguồn khác.
- Ba mức chạy (chọn):
  - Ưu: việc không cần Linux không phải qua container; mỗi người kiểm tới mức máy của mình cho phép.
  - Nhược: phần cần Pinocchio phải kiểm trên Linux: mức 2, mức 3 hoặc job Linux của CI.
- Mọi mã Python chạy trong dev container Linux:
  - Ưu: mọi người dùng chung một môi trường Linux, nơi có wheel Pinocchio.
  - Nhược: cả việc không cần Linux cũng phải chạy qua container.

## Thông tin thêm

- Xét lại công cụ Python nếu người phát triển cần chạy test động học ngay trên Windows mà không qua Docker; khi đó pixi cộng conda-forge là phương án đã biết.
- Các điểm chưa quyết:
  - Phiên bản uv chưa được ghim.
  - Test cần ur_rtde bỏ qua thế nào trên máy không cài gói này; quy tắc `pytest.importorskip` ở trên mới áp cho test cần Pinocchio.
  - Có cho macOS cài `pin` hay không, vì marker `sys_platform == 'linux'` hiện loại cả macOS.
  - `training/` dùng chung phiên bản Python với `robot-core` hay ghim riêng.
- `uv.lock`, hatchling cộng hatch-vcs, mypy và độ dài dòng 88 là lựa chọn của dự án, chưa được so với phương án khác, ví dụ định dạng lock chuẩn `pylock.toml` của [PEP 751](https://peps.python.org/pep-0751/).
- Liên quan: ADR 0003 (kiến trúc), ADR 0004 (chuyển động và lực chạy trên controller UR), ADR 0012 (tay máy đa năng, tính toán bằng Pinocchio).
