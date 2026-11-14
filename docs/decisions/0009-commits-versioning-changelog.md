# 0009. Commit theo Conventional Commits, phiên bản theo SemVer, changelog theo Keep a Changelog

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Repo chứa mã Python (`robot-core`, `training`) và TypeScript (`operator-ui`), cùng cấu hình, tài liệu và ADR. Lịch sử commit phải cho biết mỗi thay đổi làm gì, vì sao, đã kiểm chứng thế nào, và phải đủ để lập changelog, chọn số phiên bản cho từng bản phát hành. Mỗi loại thay đổi cần ghi những ý khác nhau; thay đổi ở các phần liên quan an toàn phải ghi rõ lý do và cách kiểm chứng.

Phần mềm tới tay người dùng trên thiết bị cài sẵn và được cập nhật qua OTA (ADR 0013), nên ngoài hiện trường có thể cùng lúc chạy nhiều bản. Người nhận thiết bị hoặc bản cài được truy cập repo ở đúng tag đang chạy, và trang "Giới thiệu" của HMI ghi phiên bản cùng commit (ADR 0011). Vì vậy số phiên bản và tag phải khớp nhau, nguồn gốc của commit và tag phải kiểm được, và phải vá được một bản đã giao mà không kéo theo việc đang làm dở.

Repo là repo public của tổ chức trên GitHub, nên dùng được ruleset để bảo vệ nhánh và tag ngay trên GitHub; hook trên máy cộng CI là lớp kiểm tra trước đó. Dự án có một người bảo trì.

Cần chốt: thông điệp commit theo quy ước nào và máy kiểm bằng gì; công cụ nào quản lý hook; số phiên bản đánh ra sao; changelog có dạng gì và lập thế nào; dùng mô hình nhánh nào; thay đổi đi vào nhánh chính thế nào và cổng merge là gì; nhánh và tag được bảo vệ ra sao; commit sai thì sửa thế nào; tag và bản phát hành được tạo ra sao.

## Yếu tố quyết định

- Máy kiểm thay cho trí nhớ: luật nào máy kiểm được thì kiểm ở hook trên máy và kiểm lại trên CI; luật về nhánh và tag thì GitHub chặn.
- Một nguồn luật duy nhất trong repo: luật nằm ở `CONTRIBUTING.md` và file cấu hình, không chép sang nơi khác.
- Phần máy đọc của thông điệp dùng token cố định để công cụ phân tích được; phần người đọc viết tiếng Việt như mọi tài liệu của dự án.
- Bản nháp changelog và mức tăng phiên bản suy ra được từ lịch sử commit.
- Mỗi commit trên nhánh chính là một thay đổi logic, tự build được và qua kiểm tra.
- Mã của bản đã phát hành tách khỏi mã đang phát triển, để vá được bản đang chạy ngoài hiện trường.
- Mọi thay đổi vào nhánh chính đi qua pull request có CI xanh; không ai push thẳng, và lịch sử đã vào nhánh chính không bị viết lại.
- Cổng merge dựa vào máy kiểm, không dựa vào một lượt duyệt mà chính người bảo trì không tự cấp được.
- Nguồn gốc của commit và tag kiểm được.
- Trên nhánh làm việc, lịch sử chỉ chứa trạng thái đúng, không có commit sai rồi commit vá chồng lên.
- Một bộ hook chạy được cho mọi ngôn ngữ của repo và chạy giống nhau trên máy lẫn trên CI.

## Các phương án đã xét

Chỉ các phần dưới đây có hơn một phương án; các phần khác xem mục "Thông tin thêm".

Thông điệp commit:

1. Conventional Commits 1.0.0, body chia ý theo label
2. Conventional Commits 1.0.0, body là đoạn văn tự do

Nơi khai luật của commitlint:

1. `commitlint.config.mjs`
2. `.commitlintrc.yaml`

Công cụ quản lý hook Git:

1. Framework pre-commit
2. husky

Mô hình nhánh:

1. Git-flow: `main` cho bản đã phát hành, `develop` cho bản kế tiếp, nhánh `release` và `hotfix`
2. GitHub flow: một nhánh `main`, phát hành bằng PR vào `main`

Cách đưa nhánh vào nhánh đích:

1. Pull request, merge commit
2. Rebase lên nhánh đích rồi fast-forward
3. Squash
4. Nút "Rebase and merge" của GitHub

Cách bảo vệ `main` và `develop`:

1. Ruleset của GitHub
2. Hook trên máy chặn commit và push

Cổng merge:

1. Mọi job CI xanh, không bắt lượt duyệt
2. Bắt một lượt duyệt, do một job CI tự duyệt khi các job khác xanh

Cách sửa commit sai:

1. Gộp phần sửa vào commit gây lỗi trước khi merge
2. Thêm commit sửa lên trên

Cách tạo tag và bản phát hành:

1. Workflow tạo khi PR từ `release/X.Y.Z` hay `hotfix/X.Y.Z` được merge vào `main`, sau khi artifact đã build xong
2. Tag annotated có chữ ký tạo trên máy rồi push

## Kết quả quyết định

Luật chi tiết chỉ nằm ở `CONTRIBUTING.md` và các file cấu hình nêu dưới đây; ADR này ghi phương án được chọn và lý do, không chép bảng type, scope, label hay footer.

Phương án được chọn cho từng phần:

- **Thông điệp commit:** Conventional Commits 1.0.0, body chia ý theo label (mục "Quy ước commit" của CONTRIBUTING). Type, scope, `!`, label và khoá footer dùng tiếng Anh ASCII; mô tả và nội dung viết tiếng Việt, mã hoá UTF-8, chuẩn hoá NFC. Ba phần của thông điệp gọi là header, body và footer; mỗi ý của body mở đầu bằng một label (Why, What, How, Rejected, Test, Impact), label bắt buộc tuỳ scope và type. Header tối đa 72 ký tự; header của commit revert được tới 80.
  - Vì Conventional Commits gắn type với mức tăng SemVer và với mục changelog; body chia ý dễ đọc hơn đoạn văn, và mỗi loại thay đổi cần những ý khác nhau.
  - Vì token máy đọc giữ tiếng Anh ASCII để công cụ phân tích được; gọi các phần là header, body, footer và label thì tên các phần không lẫn hai thứ tiếng.
  - Vì header chỉ là bản tóm tắt để đọc lướt và tìm kiếm, còn tiếng Việt cùng ý dài hơn tiếng Anh, nên giới hạn là 72 thay cho mức 50 ký tự mà tài liệu Git khuyên; chuẩn hoá NFC để đếm độ dài chữ có dấu cho đúng.
  - Vì tiền tố `revert:` cùng một dấu cách thêm 8 ký tự vào header gốc, nên giới hạn 72 sẽ chặn oan commit revert của một header gốc dài.
- **Kiểm thông điệp:** commitlint với cấu hình `commitlint.config.mjs`, mở rộng `@commitlint/config-conventional` và thêm ba luật tự viết: `body-labels` (label bắt buộc, thứ tự, số lần), `breaking-marker` (`!` luôn đi cùng footer `BREAKING CHANGE:`) và `header-length`. commitlint chạy ở hook commit-msg và trên CI cho từng commit mới của mỗi PR và mỗi lần `main` hay `develop` đổi; CI còn kiểm chính bộ luật bằng các mẫu sai phải bị chặn và mẫu đúng phải qua.
  - Vì máy kiểm thay cho trí nhớ; luật tự viết là hàm JavaScript, nên cấu hình phải là file JavaScript.
- **Hook Git:** framework pre-commit, cấu hình ở `.pre-commit-config.yaml`, không dùng husky (mục "Kiểm tra" của CONTRIBUTING). `pre-commit install` cài hook pre-commit và commit-msg vào `.git/hooks/` của từng bản clone; hook `no-commit-to-branch` chặn commit trên `main` và `develop`. CI chạy lại cùng cấu hình bằng `pre-commit run --all-files`, chỉ bỏ qua `no-commit-to-branch`, vì khi CI chạy trên `main` hay `develop` thì checkout đứng ở chính nhánh đó.
  - Vì repo nhiều ngôn ngữ (Python, TypeScript) và pre-commit quản lý hook viết bằng mọi ngôn ngữ; husky chỉ dành cho Node và cần thư mục `.husky/` trong repo; dùng cả hai thì hai bộ hook trùng nhau.
- **Phiên bản:** SemVer 2.0.0, bắt đầu từ 0.1.0; CHANGELOG cũng bắt đầu từ 0.1.0. Type của commit quyết định mức tăng theo bảng "Type" của CONTRIBUTING. Commit có `!` hoặc footer `BREAKING CHANGE` tăng MAJOR từ bản 1.0.0, còn khi ở 0.y.z thì tăng MINOR. Thay đổi không tương thích xác định theo danh sách hợp đồng công khai ở mục "Thay đổi không tương thích" của CONTRIBUTING. Tag đầu tiên là `v0.1.0`, gắn khi xong walking skeleton: lát cắt mỏng nhất chạy đầu-cuối.
  - Vì SemVer dành dòng 0.y.z cho giai đoạn phát triển ban đầu và lấy 1.0.0 làm bản định nghĩa API công khai; FAQ của SemVer gợi ý bắt đầu từ 0.1.0. Tăng MAJOR khi còn ở 0.y.z sẽ đưa repo lên 1.0.0 trước khi API công khai được chốt.
- **Changelog:** `CHANGELOG.md` theo Keep a Changelog 1.1.0; tiêu đề mỗi bản dạng `## [X.Y.Z] - YYYY-MM-DD`, tên mục giữ tiếng Anh (Added, Changed, Deprecated, Removed, Fixed, Security), nội dung viết tiếng Việt. Bản nháp lấy bằng `pnpm exec git-cliff --unreleased` theo `cliff.toml`, rồi biên tập tay; sửa lỗi liên quan bảo mật chuyển sang mục Security; commit không tương thích vào mục Changed với tiền tố "Không tương thích:" (mục "Phát hành" của CONTRIBUTING).
  - Vì type đã cho biết mục changelog, nên bản nháp lấy được từ lịch sử; nhưng Keep a Changelog coi changelog là để người đọc, và cho rằng chép thẳng log commit là ý tồi vì log đầy nhiễu.
- **Mô hình nhánh:** git-flow (mục "Nhánh và lịch sử" của CONTRIBUTING). `main` chỉ chứa bản đã phát hành, mỗi lần đổi mang một tag; `develop` là nhánh mặc định, gom thay đổi cho bản kế tiếp; nhánh làm việc tách từ `develop` và merge về `develop`; `release/X.Y.Z` tách từ `develop` để chốt bản, `hotfix/X.Y.Z` tách từ `main` để vá gấp; sau mỗi lần phát hành, `main` được đưa về `develop` bằng một PR.
  - Vì phần mềm có phiên bản rõ ràng và sẽ có nhiều bản cùng chạy ngoài hiện trường; tác giả của git-flow vẫn khuyên mô hình này cho trường hợp đó, còn với phần mềm giao liên tục thì khuyên luồng đơn giản hơn.
  - Vì `main` luôn đúng bằng bản đã phát hành mới nhất, nên bản vá gấp tách từ đúng mã đang chạy, không kéo theo việc dở trên `develop`.
- **Phát hành:** qua PR từ `release/X.Y.Z` hay `hotfix/X.Y.Z` vào `main`; nhánh đó có commit `chore(release): phát hành X.Y.Z` chỉ sửa `CHANGELOG.md`. Khi PR được merge, workflow `.github/workflows/release.yaml` kiểm số phiên bản và mục CHANGELOG, build và đẩy artifact của bản đó, rồi mới tạo tag `vX.Y.Z` và GitHub Release trên commit merge (mục "Phát hành" của CONTRIBUTING). Luồng thường không tạo tag bằng tay; tag và bản phát hành đã đẩy lên không bị xoá, dời hay dùng lại.
  - Vì phát hành chạy từ một sự kiện đã qua CI, nên tag luôn trỏ đúng commit đã kiểm, không phụ thuộc máy của người phát hành.
  - Vì artifact build xong mới tạo tag và GitHub Release, nên build hỏng không để lại bản phát hành dở, và bản đó vẫn phát hành được bằng `hotfix/X.Y.Z` cùng số.
  - Vì tag do `GITHUB_TOKEN` tạo không kích hoạt workflow khác, nên kiểm, build, tạo tag và GitHub Release nằm trong cùng một workflow.
  - Vì tiền tố `v` là cách thường dùng để đánh dấu số phiên bản trong tên tag; theo SemVer, `v1.2.3` là tên tag còn số phiên bản là `1.2.3`, nên tiêu đề CHANGELOG ghi số không có `v`.
- **Bảo vệ nhánh và tag:** ruleset của GitHub cho `main` và `develop`: mọi thay đổi đi qua PR, các job CI chính phải xanh trên nhánh đã cập nhật theo nhánh đích, bình luận phải được giải quyết, commit phải có chữ ký, chỉ merge bằng merge commit, không force-push, không xoá nhánh; ruleset cho tag `v*`: không xoá, không dời. Repo bật release immutability.
  - Vì GitHub chặn ngay trên server, không ai vượt được bằng `--no-verify` hay bằng một bản clone chưa cài hook; hook trên máy chỉ là lớp báo sớm.
- **Cổng merge:** PR được merge khi mọi job CI xanh; repo không bắt lượt duyệt.
  - Vì dự án có một người bảo trì: GitHub không cho tác giả tự duyệt PR của mình, còn một lượt duyệt do job CI tự cấp không thêm kiểm tra nào ngoài chính các job đó và cần cho GitHub Actions quyền duyệt PR.
- **Chữ ký:** mọi commit ký bằng khoá SSH (mục "Cài đặt" của CONTRIBUTING), và ruleset bắt commit trên `main` và `develop` có chữ ký; commit merge và commit của Dependabot mang chữ ký của GitHub; tag do workflow phát hành tạo.
  - Vì chữ ký cho người khác tin được nguồn gốc của commit, và GitHub kiểm được chữ ký SSH.
- **Lịch sử:** kiểu merge là merge commit; repo chỉ bật kiểu này.
  - Vì merge commit đưa các commit của nhánh vào nhánh đích nguyên vẹn cùng chữ ký, `git log --first-parent` cho lịch sử gọn theo từng PR, và cả PR hoàn tác được bằng một `git revert -m 1`; CI chạy trên kết quả merge của PR, và ruleset bắt nhánh cập nhật theo nhánh đích, nên trạng thái gộp đã được kiểm trước khi merge.
- **Sửa commit sai:** trước khi PR được merge, gộp phần sửa vào chính commit gây lỗi bằng `git commit --fixup`, chạy `git rebase --autosquash --exec` kiểm lại từng commit, rồi `git push --force-with-lease`; chỉ phần sửa sai được gộp, việc mới độc lập vẫn là commit riêng. Sau khi merge thì sửa bằng nhánh mới và PR mới.
  - Vì lịch sử của nhánh chỉ nên chứa trạng thái đúng; còn viết lại sau khi đã merge thì ai đã dựa vào nhánh chính phải tự sửa lịch sử của mình.
- **Commit của bot:** commit của Dependabot giữ tiếng Anh, prefix do `.github/dependabot.yml` đặt; CI không chạy commitlint trên commit do `dependabot[bot]` viết (mục "Commit của bot" của CONTRIBUTING). PR của Dependabot vào `develop`, nhánh mặc định, và đi cùng luồng PR như mọi thay đổi khác; bản vá bảo mật cũng gom thành một PR cho mỗi hệ.
  - Vì body do bot sinh có dòng dài và ghi chú phát hành.

### Hệ quả

- Tốt, vì bản nháp changelog và mức tăng phiên bản suy ra được từ type, dấu `!` và footer `BREAKING CHANGE` của từng commit.
- Tốt, vì thông điệp sai bị chặn ngay lúc commit và bị chặn lại trên CI, không dựa vào trí nhớ của người viết.
- Tốt, vì commit ở các scope liên quan an toàn luôn có đủ label bắt buộc, nên lý do và cách kiểm chứng không bị bỏ sót.
- Tốt, vì `main` luôn đúng bằng bản đã phát hành mới nhất, mỗi PR vào nhánh chính là một commit trên `git log --first-parent`, và lịch sử trên nhánh làm việc chỉ chứa trạng thái đúng.
- Tốt, vì GitHub tự chặn push thẳng, force-push, commit thiếu chữ ký và merge khi job CI chính chưa xanh trên `main` và `develop`.
- Tốt, vì tag và GitHub Release do workflow tạo đúng trên commit merge, chỉ sau khi artifact đã build xong; gói Python lấy phiên bản từ tag qua hatch-vcs, còn khi build trong Docker thì phiên bản truyền qua biến pretend-version của setuptools-scm.
- Xấu, vì git-flow cần thêm nhánh `develop` và một PR đưa `main` về `develop` sau mỗi lần phát hành.
- Xấu, vì mỗi bản clone phải tự chạy `pre-commit install` và tự cấu hình khoá ký, do `.git/hooks/` và `.git/config` không nằm trong Git.
- Xấu, vì viết body theo label tốn công hơn đoạn văn tự do, và thêm scope hay label phải sửa `commitlint.config.mjs` cùng CONTRIBUTING trong một commit.
- Xấu, vì bản nháp của git-cliff chỉ xếp commit vào Added, Changed và Fixed; mục Deprecated, Removed và Security do người biên tập xếp.
- Xấu, vì không có người thứ hai đọc thay đổi trước khi merge: chất lượng dựa vào CI và kỷ luật của người bảo trì.
- Xấu, vì tag không mang chữ ký khoá cá nhân; nguồn gốc của tag dựa vào việc chỉ workflow phát hành tạo tag và ruleset không cho dời hay xoá tag.
- Xấu, vì lịch sử không tuyến tính; từng commit của nhánh được kiểm trên nền của nhánh, còn trạng thái gộp được kiểm qua CI của PR.
- Xấu, vì job CI mới chỉ thành job bắt buộc khi được thêm vào ruleset, và job chạy có điều kiện phải báo trạng thái bỏ qua để ruleset coi là đạt.

### Xác nhận

- Hook commit-msg chạy commitlint ở mỗi commit; CI chạy commitlint trên từng commit mới của mỗi PR và mỗi lần `main` hay `develop` đổi.
- Bước "Commit rules reject and accept the reference messages" trong `.github/workflows/ci.yaml` kiểm chính bộ luật: các mẫu sai phải bị chặn, các mẫu đúng phải qua.
- Các ví dụ thông điệp trong CONTRIBUTING qua `pnpm exec commitlint`.
- CI chạy `pre-commit run --all-files` với đúng `.pre-commit-config.yaml` mà hook trên máy dùng, chỉ bỏ qua `no-commit-to-branch`.
- `gh api repos/RomDev-Hub/rom-automatic-ev-charging-arm/rulesets` liệt kê ruleset của `main`, `develop` và tag `v*` với các luật nêu trên; push thẳng vào `main` hay `develop` bị GitHub từ chối.
- `git log --no-merges --format='%h %G? %s'` cho thấy `G` ở mọi commit không phải merge; cần `gpg.ssh.allowedSignersFile` như mục "Cài đặt" của CONTRIBUTING.
- Sau lần push khởi tạo, mỗi commit trên `git log --first-parent main` là commit merge của một PR từ `release/X.Y.Z` hay `hotfix/X.Y.Z` và mang tag `vX.Y.Z`.
- Commit `chore(release)` chỉ sửa `CHANGELOG.md` (`git show --stat`), và mỗi tag `vX.Y.Z` có đúng một mục `## [X.Y.Z]` trong CHANGELOG cùng một GitHub Release.

## Ưu và nhược của từng phương án

### Conventional Commits 1.0.0, body chia ý theo label

- Tốt, vì mỗi ý có tên riêng, đọc lướt dễ hơn đoạn văn.
- Tốt, vì label bắt buộc tuỳ scope và type, nên commitlint kiểm được thông điệp có đủ ý cần cho từng loại thay đổi.
- Xấu, vì người viết phải theo đúng thứ tự label và biết label nào bắt buộc; sai thì commitlint chặn.

### Conventional Commits 1.0.0, body là đoạn văn tự do

- Tốt, vì viết nhanh, không phải theo khuôn label.
- Xấu, vì khuôn ba ý cố định (vấn đề, vì sao chọn cách làm, phương án bị loại) không hợp mọi scope: có loại thay đổi cần ghi kiểm chứng hay ảnh hưởng khi triển khai, có loại không có phương án bị loại.
- Xấu, vì máy không kiểm được một đoạn văn đã đủ ý hay chưa.

### `commitlint.config.mjs`

- Tốt, vì khai được luật tự viết `body-labels`, `breaking-marker` và `header-length`.

### `.commitlintrc.yaml`

- Xấu, vì YAML không chứa được hàm, nên không khai được luật tự viết.

### Framework pre-commit

- Tốt, vì một cấu hình quản lý hook viết bằng mọi ngôn ngữ, hợp với repo có cả Python và TypeScript.
- Tốt, vì CI chạy lại đúng cấu hình đó bằng `pre-commit run --all-files`.
- Tốt, vì hook ghim theo SHA, và Dependabot mở PR khi hook có bản mới.
- Xấu, vì `pre-commit install` phải chạy trên từng bản clone.

### husky

- Xấu, vì chỉ dành cho Node.
- Xấu, vì cần thư mục `.husky/` trong repo.
- Xấu, vì dùng song song với pre-commit thì hai bộ hook trùng nhau.

### Git-flow

- Tốt, vì `main` luôn là bản đã phát hành mới nhất, nên vá gấp được bản đang chạy mà không kéo theo việc dở.
- Tốt, vì chốt bản trên nhánh `release` riêng, việc mới vẫn vào `develop` trong lúc chốt.
- Xấu, vì thêm nhánh `develop`, thêm PR đưa `main` về `develop` sau mỗi lần phát hành, và hai nhánh chính lệch nhau nếu bỏ sót bước đó.

### GitHub flow

- Tốt, vì chỉ có một nhánh chính, ít bước nhất.
- Xấu, vì `main` gom cả việc chưa phát hành, nên vá một bản đã giao khi `main` đã đi tiếp phải dựng nhánh duy trì riêng lúc cần.

### Pull request, merge commit

- Tốt, vì các commit của nhánh vào nhánh đích nguyên vẹn cùng chữ ký.
- Tốt, vì mọi thay đổi vào nhánh đích đi qua CI của PR, và `git log --first-parent` cho lịch sử theo từng PR.
- Tốt, vì cả PR hoàn tác được bằng một `git revert -m 1`.
- Xấu, vì lịch sử không tuyến tính, và từng commit của nhánh chỉ được kiểm trên nền của nhánh; trạng thái gộp được kiểm qua CI của PR.

### Rebase lên nhánh đích rồi fast-forward

- Tốt, vì lịch sử tuyến tính, và mỗi commit là trạng thái đã kiểm bằng `git rebase -x` trên nền nhánh đích mới nhất.
- Xấu, vì trên GitHub, fast-forward chỉ làm được bằng cách push thẳng vào nhánh đích, mà ruleset chặn việc đó.
- Xấu, vì trước mỗi lần gộp phải rebase và chạy lại kiểm tra trên từng commit.

### Squash

- Xấu, vì gộp nhiều thay đổi logic vào một commit, trái nguyên tắc mỗi commit làm một việc, và bỏ mất body của từng commit.
- Xấu, vì mất thông tin từng thay đổi được làm lúc nào và ai là tác giả của các commit bị gộp.

### Nút "Rebase and merge" của GitHub

- Tốt, vì không phải rebase trên máy.
- Xấu, vì luôn tạo SHA mới, đổi thông tin committer, và commit đưa vào nhánh đích không có chữ ký, do GitHub không có khoá riêng của người viết.

### Ruleset của GitHub

- Tốt, vì GitHub chặn ngay trên server: không push thẳng, không force-push, không merge khi job CI chính chưa xanh, không nhận commit thiếu chữ ký.
- Tốt, vì có cho repo public ở gói GitHub Free.
- Xấu, vì job CI mới phải được thêm vào danh sách job bắt buộc của ruleset.

### Hook trên máy chặn commit và push

- Tốt, vì báo ngay trên máy, trước khi push.
- Xấu, vì vượt được bằng `--no-verify` hay bằng một bản clone chưa cài hook, và không kiểm được CI hay chữ ký.

### Mọi job CI xanh, không bắt lượt duyệt

- Tốt, vì hợp với dự án một người bảo trì: không có lượt duyệt hình thức.
- Xấu, vì không có người thứ hai đọc thay đổi trước khi merge.

### Bắt một lượt duyệt, do một job CI tự duyệt khi các job khác xanh

- Tốt, vì đáp ứng luật bắt một lượt duyệt của ruleset.
- Xấu, vì lượt duyệt đó không thêm kiểm tra nào ngoài các job CI, và phải cho GitHub Actions quyền duyệt PR.

### Gộp phần sửa vào commit gây lỗi trước khi merge

- Tốt, vì lịch sử của nhánh chỉ chứa trạng thái đúng, mỗi commit đọc được như một thay đổi hoàn chỉnh.
- Tốt, vì `git rebase --autosquash --exec` chạy lại kiểm tra trên từng commit sau khi gộp.
- Xấu, vì viết lại commit được sửa và mọi commit sau nó, nên nhánh phải push lại bằng `--force-with-lease`, và chỉ dùng được trước khi merge.

### Thêm commit sửa lên trên

- Tốt, vì không viết lại lịch sử.
- Xấu, vì lịch sử giữ cả trạng thái sai lẫn commit vá chồng lên, dù commit sai chưa vào nhánh chính.

### Workflow tạo khi PR từ `release/X.Y.Z` hay `hotfix/X.Y.Z` được merge vào `main`

- Tốt, vì tag trỏ đúng commit merge đã qua CI, không phụ thuộc máy của người phát hành, và chỉ được tạo sau khi artifact đã build xong.
- Xấu, vì tag không mang chữ ký khoá cá nhân, và workflow cần quyền ghi nội dung repo.

### Tag annotated có chữ ký tạo trên máy rồi push

- Tốt, vì tag mang chữ ký khoá cá nhân, kiểm được bằng `git tag -v`.
- Xấu, vì phát hành phụ thuộc máy và thao tác của người phát hành, dễ gắn tag lên commit chưa qua CI, và GitHub Release cùng artifact phải tạo ở bước khác.

## Thông tin thêm

- File thực hiện quyết định: `CONTRIBUTING.md` (các mục "Kiểm tra", "Ngôn ngữ", "Quy ước commit", "Nhánh và lịch sử", "Phát hành"), `commitlint.config.mjs`, `.pre-commit-config.yaml`, `cliff.toml`, `.github/workflows/ci.yaml`, `.github/workflows/release.yaml`, `.github/dependabot.yml`; ruleset và cài đặt của repo trên GitHub. Phiên bản của commitlint, git-cliff và pre-commit thuộc ADR 0008.
- Phạm vi: chữ ký ở đây là chữ ký Git của commit và tag. Chữ ký và phiên bản của bản cập nhật OTA, của model, và khoá của thiết bị thuộc ADR 0013, ADR 0015 và ADR 0016. Cách giữ khoá ký trên từng máy không thuộc ADR này.
- Không phương án nào khác được cân nhắc cho cách đánh số phiên bản, dạng changelog và loại khoá ký (SSH hay OpenPGP).
- Chưa quyết định, kèm điều kiện đóng:
  1. Cách tính số phiên bản tiếp theo: tính tay theo bảng "Type" của CONTRIBUTING hay dùng `git-cliff --bump`. Lệnh này đọc mục `[bump]`, trong đó tuỳ chọn `breaking_always_bump_major` quyết định thay đổi không tương thích có đưa 0.y.z lên 1.0.0 hay không; `cliff.toml` hiện chưa có mục `[bump]`. Đóng khi mục "Phát hành" của CONTRIBUTING ghi cách tính, trước lần phát hành đầu tiên sau 0.1.0.
  2. Điều kiện phát hành 1.0.0: SemVer coi 1.0.0 là bản định nghĩa API công khai. Đóng bằng một ADR mới khi Mr.Ròm chốt rằng các hợp đồng công khai ở mục "Thay đổi không tương thích" của CONTRIBUTING đã ổn định.
- Nguồn:
  - [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/): `fix` ứng với PATCH, `feat` với MINOR, `!` hoặc footer `BREAKING CHANGE` với MAJOR.
  - [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): mục 4 và 5 về 0.y.z và 1.0.0; FAQ về bắt đầu từ 0.1.0 và về tiền tố `v` của tên tag.
  - [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/): các mục Added, Changed, Deprecated, Removed, Fixed, Security; changelog viết cho người đọc, không chép log commit.
  - [commitlint](https://github.com/conventional-changelog/commitlint) và [pre-commit](https://pre-commit.com/).
  - [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks): hook `no-commit-to-branch`.
  - [git-cliff: cấu hình bump](https://git-cliff.org/docs/configuration/bump).
  - [git-commit](https://git-scm.com/docs/git-commit): dòng tóm tắt không quá 50 ký tự, `--fixup`.
  - [git-rebase](https://git-scm.com/docs/git-rebase): `--autosquash`, `--exec`, và hậu quả của việc viết lại nhánh người khác đã dựa vào.
  - [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/): git-flow, và ghi chú năm 2020 của tác giả về khi nào nên dùng mô hình này.
  - [GitHub: ruleset](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets): luật cho nhánh và tag.
  - [GitHub: release immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes): bản phát hành đã công bố không đổi được tag hay tệp đính kèm.
  - [GitHub: ký commit và tag](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification).
  - [GitHub: các cách merge pull request](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github): merge commit giữ commit của nhánh; "Rebase and merge" tạo SHA mới và không có chữ ký; squash mất thông tin tác giả và thời điểm.
  - [GitHub: kích hoạt workflow từ workflow](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow): sự kiện do `GITHUB_TOKEN` tạo không kích hoạt workflow mới, trừ `workflow_dispatch` và `repository_dispatch`.
