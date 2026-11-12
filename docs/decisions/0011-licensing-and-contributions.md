# 0011. Giấy phép AGPL-3.0-or-later, thoả thuận đóng góp và tài sản phi thương mại

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Phần mềm của hệ thống tới tay người khác dưới dạng thiết bị cài sẵn hoặc bản cài. Thiết bị lắp ở trạm sạc hoặc ở nhà và chỉ nhận bản cập nhật có chữ ký (ADR 0013); giao diện vận hành chạy trong trình duyệt và làm việc với thiết bị qua mạng.

Dự án hiện phi thương mại, nhưng Mr.Ròm muốn sau này vẫn đổi được giấy phép hoặc thương mại hoá. Code và tài sản của bên thứ ba mà hệ thống dùng theo nhiều giấy phép khác nhau: phần lớn dependency theo giấy phép cho phép như MIT, BSD hay Apache-2.0; Ultralytics, thư viện dùng để train model keypoint cổng sạc, theo AGPL-3.0; một số tài sản không phải code có thể chỉ được dùng cho mục đích phi thương mại.

Mã nguồn của repo theo giấy phép nào, đóng góp được nhận với điều kiện gì, và code cùng tài sản của bên thứ ba được dùng ra sao, để dự án đáp ứng giấy phép của chính nó và của bên thứ ba mà Mr.Ròm vẫn giữ được đường đổi giấy phép hoặc thương mại hoá về sau?

## Yếu tố quyết định

- Mr.Ròm giữ được quyền đổi giấy phép hoặc thương mại hoá về sau, kể cả với phần code do người khác đóng góp.
- Khi còn phi thương mại, dự án không gánh nghĩa vụ thị trường, trong đó có việc mua giấy phép thương mại.
- Thiết bị nằm trong tay người nhận, có thể lắp tại nhà họ, và chỉ nhận bản cập nhật có chữ ký.
- Model keypoint cổng sạc được train offline bằng Ultralytics (AGPL-3.0); thiết bị chỉ chạy model đã train.
- Mỗi tài sản không phải code (dataset, model, URDF, mesh) có nguồn và giấy phép riêng.

## Các phương án đã xét

- AGPL-3.0-or-later, có thoả thuận đóng góp
- AGPL-3.0-or-later, không có thoả thuận đóng góp
- Giấy phép cho phép (MIT hoặc Apache-2.0)

## Kết quả quyết định

Chọn "AGPL-3.0-or-later, có thoả thuận đóng góp", vì thoả thuận giữ cho Mr.Ròm quyền đổi giấy phép hoặc thương mại hoá về sau dù repo nhận đóng góp của người khác, còn weights fine-tune từ checkpoint của Ultralytics, vốn thuộc AGPL, không gây vướng mắc khi chính dự án cũng theo AGPL (cách đọc giấy phép cần kiểm pháp lý, xem mục Hệ quả).

**Giấy phép của repo.** [LICENSE](../../LICENSE) ở gốc repo chứa toàn văn AGPL-3.0. Manifest của package khai định danh SPDX `AGPL-3.0-or-later`: `package.json` ở trường `license`, `pyproject.toml` ở khoá `license` của bảng `[project]` theo PEP 639.

**Mã nguồn cho người nhận.** Ai nhận thiết bị hoặc bản cài đều được truy cập repo ở đúng tag đang chạy.

- Giao diện vận hành có trang "Giới thiệu" ghi phiên bản, commit, giấy phép và chỗ lấy mã nguồn.
- Chủ thiết bị đăng ký được khoá ký của riêng mình (chế độ developer) để tự cài bản đã sửa: khi chế độ này bật, thiết bị nhận release manifest ký bằng khoá đó và ghi nhật ký kiểm toán (ADR 0013). Hướng dẫn sử dụng ghi cách làm.

**Thoả thuận đóng góp.** Trước đóng góp đầu tiên, người đóng góp ký với Mr.Ròm một thoả thuận bằng văn bản. Thoả thuận chuyển quyền tác giả của đóng góp cho Mr.Ròm, hoặc cấp cho Mr.Ròm quyền đủ rộng để sau này vẫn đổi giấy phép hoặc thương mại hoá được. Đóng góp chưa có thoả thuận thì chưa được nhận. Mục "Thoả thuận đóng góp" của [CONTRIBUTING.md](../../CONTRIBUTING.md) nêu yêu cầu này; bản đã ký lưu ngoài repo.

**Code và tài sản của bên thứ ba.** Không chép code từ dự án AGPL hay GPL vào file của dự án; code của các dự án đó chỉ được dùng qua dependency.

- Ultralytics chỉ có trong component `training/`, vốn có lockfile riêng và chỉ chạy trên máy chủ train. Thiết bị suy luận bằng ONNX Runtime (MIT) trên model đã xuất ra ONNX (ADR 0015).
- CI kê giấy phép của dependency ở chế độ chỉ cảnh báo, không làm CI thất bại.
- Tài sản không phải code (dataset, model, URDF, mesh) được kê trong `third_party/assets.yaml`, mỗi tài sản ghi nguồn, giấy phép và cờ `nc`; tài sản chỉ được dùng cho mục đích phi thương mại có `nc: true`. Văn bản giấy phép của tài sản đã dùng nằm trong `third_party/licenses/`, ví dụ BSD-3 của URDF.
- Mesh của UR cho twin 3D kiểm giấy phép riêng, tách khỏi URDF; nếu chỉ được dùng cho mục đích phi thương mại thì có `nc: true`.
- Model làm mờ mặt người và biển số được chọn trong các model có giấy phép cho phép, chạy bằng ONNX.
- URSim, bộ mô phỏng controller của UR, miễn phí nhưng không phải mã nguồn mở: chỉ dùng để test, không phát hành.

**Phạm vi phi thương mại.** Phi thương mại không làm bớt tính năng nào; dự án chỉ không gánh các nghĩa vụ thị trường:

- mua giấy phép thương mại;
- chương trình tuân thủ giấy phép nguồn mở theo OpenChain (ISO/IEC 5230);
- hồ sơ CE, CRA, RED và technical file.

An toàn, bảo mật, CI, test, phiên bản, changelog và SBOM vẫn giữ.

### Hệ quả

- Ưu: Mr.Ròm đổi được giấy phép hoặc thương mại hoá về sau mà không phải xin lại từng người đóng góp.
- Ưu: người nhận thiết bị hoặc bản cài biết phần mềm theo giấy phép gì và lấy mã nguồn của đúng bản đang chạy ở đâu.
- Nhược: weights fine-tune từ checkpoint của Ultralytics vẫn thuộc AGPL, dù thiết bị chạy chúng bằng ONNX Runtime. Với dự án AGPL thì không sao, nhưng muốn thương mại hoá sau này thì phải có Enterprise License của Ultralytics, hoặc train từ đầu một model có giấy phép cho phép. Đây là cách đọc giấy phép, cần kiểm pháp lý.
- Nhược: thiết bị lắp ở nhà được tính là "User Product" theo mục 6 của GPLv3 và AGPLv3. Vì OTA chỉ nhận bản có chữ ký, người nhận thiết bị phải có cách tự cài bản đã sửa; chế độ developer ở trên là cách đáp ứng yêu cầu đó. Đây là cách đọc giấy phép, cần kiểm pháp lý trước khi giao thiết bị.
- Nhược: trước khi giao thiết bị phải xong ba việc: hồ sơ an toàn, hướng dẫn sử dụng, nghiệm thu tại chỗ. Lắp ở trạm hay nhà thật thì luật an toàn máy và luật dữ liệu cá nhân của nơi lắp vẫn áp dụng, dù dự án phi thương mại.
- Nhược: người đóng góp phải ký thoả thuận trước đóng góp đầu tiên, và Mr.Ròm phải giữ bản đã ký.
- Nhược: bước kê giấy phép chỉ cảnh báo, nên dependency có giấy phép ngoài danh sách cho phép vẫn vào được repo nếu không ai đọc cảnh báo.
- Trung tính: cờ `nc` cho biết tài sản nào phải thay, hoặc phải có giấy phép khác, trước khi thương mại hoá.

### Xác nhận

- [LICENSE](../../LICENSE) chứa toàn văn AGPL-3.0; `README.md` ghi giấy phép `AGPL-3.0-or-later` và dẫn tới `LICENSE`; `package.json` ở gốc repo khai `"license": "AGPL-3.0-or-later"`. Người duyệt kiểm mỗi `package.json` hay `pyproject.toml` thêm sau cũng khai như vậy.
- Trong `.github/workflows/ci.yaml`, bước `Dependency licences (warning only)` kê dependency do pnpm quản lý bằng `pnpm licenses list --json`; job `python-licences` chạy `scripts/list_python_licences.py`, kê từng gói trong `robot-core/uv.lock` với giấy phép lấy từ metadata trên PyPI của đúng bản đã khoá. Cả hai in một cảnh báo cho mỗi giấy phép không có trong danh sách cho phép (biến `ALLOWED_LICENCES` của workflow) và có `continue-on-error: true`, nên không làm CI đỏ.
- `pin` và `libpinocchio` 4.1.0 được kê là BSD-2-Clause theo file `LICENSE` mà hai gói này mang, chính là file của Pinocchio ở tag v4.1.0, thay cho BSD-3-Clause trong metadata trên PyPI (ADR 0012). Khi bản đã khoá của hai gói đổi, script cảnh báo để người duyệt đọc lại file `LICENSE` của bản mới.
- Chưa có kiểm tra tự động cho các điểm sau, nên chúng được kiểm khi review: thoả thuận đã ký trước khi nhận đóng góp; Ultralytics chỉ nằm trong `training/`; không có code chép từ dự án AGPL hay GPL; mỗi tài sản mới có mục trong `third_party/assets.yaml`.
- Trước khi giao thiết bị: bản đang chạy có trang "Giới thiệu" và chế độ developer; hướng dẫn sử dụng đã có và ghi cách dùng chế độ developer; hồ sơ an toàn và nghiệm thu tại chỗ đã xong; cách đọc "User Product" đã được kiểm pháp lý.

## Ưu và nhược của từng phương án

### AGPL-3.0-or-later, có thoả thuận đóng góp

- Ưu: Mr.Ròm giữ quyền đổi giấy phép hoặc thương mại hoá với toàn bộ code, kể cả phần người khác đóng góp.
- Ưu: weights fine-tune từ checkpoint của Ultralytics, vốn thuộc AGPL, khớp với giấy phép của dự án (cách đọc cần kiểm pháp lý).
- Nhược: người đóng góp phải ký thoả thuận trước; Mr.Ròm cần một mẫu thoả thuận đã được người có chuyên môn pháp lý xem, và chỗ giữ bản đã ký.

### AGPL-3.0-or-later, không có thoả thuận đóng góp

- Ưu: người đóng góp không phải ký gì; Mr.Ròm không phải soạn mẫu thoả thuận hay giữ bản đã ký.
- Ưu: weights fine-tune từ checkpoint của Ultralytics khớp với giấy phép của dự án, như phương án trên.
- Nhược: mỗi người đóng góp giữ quyền tác giả phần mình viết và chỉ cấp phép theo AGPL-3.0-or-later, nên muốn đổi giấy phép hay thương mại hoá phải xin đồng ý của từng người, hoặc gỡ phần họ viết.

### Giấy phép cho phép (MIT hoặc Apache-2.0)

- Ưu: ai cũng được dùng, sửa và phân phối lại, kể cả trong sản phẩm đóng, nên thương mại hoá phần code của dự án không cần đổi giấy phép hay thoả thuận đóng góp.
- Nhược: weights fine-tune từ checkpoint của Ultralytics vẫn thuộc AGPL (cách đọc cần kiểm pháp lý), nên thiết bị vẫn mang một phần AGPL; muốn tránh thì phải có Enterprise License của Ultralytics hoặc train từ đầu một model có giấy phép cho phép.

## Thông tin thêm

- Quyết định liên quan: ADR 0002 (bố cục repo, gồm `training/` và `third_party/`), ADR 0010 (file lớn và dữ liệu nằm ngoài Git, `third_party/assets.yaml`), ADR 0013 (cập nhật OTA, chế độ developer), ADR 0014 (dữ liệu gửi về máy chủ và quyền riêng tư), ADR 0015 (vòng đời model: đóng gói ONNX, model card ghi giấy phép).
- Nguồn:
  - [GNU Affero General Public License v3](https://www.gnu.org/licenses/agpl-3.0.html): toàn văn giấy phép, như trong `LICENSE`; mục 6 định nghĩa "User Product" và "Installation Information", mục 13 nói về người dùng tương tác với chương trình qua mạng.
  - [Frequently Asked Questions about the GNU Licenses](https://www.gnu.org/licenses/gpl-faq.html) và [Various Licenses and Comments about Them](https://www.gnu.org/licenses/license-list.html): cách FSF giải thích GPL, AGPL và độ tương thích giữa các giấy phép.
  - [Open Source Initiative: AGPL-3.0](https://opensource.org/license/agpl-v3): AGPL-3.0 là giấy phép nguồn mở được OSI duyệt.
  - [SPDX: AGPL-3.0-or-later](https://spdx.org/licenses/AGPL-3.0-or-later.html): định danh khai trong manifest.
  - [PEP 639](https://peps.python.org/pep-0639/): khoá `license` của bảng `[project]` trong `pyproject.toml` là một biểu thức giấy phép SPDX.
  - [npm Docs: package.json, `license`](https://docs.npmjs.com/cli/v11/configuring-npm/package-json#license): trường `license` dùng định danh SPDX.
  - [pnpm licenses](https://pnpm.io/cli/licenses): lệnh CI dùng để kê giấy phép dependency.
  - [Ultralytics Licensing](https://www.ultralytics.com/license): Ultralytics cấp AGPL-3.0 và Enterprise License; trang này ghi model train bằng Ultralytics mặc định thuộc AGPL-3.0.
  - [ONNX Runtime, LICENSE](https://github.com/microsoft/onnxruntime/blob/main/LICENSE): MIT.
  - [OpenChain](https://openchainproject.org/): chương trình tuân thủ giấy phép nguồn mở, chuẩn ISO/IEC 5230.
  - Luật EU, chỉ để tham khảo các hồ sơ mà dự án không làm: [Regulation (EU) 2023/1230](https://eur-lex.europa.eu/eli/reg/2023/1230/oj/eng) về máy, [Regulation (EU) 2024/2847](https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng) (CRA), [Directive 2014/53/EU](https://eur-lex.europa.eu/eli/dir/2014/53/oj/eng) (RED).
- Chưa quy định:
  - mẫu thoả thuận đóng góp (chuyển quyền tác giả hay cấp quyền, cách ký) và nơi giữ bản đã ký: người có chuyên môn pháp lý xem mẫu trước khi có người đóng góp đầu tiên;
  - hai cách đọc giấy phép ở mục Hệ quả (weights dẫn xuất từ Ultralytics, "User Product") chưa được kiểm pháp lý, trong đó cách đọc "User Product" phải kiểm xong trước khi giao thiết bị;
  - người nhận được truy cập repo ở đúng tag bằng cách nào, và trang "Giới thiệu" ghi địa chỉ nào: cần có trước khi giao thiết bị hoặc bản cài đầu tiên;
  - kê giấy phép dependency Python của `training/`: job `python-licences` hiện chỉ đọc `robot-core/uv.lock`, thêm `training/uv.lock` khi component này có lockfile;
  - schema của `third_party/assets.yaml` ngoài nguồn, giấy phép và `nc` (ADR 0010);
  - giấy phép mesh của UR cho twin 3D (chưa kiểm) và model làm mờ mặt người, biển số (chưa chọn);
  - lý do chọn AGPL-3.0-or-later thay vì GPL-3.0 hay một giấy phép cho phép, và chọn "or-later" thay vì "only", chưa được ghi, ngoài điểm về weights dẫn xuất từ Ultralytics.
