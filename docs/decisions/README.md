# Quyết định kiến trúc

Mỗi quyết định kiến trúc (ADR) là một file trong thư mục này, viết theo [MADR 4.0](https://adr.github.io/madr/) với tiêu đề mục dịch sang tiếng Việt.

## Mục lục

| Số | Tiêu đề | Status | Date |
| --- | --- | --- | --- |
| 0001 | [Ghi quyết định kiến trúc bằng MADR](0001-record-architecture-decisions.md) | accepted | 2026-11-12 |
| 0002 | [Bố cục repo, ranh giới thành phần và thuật ngữ](0002-repository-layout.md) | accepted | 2026-11-12 |
| 0003 | [Kiến trúc modular monolith Python theo ports/adapters](0003-architecture-modular-monolith.md) | accepted | 2026-11-12 |
| 0004 | [Chuyển động và lực chạy trên controller UR, ArmPort nhận lệnh segment](0004-motion-on-controller.md) | accepted | 2026-11-12 |
| 0005 | [Phân bổ chức năng an toàn cho phần cứng có mức an toàn](0005-safety-allocation.md) | accepted | 2026-11-12 |
| 0006 | [Hợp đồng giao tiếp HMI: REST, một kênh WSS, lỗi theo RFC 9457](0006-hmi-contract.md) | accepted | 2026-11-12 |
| 0007 | [Dữ liệu runtime nằm trong volume](0007-runtime-data-in-volumes.md) | accepted | 2026-11-12 |
| 0008 | [Môi trường dev ba mức và phiên bản công cụ](0008-dev-environment-and-tool-versions.md) | accepted | 2026-11-12 |
| 0009 | [Commit theo Conventional Commits, phiên bản theo SemVer, changelog theo Keep a Changelog](0009-commits-versioning-changelog.md) | accepted | 2026-11-12 |
| 0010 | [File lớn và dữ liệu nằm ngoài Git](0010-large-files-and-data.md) | accepted | 2026-11-12 |
| 0011 | [Giấy phép AGPL-3.0-or-later, thoả thuận đóng góp và tài sản phi thương mại](0011-licensing-and-contributions.md) | accepted | 2026-11-12 |
| 0012 | [Tay máy đa năng](0012-multi-arm-support.md) | accepted | 2026-11-12 |
| 0013 | [Cập nhật OTA cho container và hệ điều hành](0013-ota-updates.md) | accepted | 2026-11-12 |
| 0014 | [Gửi khung hình đã làm mờ về máy chủ khi có đồng ý](0014-data-upload-and-privacy.md) | accepted | 2026-11-12 |
| 0015 | [Vòng đời model nhận dạng: train offline, kiểm trên tập test cố định, đóng gói có chữ ký](0015-model-lifecycle.md) | accepted | 2026-11-12 |
| 0016 | [Danh tính thiết bị, khoá ký và hỗ trợ từ xa](0016-device-identity-and-keys.md) | accepted | 2026-11-12 |

Cột Status và cột Date chép từ dòng `Status` và dòng `Date` của từng ADR. Một số ADR đã chấp nhận còn phần riêng ghi `Status: proposed`; điều kiện đóng của phần đó ghi ngay tại chỗ.

## Thêm hoặc thay ADR

Quy tắc đầy đủ nằm ở [ADR 0001](0001-record-architecture-decisions.md); tóm tắt:

1. Lấy số kế tiếp, gồm bốn chữ số. Số đã cấp không đổi và không dùng lại.
2. Đặt tên file `NNNN-<english-kebab-title>.md`: tiêu đề ngắn bằng tiếng Anh, viết thường, các từ nối bằng dấu gạch ngang, chỉ gồm chữ cái và chữ số ASCII.
3. Viết tiếng Việt; định danh, đường dẫn, phiên bản và tên chuẩn giữ nguyên. Dòng đầu là `# NNNN. <tiêu đề tiếng Việt>`, cùng số với tên file. Ngay dưới là ba dòng metadata bằng tiếng Anh: `- Status:`, `- Date:` (ngày cập nhật gần nhất, dạng `YYYY-MM-DD`) và `- Decision-makers:`.
4. Viết các mục theo đúng tên và thứ tự trong bảng của ADR 0001; mục không bắt buộc chỉ bỏ khi không có gì để ghi, và khi bỏ thì bỏ cả tiêu đề. Mục Kết quả quyết định mở đầu bằng `Chọn "<tên phương án>", vì <lý do>`. Mục Ưu và nhược của từng phương án có một tiêu đề `###` cho mỗi phương án, đúng tên như trong mục Các phương án đã xét. Mỗi ý trong mục Hệ quả và mục Ưu và nhược của từng phương án mở đầu bằng `Ưu:`, `Nhược:` hoặc `Trung tính:`.
5. Dòng `Status` nhận một trong bốn giá trị: `proposed` (đang bàn, chưa có hiệu lực), `accepted` (đã chốt, đang có hiệu lực), `superseded by ADR-NNNN` (ADR `NNNN` đã thay quyết định này), `rejected` (đề xuất không được chấp nhận).
6. Quyết định đã `accepted` chỉ đổi bằng một ADR mới thay nó, kể cả khi bỏ hẳn quyết định. ADR mới nêu số của ADR bị thay trong mục Bối cảnh và vấn đề. Trong cùng commit, ADR bị thay chỉ đổi dòng `Status` thành `superseded by ADR-NNNN` và cập nhật dòng `Date`; phần còn lại giữ nguyên.
7. Commit theo mục "Quy ước commit" của [CONTRIBUTING.md](../../CONTRIBUTING.md).
