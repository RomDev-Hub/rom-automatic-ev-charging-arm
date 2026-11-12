# Hướng dẫn đóng góp

## Thoả thuận đóng góp

Trước đóng góp đầu tiên, người đóng góp ký với Mr.Ròm một thoả thuận bằng văn bản. Theo thoả thuận đó, quyền tác giả của mọi đóng góp thuộc Mr.Ròm, hoặc Mr.Ròm được cấp quyền đủ rộng để đổi giấy phép hay thương mại hoá về sau. Đóng góp chưa có thoả thuận thì chưa được nhận.

## Môi trường làm việc

### Cài đặt

- Công cụ chung: Git, pnpm 12, uv, pre-commit 4.7 trở lên; Docker cho mức 2.
- Sau khi clone, chạy `pnpm install` rồi `pre-commit install`. pnpm tự tải Node theo `devEngines` trong `package.json`.
- Mọi commit đều có chữ ký: `git config gpg.format ssh`, `git config user.signingkey <khoá công khai>`, `git config commit.gpgsign true`, `git config tag.gpgSign true`. Để kiểm chữ ký trên máy (`git log --show-signature`), khai thêm `git config gpg.ssh.allowedSignersFile <file khoá công khai được phép>`.

### Ba mức chạy và kiểm

Mã chạy và được kiểm ở ba mức. Mỗi người làm tới mức mà máy của mình cho phép:

| Mức | Chạy ở đâu | Kiểm được |
| --- | --- | --- |
| 1 | Thẳng trên máy: Windows, macOS hoặc Linux | unit test, adapter mô phỏng, API, mission, giao diện vận hành |
| 2 | Docker Desktop (WSL2) hoặc Docker Engine | cả stack bằng Docker Compose, test integration, test cần Pinocchio, adapter UR nối với bộ mô phỏng URSim |
| 3 | PC Linux hoặc Jetson, làm việc qua SSH | test với tay máy, camera và GPU thật; máy đích cần Docker Engine và NVIDIA Container Toolkit |

- Pinocchio và ur_rtde chỉ khai cho Linux, vì PyPI không có đủ bản cài sẵn cho các nền tảng khác. Trên máy khác, test cần Pinocchio tự bỏ qua; CI chạy trên Linux và coi việc bỏ qua đó là lỗi.
- Trên Linux, `uv sync` build ur_rtde từ source vì PyPI không có wheel cho Python 3.14, nên máy cần trình biên dịch C/C++, CMake, git, Boost (system, thread, program_options) và mạng ra GitHub; trên Debian và Ubuntu là các gói `g++ cmake git libboost-system-dev libboost-thread-dev libboost-program-options-dev`.
- Dev container (`.devcontainer/`) là tuỳ chọn, cho ai muốn mở repo trong môi trường Linux.

Ở mức 2, test của robot-core chạy trong target dev của image `core`. Target này dựng trên target chạy thật nên dùng đúng thư viện hệ thống của image đó; test cần Pinocchio chạy, không test nào bị bỏ qua. Lần build đầu biên dịch ur_rtde, mất khoảng 6 phút trên amd64; các lần sau dùng lại cache.

```bash
docker build -f deploy/docker/core.Dockerfile --target dev -t ev-arm-core:dev .
docker run --rm --network none ev-arm-core:dev pytest
```

Stack mô phỏng chạy bằng `deploy/compose.yaml` cộng `deploy/compose.sim.yaml`; thêm `-f deploy/compose.dev.yaml` sau cùng để chạy bằng target dev. Stack dùng volume riêng `ev-arm-sim-*`, không đụng volume của thiết bị. `core` không mở cổng nào ra host, nên gọi API từ một container gắn vào mạng `ev-arm_cell`.

```bash
docker compose -f deploy/compose.yaml -f deploy/compose.sim.yaml up -d --build
# Tạo tài khoản quản trị; mật khẩu được hỏi trên terminal, hoặc đọc một dòng từ stdin khi chạy với -T.
docker compose -f deploy/compose.yaml -f deploy/compose.sim.yaml run --rm core robot-core admin create <tên>
# Dừng stack và xoá volume của nó.
docker compose -f deploy/compose.yaml -f deploy/compose.sim.yaml down -v
```

## Kiểm tra

- Hook do framework pre-commit quản lý, cấu hình ở `.pre-commit-config.yaml`; repo không dùng husky. `pre-commit install` cài hook `pre-commit` và `commit-msg` vào `.git/hooks/`. Thư mục này không nằm trong Git, nên mỗi bản clone phải tự cài.
- Hook `no-commit-to-branch` chặn commit trên `main` và `develop`; trên GitHub, ruleset của hai nhánh này chặn mọi thay đổi không qua pull request (mục "Nhánh và lịch sử"). CI chạy các hook với `SKIP=no-commit-to-branch`, vì khi CI chạy trên `main` hay `develop` thì checkout đứng ở chính nhánh đó.
- Hook pre-commit chạy ở mỗi commit; commitlint chạy ở hook commit-msg. Trên mỗi PR và mỗi lần `main` hay `develop` đổi, CI chạy commitlint trên từng commit mới và chạy lại các hook trên toàn bộ file của commit cuối. Kiểm từng commit qua hook thì chạy `git rebase -x` như mục "Nhánh và lịch sử".
- Với `operator-ui`, hook chạy ESLint, Prettier, kiểm kiểu và kiểm kiểu sinh từ `contracts/` còn khớp; test chạy bằng `pnpm --filter operator-ui run test`, bản build bằng `pnpm --filter operator-ui run build`. Sau khi đổi `contracts/`, sinh lại kiểu bằng `pnpm --filter operator-ui run contracts`.
- Không dùng `--no-verify`.

## Ngôn ngữ

- Tên định danh (kể cả tên bước trong workflow CI), docstring và thông báo cho developer (log, lỗi) viết tiếng Anh.
- Comment trong mã nguồn Python và TypeScript viết tiếng Anh, theo khuyến nghị của PEP 8.
- Comment trong file cấu hình viết tiếng Việt: YAML, TOML, workflow CI, `.gitattributes`, `.gitignore`, `.editorconfig`, `commitlint.config.mjs`.
- Tài liệu, ADR, mô tả và body commit viết tiếng Việt. Label trong body commit và khoá footer viết tiếng Anh.
- Chuỗi hiển thị cho người dùng đi qua `locales/` (vi, en).

## Bố cục thư mục

- Khung thư mục đã dựng sẵn. Thư mục còn rỗng giữ bằng `.gitkeep`. Khi thêm file thật đầu tiên vào thư mục thì xoá `.gitkeep` trong cùng commit.
- `scripts/check_layout.py` chặn thư mục nằm ngoài danh sách cho phép. Muốn thêm thư mục mới thì sửa danh sách trong script và ADR 0002 trong cùng một commit.

## Quy ước commit

Theo Conventional Commits 1.0.0, kiểm bằng commitlint với cấu hình `commitlint.config.mjs`.

### Một commit làm một việc

- Mỗi commit là một thay đổi logic, tự build được và qua test.
- Tách riêng:
  - refactor khỏi thay đổi hành vi;
  - đổi tên khỏi sửa nội dung;
  - dependency khỏi code;
  - phần an toàn khỏi phần còn lại.

### Cấu trúc

```text
<type>(<scope>)!: <mô tả>

- <label>: <nội dung>
  <dòng tiếp theo của cùng ý, thụt 2 dấu cách>

<footer>
```

- Chỉ header là bắt buộc. `(<scope>)` và `!` là tuỳ chọn.
- Body bắt buộc theo bảng ở mục "Body".
- Body và footer cách phần trước một dòng trống.
- `type`, `scope`, `!`, `label` và khoá footer dùng tiếng Anh ASCII.
- Mô tả và nội dung viết tiếng Việt, mã hoá UTF-8, chuẩn hoá NFC.

Ví dụ:

```text
feat(mission): thêm trạng thái chờ tài xế rời xe

- Why: khi xe vừa dừng, tay máy có thể bắt đầu chạy trong lúc tài xế
  còn đứng cạnh cửa.
- What: trạng thái DRIVER_EGRESS giữ máy ở chế độ chờ tới khi khoảng
  cách tới người đạt 1,6 m liên tục trong 1,5 s.
- Rejected: bộ hẹn giờ cố định, vì không biết người còn trong vùng
  hay không.

Closes #23
```

### Header

- Header là bản tóm tắt để đọc lướt và tìm kiếm, tối đa 72 ký tự; cần làm rõ chi tiết hơn thì thể hiện thêm ở body.

#### Type

| type | Dùng khi | Phiên bản | Mục changelog |
| --- | --- | --- | --- |
| feat | thêm khả năng mà người dùng, client API hay người triển khai thấy được | MINOR | Added |
| fix | sửa hành vi sai | PATCH | Fixed |
| perf | tăng hiệu năng; body ghi số đo trước và sau | PATCH | Changed |
| refactor | đổi cấu trúc code, không đổi hành vi | không đổi | không ghi |
| docs | chỉ tài liệu, ADR, README | không đổi | không ghi |
| test | chỉ test | không đổi | không ghi |
| build | build, dependency, lockfile, Dockerfile, Compose | không đổi | không ghi |
| ci | workflow CI | không đổi | không ghi |
| chore | bảo trì khác: ignore, editorconfig, commit phát hành | không đổi | không ghi |
| style | chỉ định dạng | không đổi | không ghi |
| revert | hoàn tác một commit | ngược với commit bị hoàn tác | Changed |

#### Scope

| scope | Đường dẫn | Phạm vi |
| --- | --- | --- |
| api | `robot-core/src/robot_core/gateway/` (route, WSS), `contracts/` | hợp đồng giao tiếp |
| auth | `robot-core/src/robot_core/gateway/` (session, vai trò, kiểm toán) | đăng nhập, phân quyền |
| mission | `robot-core/src/robot_core/mission/` | trạng thái, guard, dispatcher |
| motion | `robot-core/src/robot_core/motion/` | director, kiểm segment |
| arm | `robot-core/src/robot_core/arm/`, `defaults/arms/`, `defaults/tools/` | model tay máy, tool, FK/IK |
| safety | logic dừng, chốt, SAFE_HOLD; `docs/safety/` | thay đổi có mục đích an toàn |
| perception | `robot-core/src/robot_core/perception/` | nhận dạng, tư thế cổng sạc |
| calib | `robot-core/src/robot_core/calibration/` | hiệu chuẩn |
| hal | `robot-core/src/robot_core/ports/`, `adapters/` trừ `adapters/sim/` | giao tiếp thiết bị |
| sim | `robot-core/src/robot_core/adapters/sim/` | mô phỏng, lỗi giả lập |
| config | `robot-core/src/robot_core/config/`, schema cấu hình, `defaults/vehicles/` | cấu hình |
| recording | `robot-core/src/robot_core/recording/` | MCAP, journal |
| harvest | `robot-core/src/robot_core/harvest/` | thu thập, làm mờ, gửi dữ liệu |
| ota | `robot-core/src/robot_core/ota/`, `deploy/release/`, `deploy/host/updater/`, `deploy/os/` | cập nhật |
| cli | `robot-core/src/robot_core/cli/` | lệnh dòng lệnh |
| training | `training/` | huấn luyện, đánh giá, xuất model |
| hmi | `operator-ui/` | giao diện vận hành |
| i18n | `robot-core/src/robot_core/locales/`, `docs/glossary.md` | ngôn ngữ, thuật ngữ |
| deploy | `deploy/` (phần còn lại), `.devcontainer/` | đóng gói, triển khai |
| adr | `docs/decisions/` | quyết định kiến trúc |
| release | `CHANGELOG.md` khi phát hành | phát hành |
| deps, deps-dev | (Dependabot) | cập nhật dependency |

- Thay đổi toàn repo thì bỏ scope. Workflow CI dùng type `ci`, không scope. README và CONTRIBUTING dùng type `docs`, không scope.
- Không tự đặt scope mới. Muốn thêm scope thì sửa `commitlint.config.mjs` và bảng này trong cùng một commit.

#### Mô tả

- Bắt đầu bằng động từ mệnh lệnh viết thường: thêm, sửa, bỏ, tách, gộp, đổi, chuyển, chặn, cho phép, ghi, dựng, nâng, hạ, ghim.
- Không chủ ngữ, không dùng "đã" hay "vừa", không dấu chấm cuối, không số issue.
- Tên định danh và đường dẫn giữ nguyên, đặt trong backtick khi cần.

### Body

Mỗi ý một dòng, dạng `- <label>: <nội dung>`. Label là một từ tiếng Anh trong bộ dưới đây, viết theo đúng thứ tự của bảng, mỗi label tối đa một lần:

| Label | Ghi gì |
| --- | --- |
| `Why` | vấn đề phải sửa hoặc nhu cầu mới; không đổi thì sai gì |
| `What` | thay đổi cụ thể mà header không chứa hết: hành vi, giá trị cũ và mới, thành phần bị đụng |
| `How` | cách làm và vì sao chọn cách này |
| `Rejected` | phương án đã cân nhắc mà không chọn, kèm lý do |
| `Test` | đã kiểm chứng thế nào: test nào, ở mức nào, số đo kèm đơn vị SI |
| `Impact` | điều thay đổi khi triển khai |

Với các scope liên quan an toàn, body và một số label là bắt buộc:

| scope | type `feat`, `fix`, `perf`, `refactor` | type khác, trừ `revert` |
| --- | --- | --- |
| `safety` | Why, How, Rejected, Test, Impact | Why |
| `motion`, `arm`, `hal` | Why, How, Test | Why |
| `auth`, `ota` | Why, How, Test, Impact | Why |
| `config`, `harvest` | Why, What, Impact | Why |

- Ở mọi scope: type `perf` cần Why, How và Test (số đo trước và sau); header có `!` cần Why.
- Commit rơi vào nhiều trường hợp thì cần đủ label của mọi trường hợp đó. commitlint kiểm label bắt buộc, thứ tự và số lần.
- Label không bắt buộc chỉ viết khi có nội dung. Ngoài các trường hợp trên, body tuỳ chọn và viết tự do.
- Xuống dòng ở 72 ký tự; dòng tiếp theo của một ý thụt 2 dấu cách. commitlint chặn dòng dài quá 100 ký tự.
- Nhắc tới commit khác theo dạng `git show -s --pretty=reference <sha>`.

Ví dụ:

```text
fix(auth): chặn nhập cấu hình an toàn khi chưa nâng quyền

- Why: route nhập và khôi phục cấu hình nhận yêu cầu từ mọi máy trong
  mạng trạm, nên ai cũng nới được giới hạn lực.
- How: hai route này cần vai trò bảo trì và xác thực lại; mỗi lần gọi
  ghi một dòng nhật ký kiểm toán.
- Test: test API cho ba vai trò; gọi khi chưa đủ quyền nhận mã 403.
- Impact: tài khoản không có vai trò bảo trì không nhập được cấu hình
  an toàn nữa.
```

### Footer

| Footer | Khi nào |
| --- | --- |
| `BREAKING CHANGE: <ghi chú chuyển đổi>` | thay đổi không tương thích |
| `Closes #n` hoặc `Fixes #n` | đóng issue khi vào nhánh chính |
| `Refs: #n` hoặc `Refs: <sha>` | tham chiếu, không đóng |
| `Co-authored-by: Tên <email>` | người cùng làm |

- Khối footer là đoạn cuối và chỉ chứa footer.
- Không tự động thêm `Signed-off-by`.

### Thay đổi không tương thích

- Là thay đổi khiến client hiện có của một hợp đồng công khai bị hỏng nếu không sửa theo. Các hợp đồng công khai gồm:
  - `contracts/`;
  - schema cấu hình và file cấu hình trạm;
  - `robot-core/src/robot_core/ports/`;
  - schema kênh MCAP;
  - biến môi trường, volume, cổng và tên service của Docker;
  - lệnh và cờ CLI;
  - định dạng gói dữ liệu upload.
- Đánh dấu bằng cả `!` lẫn footer `BREAKING CHANGE:`; commitlint chặn khi thiếu một trong hai.

Commit có `!` hoặc footer `BREAKING CHANGE` tăng MAJOR từ bản 1.0.0; khi còn ở 0.y.z thì tăng MINOR. Commit đó được ghi vào mục Changed với tiền tố "Không tương thích:".

Ví dụ:

```text
feat(arm)!: đổi khung gốc của model sang base của controller

- Why: FK tính theo base_link của URDF, lệch 180° quanh trục z so với
  base mà controller UR báo.
- How: model dùng frame base, nên pose tính ra khớp với pose mà
  controller báo.
- Test: so FK với pose controller tại 20 tư thế; lệch dưới 1 mm và
  0,1°.

BREAKING CHANGE: pose trong cấu hình trạm phải tính lại theo frame base
```

### Revert

```text
revert: <header của commit bị hoàn tác>

This reverts commit <sha>.

<lý do hoàn tác>
```

Dòng "This reverts commit" để nguyên như Git sinh ra. Header của commit revert được dài tới 80 ký tự, vì có thêm tiền tố `revert:` và một dấu cách.

### Commit của bot

- Prefix do `.github/dependabot.yml` đặt: cập nhật gói npm và hook pre-commit dùng `build(deps)` hoặc `build(deps-dev)`; cập nhật GitHub Actions dùng `ci(deps)`.
- Commit của bot giữ tiếng Anh.
- CI không chạy commitlint trên commit do `dependabot[bot]` viết, vì body commit do bot sinh có dòng dài và ghi chú phát hành.

## Nhánh và lịch sử

Repo theo mô hình git-flow: `main` chỉ chứa bản đã phát hành, `develop` gom thay đổi cho bản kế tiếp.

- `main` chỉ chứa các bản đã phát hành: mỗi lần `main` đổi là một bản phát hành mang tag `vX.Y.Z`, và `main` chỉ nhận PR từ nhánh `release/X.Y.Z` hay `hotfix/X.Y.Z` (mục "Phát hành").
- `develop` là nhánh mặc định, gom mọi thay đổi đã kiểm cho bản kế tiếp và luôn chạy được. PR của Dependabot cũng vào `develop`.
- Không ai commit hay push thẳng vào `main` hay `develop`. Ruleset của repo trên GitHub bắt mọi thay đổi vào hai nhánh này đi qua pull request (PR), bắt các job CI chính xanh trên nhánh đã cập nhật theo nhánh đích, bắt commit có chữ ký, chặn force-push và xoá nhánh; ở máy, hook `no-commit-to-branch` chặn commit trên hai nhánh này.
- Mỗi việc một nhánh, tách từ `origin/develop` mới nhất và sống ngắn, đặt tên `<type>/<scope>-<mo-ta>` bằng tiếng Anh, chữ ASCII thường, kebab-case, với type và scope lấy từ mục "Quy ước commit", ví dụ `feat/mission-driver-egress`; việc trải nhiều vùng thì bỏ scope, thành `<type>/<mo-ta>`. Việc lớn chia thành nhiều PR nối tiếp. Nhánh phụ thuộc một PR chưa merge thì tách từ nhánh của PR đó, đặt base của PR mới là nhánh đó và ghi thứ tự merge trong mô tả; khi PR trước đã merge, rebase nhánh sau lên `origin/develop` và đổi base về `develop`.
- Trước khi push: `git fetch origin`, `git rebase origin/develop`, kiểm từng commit bằng `git rebase -x "<lệnh kiểm tra>" origin/develop`, rồi kiểm ở đầu nhánh theo các mức ở mục "Ba mức chạy và kiểm"; `git status` sạch và mọi commit có chữ ký (`git log --format='%h %G? %s' origin/develop..HEAD`).
- Push bằng `git push -u origin <nhánh>`, mở PR vào `develop` (`gh pr create --base develop`) rồi theo dõi CI bằng `gh pr checks <số> --watch`. Tiêu đề PR viết theo dạng header; mô tả viết tiếng Việt, gồm vì sao, thay đổi gì, đã kiểm thế nào, ảnh hưởng tới hợp đồng công khai, cấu hình, dữ liệu hay triển khai, điểm cần Mr.Ròm quyết và thứ tự merge nếu có. PR chưa xong thì mở dạng draft.
- CI đỏ thì đọc log bằng `gh run view <id> --log-failed`, sửa trên nhánh như bullet về sửa commit dưới đây rồi push lại. Nghi lỗi chập chờn thì chạy lại một lần bằng `gh run rerun <id> --failed`; vẫn đỏ thì coi là lỗi thật. Lỗi hạ tầng (runner, mạng, quota) thì báo Mr.Ròm, không sửa code để né.
- PR được merge khi mọi job CI xanh, nhánh đã cập nhật theo nhánh đích và không còn bình luận chưa giải quyết; repo không bắt lượt duyệt. Mr.Ròm merge hoặc chỉ thị merge. Repo chỉ bật kiểu merge commit (`gh pr merge <số> --merge --delete-branch`): các commit của nhánh vào nhánh đích nguyên vẹn cùng chữ ký, và `git log --first-parent` cho lịch sử gọn theo từng PR.
- Trước khi merge, commit sai thì sửa thẳng vào commit đó: `git commit --fixup=<sha>` (sửa nội dung) hoặc `git commit --fixup=amend:<sha>` (sửa cả thông điệp), rồi `git rebase --autosquash --exec "<lệnh kiểm tra>" origin/develop` và `git push --force-with-lease`. Không force-push nhánh của người khác. Lịch sử đã vào `main` hay `develop` không bao giờ bị viết lại: sau khi merge, sửa bằng nhánh mới và PR mới.
- Sau khi merge: `git fetch origin`, `git switch develop`, `git merge --ff-only origin/develop`, rồi xoá worktree và nhánh đã merge, cùng container, volume, image và thư mục tạm đã tạo cho việc đó. Nhánh khác đang mở thì rebase lên `origin/develop` mới, kiểm lại rồi `git push --force-with-lease`.
- Hoàn tác một PR đã merge bằng một PR mới chứa commit revert, `git revert -m 1 <sha của commit merge>`, thông điệp theo mục "Revert".

## Phát hành

- Số phiên bản theo SemVer; Mr.Ròm quyết định khi nào phát hành và số phiên bản. Giữa hai bản phát hành, `CHANGELOG.md` chỉ có mục `## [Unreleased]`, và PR thường không đổi số phiên bản. Tag có dạng `vX.Y.Z`; số phiên bản lấy từ tag, không ghi tay vào file khai báo.
- Chốt bản: nhánh `release/X.Y.Z` tách từ `origin/develop`, có commit `chore(release): phát hành X.Y.Z` chỉ sửa `CHANGELOG.md`: đổi `## [Unreleased]` thành `## [X.Y.Z] - YYYY-MM-DD`, biên tập nội dung mục đó, và mở lại một mục `## [Unreleased]` trống ở trên. Trên nhánh này chỉ sửa lỗi, không thêm tính năng. Mở PR từ nhánh này vào `main`.
- Merge PR đó vào `main` là phát hành: workflow `.github/workflows/release.yaml` lấy số phiên bản từ tên nhánh, dừng nếu CHANGELOG không có mục `## [X.Y.Z]` hoặc tag `vX.Y.Z` đã có, rồi tạo tag `vX.Y.Z` cùng GitHub Release trên commit merge, với nội dung là mục của bản đó trong CHANGELOG. Luồng thường không tạo tag bằng tay; tag và bản phát hành đã đẩy lên không bao giờ bị xoá, dời hay dùng lại: ruleset chặn xoá và dời tag `v*`, và repo bật release immutability.
- Sau khi phát hành, mở PR từ `main` vào `develop` và merge, để `develop` có mục CHANGELOG của bản vừa phát hành.
- Vá gấp bản đã phát hành: nhánh `hotfix/X.Y.Z` tách từ `origin/main`, với X.Y.Z là bản PATCH kế tiếp, có commit sửa lỗi và commit `chore(release): phát hành X.Y.Z` thêm mục `## [X.Y.Z] - YYYY-MM-DD` vào CHANGELOG; mở PR vào `main`, merge là phát hành bản PATCH, rồi đưa `main` về `develop` như trên.
- Workflow phát hành hỏng vì hạ tầng (runner, mạng, quyền, quota) thì sửa cài đặt rồi chạy lại các job hỏng của đúng lần chạy đó (`gh run rerun <id> --failed`).
- `CHANGELOG.md`:
  - tiêu đề mỗi bản dạng `## [X.Y.Z] - YYYY-MM-DD`;
  - tên mục giữ tiếng Anh (Added, Changed, Deprecated, Removed, Fixed, Security), nội dung viết tiếng Việt.
- Bản nháp lấy bằng `pnpm exec git-cliff --unreleased`, rồi biên tập tay. Các sửa lỗi liên quan bảo mật chuyển sang mục Security.

Ví dụ:

```text
chore(release): phát hành 0.1.0
```
