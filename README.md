# Tay máy sạc xe điện tự động

Hệ thống quản lý và điều khiển cánh tay robot để tự động sạc cho xe điện. Camera nhận diện xe và cổng sạc, hệ thống đưa tay máy tới đúng vị trí, cắm đầu sạc, rút ra khi sạc xong rồi đưa tay về chỗ cũ. Hệ thống làm việc với nhiều model tay máy, dùng được ở trạm sạc lẫn hộ gia đình.

## Trạng thái

Đang thử nghiệm, chưa có bản phát hành. Đọc khuyến cáo trong [SECURITY.md](SECURITY.md) trước khi dùng.

## Cảnh báo an toàn

Đây là máy có chuyển động và làm việc gần nguồn điện công suất cao. Phần mềm có các lệnh dừng, tạm dừng, chạy lại và đưa máy về trạng thái chờ an toàn để phục vụ vận hành, nhưng các lệnh này không phải chức năng an toàn: phần mềm có thể treo, mất kết nối hoặc chạy sai. Vì vậy, **dừng khẩn cấp (Emergency Stop)** và mọi chức năng an toàn phải nằm ở phần cứng: hệ an toàn của tay máy, mạch dừng khẩn cấp nối cứng và bộ ngắt mô-men an toàn (STO) của ray. Không chạy phần mềm này với thiết bị thật khi chưa có đánh giá rủi ro và nghiệm thu tại chỗ.

## Đóng góp

Môi trường làm việc, cách kiểm tra và quy ước commit nằm ở [CONTRIBUTING.md](CONTRIBUTING.md).

## Giấy phép

[AGPL-3.0-or-later](LICENSE).
