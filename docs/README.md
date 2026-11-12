# Tài liệu

## Bắt đầu đọc

1. [README](../README.md) ở gốc repo: hệ thống làm gì, trạng thái hiện tại và cảnh báo an toàn.
2. [Mục lục ADR](decisions/README.md), trước hết bốn quyết định về bố cục, kiến trúc, chuyển động và an toàn: ADR 0002 (bố cục repo, ranh giới thành phần, thuật ngữ), ADR 0003 (kiến trúc), ADR 0004 (chuyển động và lực chạy trên controller UR) và ADR 0005 (phân bổ chức năng an toàn).
3. [Thuật ngữ](glossary.md), để tra nghĩa của các từ dùng trong tài liệu và mã.
4. [CONTRIBUTING.md](../CONTRIBUTING.md) trước khi đóng góp: môi trường làm việc, kiểm tra, ngôn ngữ, bố cục thư mục và quy ước commit.

## Nội dung của `docs/`

| Đường dẫn | Chứa |
| --- | --- |
| [`decisions/`](decisions/) | Quyết định kiến trúc (ADR) theo [MADR 4.0](https://adr.github.io/madr/), mỗi quyết định một file. Mục lục và cách thêm ADR ở [decisions/README.md](decisions/README.md). |
| [`requirements/`](requirements/) | Requirement của sản phẩm, mỗi requirement có ID. |
| [`safety/`](safety/) | Tài liệu an toàn. ADR 0005 kê các tài liệu an toàn phải có trước khi làm việc với phần cứng thật và trước khi giao thiết bị. |
| [`architecture/`](architecture/) | Tài liệu kiến trúc. Container theo mô hình C4 luôn ghi là "C4 container" để không nhầm với Docker container. |
| [`verification/`](verification/) | Tài liệu kiểm chứng. Test tự động nằm cạnh mã: `robot-core/tests/` và các file `*.test.tsx` trong `operator-ui/src/`. |
| [`manual/`](manual/) | Hướng dẫn sử dụng theo [IEC/IEEE 82079-1](https://webstore.iec.ch/en/publication/29075), gồm cả cách dùng chế độ developer (ADR 0011, ADR 0013). |
| [`glossary.md`](glossary.md) | Thuật ngữ, mỗi mục có tiếng Việt và tiếng Anh. |

Thư mục chỉ có `.gitkeep` là chỗ giữ sẵn, chưa có tài liệu. Hợp đồng giao tiếp giữa HMI và `robot-core` (OpenAPI, AsyncAPI, JSON Schema) nằm ở [`contracts/`](../contracts/), ngoài `docs/` (ADR 0006).
