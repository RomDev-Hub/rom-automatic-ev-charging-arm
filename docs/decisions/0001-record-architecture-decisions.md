# 0001. Ghi quyết định kiến trúc bằng MADR

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Dự án chốt nhiều quyết định trước khi viết code, như bố cục repo, kiến trúc, phân bổ chức năng an toàn, hợp đồng giao tiếp với giao diện vận hành, cập nhật OTA, dữ liệu gửi về máy chủ, môi trường dev, quy ước commit và giấy phép. Người làm sau cần biết quyết định nào đang có hiệu lực, vì sao chọn nó và đã loại những phương án nào. Các file khác cũng dẫn tới quyết định theo số: `CONTRIBUTING.md` và `scripts/check_layout.py` đã dẫn tới ADR 0002.

Ghi quyết định kiến trúc ở đâu, theo khuôn mẫu nào, và đổi một quyết định đã chốt bằng cách nào?

## Yếu tố quyết định

- Quyết định nằm trong repo, đi cùng phiên bản code mà nó áp dụng.
- Mỗi quyết định ghi lý do, các phương án đã loại và lý do loại.
- Đổi quyết định không xoá quyết định cũ: vẫn đọc lại được trước đó đã chốt gì và vì sao đổi.
- Số của một quyết định cố định, vì file khác dẫn tới quyết định theo số.
- Dùng một khuôn mẫu cộng đồng đã công bố thay vì tự đặt khuôn mẫu riêng.
- ADR viết tiếng Việt, theo mục "Ngôn ngữ" của [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Các phương án đã xét

- MADR 4.0, tiêu đề mục dịch sang tiếng Việt
- MADR 4.0, giữ tiêu đề mục tiếng Anh
- Mẫu ADR của Michael Nygard
- Không theo khuôn mẫu: lý do ghi trong body commit và issue

## Kết quả quyết định

Chọn "MADR 4.0, tiêu đề mục dịch sang tiếng Việt", vì đây là phương án duy nhất vừa có chỗ riêng cho các phương án đã loại cùng lý do loại, vừa viết được cả tiêu đề mục lẫn nội dung bằng tiếng Việt.

**Vị trí và tên file.** Mỗi quyết định là một file trong `docs/decisions/`, đặt tên `NNNN-<english-kebab-title>.md`:

- `NNNN` gồm bốn chữ số, đánh liên tiếp từ `0001`; số đã cấp không đổi và không dùng lại.
- `<english-kebab-title>` là tiêu đề ngắn bằng tiếng Anh, viết thường, các từ nối bằng dấu gạch ngang, chỉ gồm chữ cái và chữ số ASCII. Ví dụ: `0001-record-architecture-decisions.md`.

**Nội dung.** ADR viết tiếng Việt; định danh, đường dẫn, phiên bản và tên chuẩn giữ nguyên. Dòng đầu là `# NNNN. <tiêu đề tiếng Việt>`, cùng số với tên file. Ngay dưới là ba dòng metadata dạng danh sách, viết bằng tiếng Anh, trong khi MADR 4.0 đặt các trường này trong front matter YAML. Repo không dùng hai trường tuỳ chọn `consulted` và `informed` của MADR.

| Dòng metadata | MADR 4.0 | Ghi gì |
| --- | --- | --- |
| `- Status:` | `status` | một trong bốn trạng thái ở dưới |
| `- Date:` | `date` | ngày cập nhật ADR gần nhất, dạng `YYYY-MM-DD` |
| `- Decision-makers:` | `decision-makers` | người chốt quyết định |

Sau metadata là các mục, theo đúng tên và thứ tự trong bảng dưới. Mục không bắt buộc chỉ được bỏ khi không có gì để ghi, và khi bỏ thì bỏ cả tiêu đề.

| Tiêu đề trong repo | Tiêu đề MADR 4.0 | Bắt buộc |
| --- | --- | --- |
| `## Bối cảnh và vấn đề` | `## Context and Problem Statement` | có |
| `## Yếu tố quyết định` | `## Decision Drivers` | không |
| `## Các phương án đã xét` | `## Considered Options` | có |
| `## Kết quả quyết định` | `## Decision Outcome` | có |
| `### Hệ quả` | `### Consequences` | không |
| `### Xác nhận` | `### Confirmation` | không |
| `## Ưu và nhược của từng phương án` | `## Pros and Cons of the Options` | không |
| `## Thông tin thêm` | `## More Information` | không |

Câu chữ cố định của mẫu MADR cũng dịch theo:

- Mục Kết quả quyết định mở đầu bằng `Chọn "<tên phương án>", vì <lý do>` (MADR: `Chosen option: "<title>", because <justification>`).
- Mục Ưu và nhược của từng phương án có một tiêu đề `###` cho mỗi phương án, đặt đúng tên như trong mục Các phương án đã xét.
- Trong mục Hệ quả và mục Ưu và nhược của từng phương án, mỗi ý mở đầu bằng `Ưu:`, `Nhược:` hoặc `Trung tính:` (MADR: `Good, because`, `Bad, because`, `Neutral, because`).

**Trạng thái.** Dòng `Status` nhận một trong bốn giá trị:

| Giá trị | Nghĩa |
| --- | --- |
| `proposed` | đang bàn, chưa có hiệu lực |
| `accepted` | đã chốt, đang có hiệu lực |
| `superseded by ADR-NNNN` | ADR `NNNN` đã thay quyết định này |
| `rejected` | đề xuất không được chấp nhận |

Quyết định đã `accepted` chỉ đổi bằng một ADR mới thay nó, kể cả khi bỏ hẳn quyết định; vì vậy repo không dùng trạng thái `deprecated` của MADR. ADR mới nêu số của ADR nó thay ngay trong mục Bối cảnh và vấn đề. Trong cùng commit đó, ADR cũ chỉ đổi dòng `Status` thành `superseded by ADR-NNNN` và cập nhật dòng `Date`; phần còn lại giữ nguyên.

**Mục lục.** Mục lục các ADR nằm ở `docs/decisions/README.md`.

### Hệ quả

- Ưu: mỗi quyết định có một file với số cố định, nên file khác dẫn tới được bằng số.
- Ưu: chuỗi `superseded by` giữ lại mọi quyết định cũ, nên đọc ngược được trước đó đã chốt gì và vì sao đổi.
- Ưu: phương án đã loại và lý do loại nằm ngay trong ADR, không rải theo commit hay issue.
- Nhược: đổi một quyết định đã chấp nhận, dù nhỏ, cũng phải viết một ADR mới.
- Nhược: tiêu đề mục khác bản gốc tiếng Anh, người quen MADR phải tra bảng đối chiếu ở trên.
- Nhược: metadata không nằm trong front matter YAML như mẫu MADR 4.0, nên công cụ chỉ đọc front matter sẽ không thấy.

### Xác nhận

- Người duyệt mỗi thay đổi trong `docs/decisions/` kiểm: tên file đúng mẫu và lấy số kế tiếp; số ở dòng tiêu đề khớp tên file; tên và thứ tự các mục đúng bảng trên; trạng thái là một trong bốn giá trị; ADR đã chấp nhận chỉ đổi dòng `Status` và `Date` khi bị thay.
- Hook `markdownlint-cli2` chạy ở pre-commit và trên CI, kiểm cú pháp Markdown theo `.markdownlint.yaml`; hook này không kiểm khung MADR.
- Chưa có kiểm tự động cho tên file, số thứ tự, tên mục và trạng thái.

## Ưu và nhược của từng phương án

### MADR 4.0, tiêu đề mục dịch sang tiếng Việt

[Mẫu MADR 4.0.0](https://github.com/adr/madr/blob/4.0.0/template/adr-template.md), với metadata và tiêu đề mục dịch theo các bảng ở trên.

- Ưu: có mục riêng cho yếu tố quyết định, phương án đã xét, ưu nhược của từng phương án và cách xác nhận.
- Ưu: MADR đã quy ước thư mục `docs/decisions` và tên file `NNNN-title-with-dashes.md` với số liên tiếp, repo không phải tự đặt.
- Ưu: tiêu đề mục cùng thứ tiếng với nội dung.
- Nhược: nhiều mục hơn mẫu của Nygard, viết tốn công hơn.
- Nhược: tiêu đề mục khác bản gốc, cần bảng đối chiếu.

### MADR 4.0, giữ tiêu đề mục tiếng Anh

- Ưu: khớp nguyên văn mẫu MADR 4.0, người quen MADR đọc được ngay.
- Nhược: tiêu đề tiếng Anh xen nội dung tiếng Việt trong cùng một file, trong khi ADR là tài liệu viết tiếng Việt.

### Mẫu ADR của Michael Nygard

Mẫu trong bài [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html) (2011), gồm năm phần: Title, Context, Decision, Status, Consequences.

- Ưu: ngắn, và là mẫu đi cùng bài viết đã làm phổ biến khái niệm ADR.
- Nhược: không có mục riêng cho các phương án đã xét và ưu nhược của chúng, nên phương án bị loại dễ không được ghi.

### Không theo khuôn mẫu: lý do ghi trong body commit và issue

- Ưu: không thêm file hay quy ước; body commit đã có label `Why` và `Rejected`.
- Nhược: lý do rải theo nhiều commit, không có chỗ nào cho biết quyết định nào đang có hiệu lực.
- Nhược: issue nằm trên GitHub, không đi theo bản clone hay tag của repo.

## Thông tin thêm

- Nguồn:
  - [adr.github.io](https://adr.github.io/): định nghĩa ADR và nhật ký quyết định (decision log).
  - [adr.github.io/madr](https://adr.github.io/madr/): MADR, thư mục `docs/decisions`, tên file `NNNN-title-with-dashes.md` với số liên tiếp.
  - [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions.html): đánh số liên tiếp, không dùng lại số, giữ quyết định cũ và đánh dấu là bị thay.
  - [Google developer documentation style guide, tên file](https://developers.google.com/style/filenames): tên file viết thường, nối từ bằng dấu gạch ngang, chỉ dùng chữ cái và chữ số ASCII.
  - [POSIX.1-2024, mục 3.265](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap03.html): bộ ký tự tên file portable gồm chữ cái, chữ số ASCII và `.`, `_`, `-`.
- Chưa quy định:
  - mục lục `docs/decisions/README.md` ghi những gì và cập nhật lúc nào;
  - sửa lỗi chính tả hay link hỏng, không đổi nghĩa, trong ADR đã chấp nhận có cần ADR mới hay không.
