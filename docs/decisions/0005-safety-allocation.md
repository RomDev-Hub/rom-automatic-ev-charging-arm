# 0005. Phân bổ chức năng an toàn cho phần cứng có mức an toàn

- Status: accepted
- Date: 2026-11-12
- Decision-makers: Mr.Ròm

## Bối cảnh và vấn đề

Hệ thống đưa một tay máy UR đặt trên ray tới cổng sạc của xe điện, cắm rồi rút đầu sạc, ở trạm sạc hoặc hộ gia đình. Đây là máy có chuyển động và làm việc gần nguồn điện công suất cao. Lắp ở trạm hay nhà thật thì luật an toàn máy của nơi lắp vẫn áp dụng, dù dự án phi thương mại.

Phần mềm (`robot-core`) chạy trong Docker trên Jetson hoặc PC Linux. Nó là bộ giám sát 30–50 Hz, không chạy thời gian thực; mọi vòng 500 Hz nằm trong controller UR và drive của ray. Phần mềm, HMI (`operator-ui`), perception, mạng và Docker đều có thể treo, mất kết nối hoặc chạy sai, và không phần nào trong số đó có mức an toàn.

Cần quyết định các chức năng an toàn, như dừng khẩn cấp, dừng bảo vệ (safeguard), giới hạn an toàn của tay máy và ngắt mô-men của ray, nằm ở phần nào, và phần mềm được làm gì với an toàn.

## Yếu tố quyết định

- Chức năng an toàn vẫn phải chạy đúng khi phần mềm treo, mất kết nối hoặc chạy sai, và khi host, mạng hay Docker hỏng.
- Mỗi chức năng an toàn cần mức an toàn (PL) xác định theo ISO 13849-1 và kiểm chứng được theo ISO 13849-2.
- Host không chạy kernel thời gian thực; kernel thời gian thực của Jetson mới ở mức developer preview.
- An toàn giữ nguyên khi kiến trúc phần mềm thay đổi.
- Người vận hành không được nhầm một nút trên màn hình với thiết bị dừng khẩn cấp.

## Các phương án đã xét

1. Chức năng an toàn chỉ nằm ở phần cứng có mức an toàn, mặc định dùng I/O an toàn của UR.
2. Relay hoặc PLC an toàn riêng cho mọi chức năng an toàn ngay từ đầu.
3. Giám sát an toàn bằng phần mềm trên host, tính là chức năng an toàn.
4. Perception, model ML và video làm tín hiệu an toàn.

## Kết quả quyết định

Chọn phương án 1, "Chức năng an toàn chỉ nằm ở phần cứng có mức an toàn, mặc định dùng I/O an toàn của UR", vì nó giữ được chức năng an toàn khi phần mềm, host, mạng hay Docker hỏng, điều phương án 3 và 4 không làm được, và không thêm thiết bị khi I/O an toàn của UR còn đủ như phương án 2.

Chức năng an toàn chỉ nằm ở các phần có mức an toàn sau:

- Hệ an toàn của tay máy UR, PLd Cat 3 theo công bố của UR. Giới hạn an toàn nằm trong cấu hình an toàn của UR.
- Mạch dừng khẩn cấp (E-stop) và mạch safeguard 2 kênh, nối cứng vào I/O an toàn của UR.
- Bộ ngắt mô-men an toàn (STO) của ray, nối cứng; đầu ra an toàn của UR cắt STO của ray.

Giao diện an toàn giữa các phần này theo ISO 13849-1:2023, ISO 13850 và IEC 60204-1. Mặc định dùng I/O an toàn của UR; chỉ thêm relay hoặc PLC an toàn khi số chức năng an toàn vượt số I/O an toàn của UR.

Phần mềm, HMI, perception, mạng và Docker không phải chức năng an toàn:

- Phần mềm chỉ quan sát và yêu cầu dừng. Lệnh dừng, tạm dừng, chạy lại và trạng thái `SAFE_HOLD` phục vụ vận hành, không thay cho chức năng an toàn.
- ML và video không bao giờ là chức năng an toàn hay tín hiệu an toàn.
- Nút dừng trên HMI tên là "Dừng", không gọi "Dừng khẩn cấp" hay "E-Stop". Theo ISO 13850, thiết bị dừng khẩn cấp là thiết bị vật lý; nút trên màn hình mang tên đó dễ làm người vận hành tin nhầm.

Quy tắc đi kèm:

- Chỉ nút reset vật lý xoá được chốt E-stop phần cứng, và reset không bao giờ tự cho máy chạy lại.
- Giới hạn của ứng dụng chỉ được hẹp hơn giới hạn trong cấu hình an toàn của UR và gọi là "application limits". Cấu hình trạm chỉ được thu hẹp giới hạn, không được nới.
- Dữ liệu cũ, mất kết nối hoặc adapter lỗi thì phần mềm dừng và vào `SAFE_HOLD`; khởi động lại luôn vào `SAFE_HOLD`. Mất thiết bị không bao giờ tự chuyển sang mô phỏng.
- Thao tác liên quan an toàn (cấu hình an toàn, đổi model tay máy hoặc tool, cập nhật, bật đầu ra chuyển động) cần vai trò nâng quyền, xác thực lại và ghi nhật ký kiểm toán.

**Bảo vệ dọc ray** (Status: proposed). Ray dời gốc tay máy, nên cần scanner hoặc rào dọc ray cùng STO riêng cho ray. Đây là suy luận kỹ thuật, chưa qua đánh giá rủi ro. Phần này chốt khi đánh giá rủi ro theo ISO 12100 chọn được biện pháp bảo vệ cho vùng ray và đặc tả chức năng an toàn ghi PLr cho biện pháp đó.

### Hệ quả

- Chức năng an toàn không phụ thuộc phần mềm, host, mạng hay Docker, và không đổi khi kiến trúc phần mềm đổi.
- Bảng phân bổ chức năng an toàn (SF) gán mỗi chức năng cho một trong các phần có mức an toàn ở trên. Đánh giá rủi ro và đặc tả chức năng an toàn không tính phần mềm là chức năng an toàn.
- [README](../../README.md) nêu rõ các lệnh dừng, tạm dừng, chạy lại của phần mềm không phải chức năng an toàn.
- Hãng tay máy khác UR cần adapter `ArmPort` riêng và tự kiểm chứng hệ an toàn của hãng đó.
- Sau cập nhật động tới phần mềm hay cấu hình liên quan an toàn, thiết bị ở lại `SAFE_HOLD`; kỹ sư tại chỗ chạy checklist kiểm tra rút gọn rồi mới cho chạy tự động.
- Đổi lại, số chức năng an toàn bị giới hạn bởi số I/O an toàn của UR; vượt thì phải thêm relay hoặc PLC an toàn.
- Đổi lại, camera của perception không dùng được để bảo vệ vùng nào; vùng ray cần thiết bị riêng (phần đề xuất ở trên).

### Xác nhận

- Review: thay đổi có mục đích an toàn đi thành commit riêng với scope `safety`, theo [CONTRIBUTING.md](../../CONTRIBUTING.md). Người review kiểm không chức năng an toàn nào được giao cho phần mềm, HMI, perception, mạng hay Docker, và chuỗi hiển thị trong `locales/` không gọi nút dừng trên HMI là "Dừng khẩn cấp", "E-Stop" hay "Emergency Stop".
- Test hồi quy an toàn của `robot-core` kiểm các quy tắc phần mềm ở trên: dữ liệu cũ, mất kết nối hoặc adapter lỗi thì dừng và vào `SAFE_HOLD`; khởi động lại vào `SAFE_HOLD`; mất thiết bị không chuyển sang mô phỏng; cấu hình trạm nới giới hạn bị từ chối; thao tác liên quan an toàn bị từ chối khi thiếu vai trò nâng quyền hoặc chưa xác thực lại, và mỗi lần thực hiện ghi một dòng nhật ký kiểm toán.
- Chức năng an toàn ở phần cứng được kiểm chứng bằng kế hoạch validation theo ISO 13849-2. Thiết bị chỉ được giao sau khi nghiệm thu tại chỗ.

## Ưu và nhược của từng phương án

### Chức năng an toàn chỉ nằm ở phần cứng có mức an toàn, mặc định dùng I/O an toàn của UR

- Ưu: chức năng an toàn chạy đúng khi phần mềm treo, mất kết nối hoặc chạy sai, và khi host, mạng hay Docker hỏng.
- Ưu: hệ an toàn của UR có mức PLd Cat 3 theo công bố của UR; mạch nối cứng 2 kênh và STO không đi qua phần mềm.
- Ưu: không thêm thiết bị khi I/O an toàn của UR còn đủ.
- Nhược: số chức năng an toàn bị giới hạn bởi số I/O an toàn của UR.
- Nhược: vùng ray cần thêm thiết bị bảo vệ, vì ray dời gốc tay máy.

### Relay hoặc PLC an toàn riêng cho mọi chức năng an toàn ngay từ đầu

- Ưu: có thêm I/O an toàn, không bị giới hạn bởi số I/O an toàn của UR.
- Nhược: thêm một thiết bị phải chọn, cấu hình và kiểm chứng khi chưa biết I/O an toàn của UR có thiếu hay không.
- Trung tính: vẫn là đường mở rộng của phương án 1 khi số chức năng an toàn vượt số I/O an toàn của UR.

### Giám sát an toàn bằng phần mềm trên host, tính là chức năng an toàn

- Ưu: không cần thêm phần cứng.
- Nhược: phần mềm, mạng và Docker không có mức an toàn, nên bộ giám sát chạy trên đó không tính được là chức năng an toàn.
- Nhược: host không chạy kernel thời gian thực, nên thời gian phản ứng của bộ giám sát không được bảo đảm.
- Nhược: phần mềm treo hoặc mất kết nối thì chính bộ giám sát cũng mất tác dụng.

### Perception, model ML và video làm tín hiệu an toàn

- Ưu: dùng lại camera sẵn có của perception.
- Nhược: perception là phần mềm chạy trên host, không có mức an toàn.

## Thông tin thêm

Phần đánh giá định lượng chưa làm. Trước khi làm việc với phần cứng thật và trước khi giao thiết bị phải có:

- đánh giá rủi ro theo ISO 12100;
- đặc tả chức năng an toàn kèm PLr theo ISO 13849-1;
- đặc tả dừng khẩn cấp theo ISO 13850;
- kế hoạch validation theo ISO 13849-2;
- hướng dẫn sử dụng theo IEC/IEEE 82079-1;
- quy trình nghiệm thu tại chỗ.

PLd Cat 3 là mức UR công bố cho hệ an toàn của UR. Khi chưa có PLr của từng chức năng, chưa kết luận được mức đó có đủ cho hệ thống này hay không.

Model UR dùng thật và drive của ray chưa xác định; drive được chọn phải có STO để nối cứng như trên.

Nguồn:

- [ISO 12100](https://committee.iso.org/standard/51528.html): đánh giá rủi ro và giảm rủi ro.
- [ISO 13849-1:2023](https://committee.iso.org/standard/73481.html): thiết kế phần liên quan an toàn của hệ điều khiển, PL và category.
- [ISO 13849-2](https://committee.iso.org/standard/53640.html): validation phần liên quan an toàn của hệ điều khiển.
- [ISO 13850](https://committee.iso.org/standard/59970.html): chức năng dừng khẩn cấp.
- [IEC 60204-1](https://webstore.iec.ch/en/publication/26037): thiết bị điện của máy.
- [IEC/IEEE 82079-1](https://webstore.iec.ch/en/publication/29075): hướng dẫn sử dụng.
- [Universal Robots: Safety Paper - The Standard We Set](https://www.universal-robots.com/articles/ur/safety/safety-paper-the-standard-we-set/): công bố PLd Cat 3 cho hệ an toàn của UR.
