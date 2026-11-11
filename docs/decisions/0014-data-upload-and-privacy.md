# 0014. Gửi khung hình đã làm mờ về máy chủ khi có đồng ý

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Thiết bị dùng camera để nhận dạng xe và cổng sạc. Model keypoint cổng sạc được train offline trên máy chủ train, rồi mới chạy trên thiết bị bằng ONNX Runtime (ADR 0015). Muốn model tốt lên đúng ở những chỗ nó còn sai, máy chủ train cần khung hình của chính các ca khó ở hiện trường: lần nhận dạng kém tin cậy, lần cắm thất bại hoặc phải thử lại. Những khung đó chỉ có trên thiết bị.

Camera nhìn vào bay sạc, nên khung hình có thể chứa mặt người và biển số xe. Thiết bị được lắp ở trạm sạc hoặc ở nhà. Dự án phi thương mại, nhưng thiết bị lắp ở trạm hay nhà thật vẫn chịu luật dữ liệu cá nhân của nơi lắp.

Thiết bị được gửi gì về máy chủ và khi nào, khung hình phải được xử lý ra sao trước khi lưu và gửi, dữ liệu được giữ bao lâu trên thiết bị và trên máy chủ, để có dữ liệu train mà vẫn bảo vệ người và xe xuất hiện trong khung?

## Yếu tố quyết định

- Máy chủ train cần khung hình của các ca khó ở hiện trường, để model tốt lên ở đúng các ca đó.
- Model mới chỉ tới thiết bị sau khi qua đánh giá trên tập test cố định và được đóng gói kèm SHA-256 và chữ ký; việc train chạy trên máy chủ train, không chạy trên thiết bị (ADR 0015).
- Mặt người và biển số không được lưu hay gửi đi ở dạng nhận ra được.
- Việc gửi phải do người tại chỗ chủ động bật: mặc định không gửi gì, mỗi lần bật để lại dấu vết, và thu hồi được.
- Chỉ gửi và giữ lượng dữ liệu cần cho việc train, trong thời hạn có giới hạn.
- Thiết bị không mở cổng nào nhận kết nối từ WAN; đường truyền từ trạm về máy chủ có thể đứt giữa chừng.
- Thiết bị lắp ở trạm hay nhà thật chịu luật dữ liệu cá nhân của nơi lắp, dù dự án phi thương mại.

## Các phương án đã xét

- Gửi có chọn lọc khi có đồng ý, làm mờ trên thiết bị
- Gửi mọi khung chưa làm mờ, chọn lọc và làm mờ trên máy chủ
- Học ngay trên thiết bị, không gửi dữ liệu
- Không gửi dữ liệu nào về máy chủ

## Kết quả quyết định

Chọn "Gửi có chọn lọc khi có đồng ý, làm mờ trên thiết bị", vì đây là phương án duy nhất vừa đưa được khung hình của các ca khó tới máy chủ train, nơi model được train offline và đánh giá trên tập test cố định, vừa không để mặt người hay biển số chưa làm mờ bị ghi xuống đĩa hay rời thiết bị.

- Đồng ý:
  - mặc định tắt; khi chưa bật, thiết bị không chọn và không gửi khung nào;
  - người có vai trò bảo trì (kỹ sư tại chỗ) bật trên giao diện vận hành (HMI), chọn phạm vi bay và khoảng thời gian; chỉ khung thuộc phạm vi và khoảng thời gian đó mới được chọn để gửi;
  - mỗi lần bật được ghi vào nhật ký kiểm toán: ai bật, lúc nào, phạm vi nào;
  - đồng ý thu hồi được.
- Làm mờ trên thiết bị:
  - thiết bị phát hiện mặt người và biển số trong khung, làm mờ rồi mới ghi khung xuống đĩa;
  - bộ làm mờ không chạy được, hoặc không chắc chắn về kết quả, thì khung bị bỏ: không ghi xuống đĩa, không gửi;
  - model làm mờ phải có giấy phép cho phép và chạy bằng ONNX Runtime; model cụ thể được chọn theo giấy phép và độ chính xác.
    - Status: proposed, riêng việc chọn model cụ thể.
    - Phần này đóng khi model được chọn lúc hiện thực `robot-core/src/robot_core/harvest/` và được kê trong `third_party/assets.yaml` cùng nguồn và giấy phép (ADR 0010). Tại ngày ghi ADR, model chưa được chọn.
- Chọn khung:
  - thiết bị chỉ chọn khung có kết quả nhận dạng kém tin cậy, khung của lần cắm thất bại hoặc phải thử lại, cộng một mẫu ngẫu nhiên nhỏ mỗi ngày, có mức trần;
  - khung được cắt về vùng cổng sạc khi cắt được.
- Lưu trên thiết bị:
  - khung đã làm mờ chờ gửi nằm trong volume `ev-arm-harvest`, mount tại `/var/lib/ev-arm/harvest` (ADR 0007);
  - khung bị xoá sau khi gửi thành công; khung chưa gửi được nằm trên thiết bị tối đa 30 ngày.
- Truyền:
  - thiết bị chủ động gửi lên máy chủ qua HTTPS, không mở cổng nào nhận kết nối từ WAN;
  - kết nối dùng TLS 1.3, thiết bị xác thực bằng chứng chỉ thiết bị (mTLS); chứng chỉ do CA của dự án cấp (ADR 0016);
  - gói dữ liệu theo JSON Schema trong `contracts/schemas/`;
  - đường truyền đứt giữa chừng thì gửi tiếp được, không phải gửi lại từ đầu;
  - việc gửi có giới hạn băng thông.
- Máy chủ (ngoài phạm vi repo; áp dụng cho nơi nhận, lưu và gán nhãn dữ liệu):
  - chỉ những người được chỉ định mới truy cập được dữ liệu;
  - dữ liệu mặc định được lưu 24 tháng;
  - dữ liệu được xoá theo yêu cầu, theo thiết bị, trạm hoặc khoảng thời gian, kể cả bản đã gán nhãn;
  - dữ liệu đã xoá không được dùng cho lần train sau; model đã train thì không gỡ dữ liệu ra được, và chính sách dữ liệu ghi rõ điều này;
  - việc gán nhãn dùng CVAT (mã nguồn mở, giấy phép MIT) chạy trên máy chủ.
- Thời hạn 30 ngày trên thiết bị và 24 tháng trên máy chủ là lựa chọn của dự án; không có chuẩn nào quy định các con số này.
- Đánh giá pháp lý: chưa có. ADR này không kết luận luật nào áp dụng ở nơi lắp, cũng không kết luận các biện pháp trên đã đủ theo luật đó. Thao tác bật của kỹ sư tại chỗ có đủ làm cơ sở pháp lý để xử lý ảnh của người xuất hiện trong khung hay không, khi không có bước hỏi ý từng người, cũng thuộc phần này. Các quy định tham khảo nằm ở mục Thông tin thêm.
  - Status: proposed.
  - Phần này đóng khi người có chuyên môn pháp lý đã xem xét quyết định này theo luật dữ liệu cá nhân của nơi lắp.

### Hệ quả

- Ưu: khung chưa làm mờ không được ghi xuống đĩa hay gửi đi; chỉ bản đã làm mờ mới vào volume `ev-arm-harvest`.
- Ưu: khi chưa ai bật, không có khung nào rời thiết bị; mỗi lần bật để lại dấu vết trong nhật ký kiểm toán, và đồng ý thu hồi được.
- Ưu: lượng dữ liệu gửi đi nhỏ và tập trung vào các ca model còn sai.
- Ưu: model vẫn được train offline và đánh giá trên tập test cố định trước khi tới thiết bị.
- Nhược: khung bị bỏ khi bộ làm mờ không chắc chắn, nên dataset thiếu một phần khung của chính các ca khó.
- Nhược: thiết bị phải chạy thêm model làm mờ, bên cạnh model nhận dạng.
- Nhược: model đã train không gỡ được dữ liệu đã xoá; yêu cầu xoá chỉ có hiệu lực với dữ liệu đang lưu và các lần train sau.
- Nhược: các quy định phía máy chủ (người truy cập, thời hạn lưu, xoá theo yêu cầu) nằm ngoài repo, nên test và CI của repo không kiểm được.
- Trung tính: định dạng gói dữ liệu upload là hợp đồng công khai theo mục "Thay đổi không tương thích" của [CONTRIBUTING.md](../../CONTRIBUTING.md); thay đổi không tương thích phải đánh dấu bằng `!` và footer `BREAKING CHANGE:`.

### Xác nhận

- Test của `harvest/` kiểm từng quy tắc phía thiết bị:
  - khi chưa bật đồng ý, không có khung nào được ghi vào `ev-arm-harvest` hay được gửi;
  - khung ngoài phạm vi bay hoặc khoảng thời gian đã bật không được chọn;
  - bộ làm mờ lỗi hoặc không chắc chắn thì khung bị bỏ, không có gì được ghi xuống đĩa;
  - số khung của mẫu ngẫu nhiên trong một ngày không vượt mức trần;
  - khung bị xoá sau khi gửi thành công, và không nằm trên thiết bị quá 30 ngày;
  - gói dữ liệu khớp JSON Schema trong `contracts/schemas/`;
  - đường truyền bị ngắt giữa chừng thì lần gửi sau tiếp tục từ chỗ dừng.
- Test API: chỉ vai trò bảo trì bật được đồng ý; mỗi lần bật thêm một dòng nhật ký kiểm toán ghi người bật, thời điểm và phạm vi.
- Phía máy chủ nằm ngoài repo; repo không có kiểm tra nào cho người truy cập, thời hạn 24 tháng hay việc xoá theo yêu cầu.
- Tại ngày ghi ADR, `harvest/` chưa có code, nên chưa có test nào ở trên.

## Ưu và nhược của từng phương án

### Gửi có chọn lọc khi có đồng ý, làm mờ trên thiết bị

Mô tả đầy đủ ở mục Kết quả quyết định.

- Ưu: chỉ khung đã làm mờ và cần cho việc train mới rời thiết bị.
- Ưu: việc gửi chỉ chạy khi người có vai trò bảo trì bật tại chỗ, theo bay và khoảng thời gian, có nhật ký kiểm toán, và thu hồi được.
- Ưu: giữ được quy trình train offline, đánh giá trên tập test cố định rồi mới triển khai.
- Nhược: thiết bị phải chạy thêm model làm mờ.
- Nhược: khung bị bỏ khi bộ làm mờ không chắc chắn, nên dataset thiếu một phần ca khó.
- Nhược: cần một máy chủ nhận dữ liệu, cùng quy định về người truy cập, thời hạn lưu và xoá ở phía máy chủ.

### Gửi mọi khung chưa làm mờ, chọn lọc và làm mờ trên máy chủ

Thiết bị gửi mọi khung camera ghi được; máy chủ chọn khung cần cho việc train và làm mờ trước khi gán nhãn.

- Ưu: máy chủ có đủ khung để chọn, kể cả những khung mà bộ làm mờ trên thiết bị sẽ bỏ.
- Ưu: thiết bị không phải chạy model làm mờ.
- Nhược: mặt người và biển số chưa làm mờ nằm trên đĩa thiết bị, đi qua mạng và nằm trên máy chủ cho tới khi được xử lý.
- Nhược: gửi và lưu nhiều hơn hẳn lượng khung cần cho việc train.

### Học ngay trên thiết bị, không gửi dữ liệu

Model tự cập nhật trên thiết bị từ khung hình nó gặp khi chạy.

- Ưu: khung hình không rời thiết bị.
- Nhược: model mới được dùng ngay mà không qua đánh giá trên tập test cố định.
- Nhược: model đổi ngay ngoài hiện trường, không qua đóng gói kèm SHA-256 và chữ ký, cũng không triển khai lần lượt từng thiết bị (ADR 0015).
- Nhược: thiết bị phải mang cả phần train, vốn chỉ chạy trên máy chủ train (`training/`).

### Không gửi dữ liệu nào về máy chủ

- Ưu: không có khung hình nào rời thiết bị.
- Ưu: không cần máy chủ nhận dữ liệu, đường truyền hay quy định lưu trữ.
- Nhược: máy chủ train không có khung hình của các ca khó ở hiện trường, nên model không học được từ chính những chỗ nó còn sai.

## Thông tin thêm

- Phạm vi: ADR này quy định khung hình gửi về máy chủ để train. Quy tắc làm mờ trước khi ghi xuống đĩa áp dụng cho khung chờ gửi; ADR này không quy định bản ghi MCAP trong `ev-arm-recordings` (ADR 0007), báo tình trạng thiết bị về máy chủ, hay hỗ trợ từ xa (ADR 0016).
- ADR liên quan: 0007 (dữ liệu runtime nằm trong volume), 0010 (file lớn và dữ liệu nằm ngoài Git), 0015 (vòng đời model), 0016 (danh tính thiết bị, khoá ký, hỗ trợ từ xa).
- Nguồn:
  - [RFC 9846, The Transport Layer Security (TLS) Protocol Version 1.3](https://www.rfc-editor.org/info/rfc9846): đặc tả TLS 1.3, thay RFC 8446.
  - [JSON Schema](https://json-schema.org/specification): định dạng dùng để mô tả gói dữ liệu upload trong `contracts/schemas/`.
- Quy định tham khảo cho phần đánh giá pháp lý; dự án chưa kết luận quy định nào áp dụng:
  - [Quy định (EU) 2016/679 (GDPR)](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng): Điều 5(1)(c), dữ liệu cá nhân chỉ ở mức cần thiết cho mục đích xử lý; Điều 5(1)(e), không giữ ở dạng nhận diện được người liên quan lâu hơn mức cần thiết; Điều 7(3), quyền rút lại đồng ý bất cứ lúc nào; Điều 17, quyền được xoá; Điều 25, bảo vệ dữ liệu theo thiết kế và theo mặc định; Điều 32, an toàn khi xử lý, gồm mã hoá dữ liệu cá nhân.
  - [Quy định (EU) 2024/2847 (Cyber Resilience Act)](https://eur-lex.europa.eu/eli/reg/2024/2847/oj/eng): Phụ lục I, Phần I, (2)(e), bảo vệ tính bí mật của dữ liệu khi lưu và khi truyền, ví dụ bằng mã hoá; (2)(g), chỉ xử lý dữ liệu ở mức cần thiết cho mục đích của sản phẩm. Quy định này có áp dụng cho một dự án phi thương mại hay không cũng thuộc phần đánh giá pháp lý.
- Chưa quy định:
  - con số mức trần của mẫu ngẫu nhiên mỗi ngày, ngưỡng để coi kết quả nhận dạng là kém tin cậy, ngưỡng để coi bộ làm mờ là không chắc chắn, và con số giới hạn băng thông; chốt khi hiện thực `harvest/`;
  - đồng ý được bật thay cho ai (chủ trạm, chủ nhà) và sự đồng ý đó được ghi nhận thế nào ngoài nhật ký kiểm toán;
  - khi đồng ý bị thu hồi hoặc hết khoảng thời gian đã chọn, khung đã lưu mà chưa gửi được giữ lại, gửi tiếp hay xoá; ai được thu hồi đồng ý; việc thu hồi có ghi nhật ký kiểm toán không;
  - các trường của gói dữ liệu upload; chốt khi viết schema trong `contracts/schemas/`;
  - ai được gửi yêu cầu xoá và qua kênh nào; yêu cầu xoá của một người cụ thể xuất hiện trong khung được xử lý ra sao, khi việc xoá mới được nêu theo thiết bị, trạm hoặc khoảng thời gian;
  - chính sách dữ liệu, nơi ghi rằng model đã train không gỡ được dữ liệu, nằm ở đâu và ai giữ;
  - nơi đặt máy chủ, và cách cấp, thu hồi quyền truy cập cho người được chỉ định; phần này ở phía máy chủ, ngoài repo.
