# Danh sách hazard khởi đầu

Đây là danh sách hazard khởi đầu của hệ thống, lập trước đánh giá rủi ro theo [ISO 12100](https://committee.iso.org/standard/51528.html). Đánh giá rủi ro đó chưa làm. Nó phải do người có năng lực về an toàn máy thực hiện, trên phần cứng thật: model UR, drive và kết cấu ray, tool, cáp, bộ sạc và nơi lắp đã chốt.

- Hazard là nguồn có thể gây tổn hại (ISO 12100). Danh sách nêu mười hazard đáng kể nhất thấy được từ thiết kế hiện tại; nó chưa đủ, và đánh giá rủi ro phải bổ sung.
- Danh sách không ước lượng mức nghiêm trọng hay xác suất, không gán PLr cho chức năng nào, và không tuyên bố hệ thống đạt chứng nhận hay phù hợp với chuẩn nào.
- Chức năng an toàn chỉ nằm ở phần cứng có mức an toàn; phần mềm chỉ quan sát và yêu cầu dừng ([ADR 0005](../decisions/0005-safety-allocation.md)).

## Phạm vi

- Hệ thống: một tay máy UR đặt trên ray, mang tool có đầu sạc nối cáp tới bộ sạc; host chạy `robot-core` bằng Docker và phục vụ HMI; camera của perception; một cell có một hoặc nhiều bay; lắp ở trạm sạc hoặc ở nhà.
- Bộ sạc, gồm cả cáp và đầu sạc, là thiết bị riêng có chức năng an toàn điện của chính nó; danh sách xét các hazard phát sinh khi hệ thống cầm, cắm và rút đầu sạc.
- Người có thể bị ảnh hưởng: tài xế và người đi cùng xe; người qua lại ở trạm; người trong nhà, kể cả trẻ em, khi lắp ở nhà; người vận hành; kỹ sư tại chỗ (vai trò bảo trì); người cứu hộ.
- Pha đã xét: vận hành tự động (chu trình sạc, điều phối nhiều bay), phục hồi sau lỗi, chạy tay và bảo trì, khởi động, khởi động lại và cập nhật; tên trạng thái của máy trạng thái mission ghi trong ngoặc. Chưa xét: vận chuyển, lắp đặt, chạy thử lần đầu, vệ sinh, tháo dỡ.

## Cách đọc

Mỗi hazard ghi tình huống và pha, tổn hại có thể, biện pháp hiện có hoặc dự kiến theo phần mang biện pháp, và vùng requirement liên quan.

| Phần mang | Gồm |
| --- | --- |
| Hệ an toàn UR | giới hạn an toàn trong cấu hình an toàn của tay máy UR và các kiểu dừng của UR; PLd Cat 3 theo công bố của UR |
| Mạch cứng | mạch dừng khẩn cấp và mạch safeguard 2 kênh nối cứng vào I/O an toàn của UR, cùng thiết bị bảo vệ cấp tín hiệu cho mạch safeguard |
| STO ray | STO của drive ray, nối cứng; đầu ra an toàn của UR cắt STO này |
| Bộ sạc | chức năng an toàn điện của bộ sạc, thiết bị riêng ngoài hệ thống |
| Kết cấu | kết cấu cơ khí và điện của cell, tool và đường dẫn cáp |
| Quy trình | hướng dẫn sử dụng, quy trình tại chỗ (tiếp cận, khoá năng lượng, cứu hộ), đào tạo, nghiệm thu |
| Phần mềm (quan sát) | `robot-core`, HMI và perception quan sát, yêu cầu dừng, chặn lệnh; không phải chức năng an toàn |

- Ba phần mang đầu bảng là các phần có mức an toàn của ADR 0005.
- `(đề xuất)` sau tên phần mang đánh dấu phần ADR 0005 còn để ngỏ; `(ứng viên)` đánh dấu biện pháp cần xét trong đánh giá rủi ro; biện pháp không đánh dấu đã có trong thiết kế. Chưa biện pháp nào được hiện thực hay kiểm chứng trên phần cứng thật.
- Vùng requirement ghi theo mã vùng trong ID `REQ-<vùng>-NNN` của `docs/requirements/`.

## HZ-01. Tay máy va chạm hoặc kẹp người trong vùng làm việc cạnh xe

- Tình huống và pha:
  - Vận hành tự động, từ lúc tay máy rời tư thế cất tới khi về lại (`S7_ARM_TRANSIT` tới `S19_RETRACT_STOW`), và khi phục hồi (`ABORT_UNPLUG`, `ABORT_RETRACT`): tài xế hay người đi cùng chưa rời xe hoặc quay lại xe; người qua lại, trẻ em hay vật nuôi đi vào bay; một người đứng giữa tay máy và thân xe, cột, tường hay xe ở bay bên cạnh.
  - Chạy tay và bảo trì (`MAINTENANCE`): kỹ sư đứng trong tầm với của tay máy, hoặc chạy tay từ chỗ không nhìn thấy tay máy.
  - Perception không thấy người vì camera bị che, chói hay tối, hoặc vì model nhận dạng sai.
- Tổn hại có thể: va đập; kẹp hay nghiền giữa tay máy, tool hoặc đầu sạc với thân xe hay vật cố định; chấn thương đầu, thân, tay chân; cùng một lực gây tổn hại nặng hơn cho trẻ em.
- Biện pháp:
  - Hệ an toàn UR: giới hạn an toàn trong cấu hình an toàn của UR, như vị trí và tốc độ khớp, mặt phẳng an toàn cho TCP và tool, tốc độ TCP, lực, công suất, động lượng, thời gian và quãng đường dừng; danh mục chính xác theo model và phiên bản phần mềm của UR được chọn. Giới hạn của ứng dụng chỉ được hẹp hơn.
  - Mạch cứng: thiết bị dừng khẩn cấp vật lý; số thiết bị và chỗ đặt chốt trong đặc tả dừng khẩn cấp theo [ISO 13850](https://committee.iso.org/standard/59970.html). Theo ISO 12100, dừng khẩn cấp là biện pháp bảo vệ bổ sung, không thay cho bảo vệ vùng làm việc; ở trạm chạy tự động có thể không có ai đứng cạnh để bấm.
  - Mạch cứng (ứng viên): thiết bị bảo vệ có mức an toàn, như scanner laser an toàn, giám sát vùng làm việc cạnh xe và cấp tín hiệu cho mạch safeguard; người vào vùng cảnh báo thì UR chuyển sang bộ giới hạn chặt hơn, vào vùng bảo vệ thì tay máy dừng. Khoảng cách đặt thiết bị tính theo [ISO 13855](https://committee.iso.org/standard/80590.html), chuẩn này chỉ dùng để bảo vệ người từ 14 tuổi trở lên; nơi lắp có trẻ em thì đánh giá rủi ro phải xét riêng.
  - Hệ an toàn UR (ứng viên): giới hạn công suất và lực ở mức cho phép tay máy chạm người, nếu đánh giá rủi ro cho thấy chấp nhận được với mọi người có thể có mặt, kể cả trẻ em.
  - Hệ an toàn UR (ứng viên): thiết bị cho phép 3 vị trí nối vào I/O an toàn của UR, cùng tốc độ giảm, cho chạy tay khi người ở trong tầm với; deadman trên HMI nằm trong phần mềm nên không thay được thiết bị này.
  - Quy trình: vạch và biển báo vùng làm việc; hướng dẫn tài xế và người đi cùng rời xe, ra khỏi vùng trước khi chu trình bắt đầu và không quay lại khi tay máy đang chạy; chỉ người được đào tạo mới chạy tay, và chạy tay từ chỗ nhìn thấy tay máy.
  - Phần mềm (quan sát): chờ người rời vùng trước khi tay máy rời tư thế cất (`DRIVER_EGRESS`, `BAY_CLEAR`); giảm tốc hay dừng khi perception thấy người tới gần; hành lang tiếp cận có cấu trúc và giới hạn của ứng dụng; chạy tay chỉ ở `MAINTENANCE` và khi giữ deadman ([ADR 0006](../decisions/0006-hmi-contract.md)). Perception, camera và deadman không phải chức năng an toàn.
- Vùng requirement: MIS, MOT, PER, HMI.

## HZ-02. Ray dời tay máy, va chạm hoặc kẹp người dọc ray

- Tình huống và pha:
  - Vận hành tự động: ray đưa tay máy tới bay cần phục vụ hay về chỗ nghỉ khi điều phối nhiều bay; người đứng hay đi dọc ray, giữa cụm ray và tay máy với xe đỗ, cột, tường hay đầu cuối ray.
  - Chạy tay ray khi bảo trì (`MAINTENANCE`).
  - Lỗi: ray vẫn chạy khi tay máy đã dừng; ray chạy khi tay máy chưa thu về, nên tay máy quét qua bay bên cạnh; drive nhận lệnh sai, hoặc mất liên lạc Modbus TCP khi ray đang chạy.
- Tổn hại có thể: va đập; kẹp giữa cụm ray và tay máy với xe hay vật cố định; tay máy chưa thu về quét trúng người hay xe ở bay bên cạnh.
- Biện pháp:
  - STO ray: đầu ra an toàn của UR cắt STO của ray khi có dừng khẩn cấp hay dừng bảo vệ, nên ray mất mô-men cùng lúc tay máy dừng.
  - STO ray (đề xuất): scanner hoặc rào dọc ray cùng STO riêng của ray (ADR 0005, phần "Bảo vệ dọc ray"). Hệ an toàn UR không biết vị trí ray: giới hạn vị trí của UR tính theo đế, dời theo đế khi ray chạy, nên không giữ được vùng nào cố định dọc ray.
  - STO ray (ứng viên): ray chỉ có mô-men khi một đầu ra an toàn của UR báo tay máy ở tư thế cất.
  - Kết cấu (ứng viên): chặn cuối cơ khí và giới hạn hành trình ở hai đầu ray.
  - Quy trình: đánh dấu đường ray và vùng tay máy quét qua; không đi dọc ray khi máy chạy tự động; bảo trì ray sau khi khoá năng lượng.
  - Phần mềm (quan sát): ray chỉ chạy khi tay máy đã thu về; giới hạn tốc độ, gia tốc và hành trình của ứng dụng; theo dõi vị trí ray đọc về; dữ liệu cũ hay mất liên lạc thì dừng và vào `SAFE_HOLD` ([ADR 0004](../decisions/0004-motion-on-controller.md)).
- Vùng requirement: MOT, HAL, CFG, MIS.

## HZ-03. Tay máy tới sai chỗ vì model, hồ sơ tool, hiệu chuẩn hoặc cấu hình sai

- Tình huống và pha:
  - Lắp đặt, bảo trì, đổi tool hay đổi model tay máy trong cài đặt; dùng model custom.
  - Vận hành tự động khi hiệu chuẩn camera hay hand-eye sai hoặc đã lệch, thông số hiệu chuẩn riêng của tay máy không khớp, khung toạ độ hay đơn vị bị lẫn (`base` với `base_link`, mm với m), hoặc danh mục xe ghi sai vị trí cổng sạc.
  - Tải, trọng tâm hay TCP đặt trên controller khác tool thật; cấu hình an toàn của UR không khớp tool, tải hay bố trí cell thật.
- Tổn hại có thể: tay máy hay đầu sạc đâm vào xe hoặc người (dẫn tới HZ-01, HZ-04); UR tính giới hạn lực, công suất và tốc độ TCP trên tải và TCP sai, nên dừng muộn hơn mức đã đánh giá; hỏng cổng sạc.
- Biện pháp:
  - Hệ an toàn UR: giới hạn an toàn nằm trong cấu hình an toàn của UR, không lấy từ model hay cấu hình của phần mềm.
  - Quy trình: kỹ sư tại chỗ kiểm cấu hình an toàn của UR, tải và TCP trên controller khớp tool và bố trí cell thật, khi nghiệm thu và sau mỗi lần đổi tool; ghi checksum của cấu hình an toàn mà controller UR hiển thị vào hồ sơ nghiệm thu.
  - Phần mềm (quan sát): đổi model tay máy hay tool là thao tác liên quan an toàn, cần vai trò nâng quyền, xác thực lại và nhật ký kiểm toán (ADR 0005); hồ sơ tool đặt xuống controller rồi đọc lại để so khớp; FK trên host so với pose controller báo, lệch quá ngưỡng thì khoá đầu ra chuyển động; adapter UR đọc thông số hiệu chuẩn riêng của tay máy; cấu hình trạm chỉ được thu hẹp giới hạn; hiệu chuẩn không hợp lệ thì chặn chu trình (`CALIBRATION_BLOCKED`).
- Vùng requirement: ARM, CAL, CFG, AUTH, PER.

## HZ-04. Lực quá mức, kẹp hoặc kẹt ở chỗ ghép đầu sạc với cổng sạc

- Tình huống và pha:
  - Căn trục, cắm và dò cổng (`S10_ALIGN` tới `S12_SEAT_VERIFY`, `RETRY_INSERT`): cắm lệch trục hay vướng gờ; ngón tay người nằm giữa đầu sạc với cổng sạc hay nắp cổng.
  - Mở chốt và rút (`S17_UNLOCK_WAIT`, `S18_EXTRACT`, `ABORT_UNPLUG`): rút khi chốt còn giữ đầu sạc; chốt kẹt không mở (`CONNECTOR_STUCK`); chu trình bị huỷ và tay máy thu về khi đầu sạc còn trong cổng.
  - Xe dịch chuyển, trôi hay bị lái đi khi tay máy đang dấn vào xe hoặc đầu sạc đang cắm; cáp xoắn, vướng hay bị kéo căng.
- Tổn hại có thể: kẹp, dập ngón tay; hỏng cổng sạc, đầu sạc hay cáp, để lộ phần mang điện (dẫn tới HZ-05); đầu sạc bị giật khỏi cổng, cáp hay tay máy bật mạnh trúng người đứng gần; hỏng xe.
- Biện pháp:
  - Hệ an toàn UR: giới hạn lực, công suất và động lượng trong cấu hình an toàn của UR; vượt giới hạn thì UR dừng tay máy.
  - Bộ sạc: trình tự cấp điện do bộ sạc và xe điều khiển theo [IEC 61851-1](https://webstore.iec.ch/en/publication/33644); bộ sạc ngắt điện khi mạch Control Pilot hở, như khi đầu sạc bị giật ra.
  - Kết cấu (ứng viên): đoạn mềm hay khớp nhả cơ khí giữa mặt bích và đầu sạc, giới hạn lực truyền sang xe và tay máy khi xe dịch chuyển; đường dẫn và giá giữ cáp.
  - Quy trình: hướng dẫn tài xế tắt xe, không ngồi lại trong xe hay lái xe khi đầu sạc đang cắm; quy trình gỡ đầu sạc kẹt (HZ-06).
  - Phần mềm (quan sát): force mode trên controller với giới hạn lực của ứng dụng hẹp hơn giới hạn của UR (ADR 0004); giới hạn số lần thử lại khi quá lực, rồi chuyển sang chờ người; chỉ rút khi đo được chốt đã nhả và lực dọc trục nhỏ; huỷ chu trình khi đầu sạc có thể còn trong cổng thì đi qua bước rút (`ABORT_UNPLUG`), không thu tay ngay; xe xê dịch quá ngưỡng sau khi đã căn trục thì huỷ; không có số đo thì không coi điều kiện là đạt.
- Vùng requirement: MIS, MOT, HAL, PER.

## HZ-05. Điện giật, hồ quang, cháy hoặc bỏng ở đầu sạc, cáp và cổng sạc

- Tình huống và pha:
  - Cấp điện khi đầu sạc chưa vào hết hay chưa được giữ chắc (`S12_SEAT_VERIFY` tới `S15_CHARGING`).
  - Rút hay kéo đầu sạc khi còn điện (`S16_STOPPING` tới `S18_EXTRACT`, `ABORT_UNPLUG`); contactor của bộ sạc dính.
  - Cách điện của cáp hay đầu sạc hỏng do uốn lặp, va chạm, nước (HZ-09) hay lực quá mức (HZ-04); tiếp điểm quá nhiệt khi sạc.
  - Người chạm đầu sạc hay cổng sạc đang hở, hoặc gỡ đầu sạc kẹt bằng tay; xe cháy khi đang sạc và tay máy cản đường cứu hộ.
- Tổn hại có thể: điện giật; bỏng do hồ quang hay tiếp điểm nóng; cháy lan sang xe hay cell.
- Biện pháp:
  - Bộ sạc: chức năng an toàn điện của bộ sạc theo IEC 61851-1 và, với sạc DC, [IEC 61851-23](https://webstore.iec.ch/en/publication/32973), như kiểm mạch Control Pilot trước khi cấp điện, đóng cắt contactor, giám sát cách điện khi sạc DC; danh mục chính xác theo bộ sạc được chọn. Hệ thống không điều khiển Control Pilot (CP) hay Proximity Pilot (PP); cổng chính giữa hệ thống và bộ sạc là một tín hiệu cho phép nối cứng, nội dung tín hiệu chưa chốt.
  - Kết cấu (ứng viên): cáp, đầu sạc và đường dẫn cáp chịu được uốn lặp; thiết bị điện của cell theo [IEC 60204-1](https://webstore.iec.ch/en/publication/26037), gồm thiết bị cách ly nguồn; cấp bảo vệ vỏ hợp với nơi lắp (HZ-09).
  - Quy trình: kiểm cáp và đầu sạc định kỳ; khoá năng lượng bộ sạc trước khi chạm đầu sạc hay gỡ đầu sạc kẹt; quy trình chữa cháy và cứu hộ của nơi lắp, gồm cách gỡ tay máy và đầu sạc khỏi xe khi mất điện.
  - Phần mềm (quan sát): theo dõi bộ sạc qua kênh giám sát; yêu cầu dừng phiên khi nhiệt độ chân sạc vượt ngưỡng; chỉ rút khi dòng đã về 0 và chốt đã nhả. Dòng gần 0 hay chốt đã nhả không chứng minh đầu sạc đã hết điện.
- Vùng requirement: HAL, MIS.

## HZ-06. Người vào vùng nguy hiểm vì tin máy đã an toàn

- Tình huống và pha:
  - HMI báo "Dừng", `SAFE_HOLD`, `MAINTENANCE` hay chu trình đang chờ; đèn tháp tắt; dòng sạc gần 0. Người vào vùng để gỡ đầu sạc kẹt (`CONNECTOR_STUCK`), lau camera, sửa ray, đưa xe ra hay cứu người.
  - Người vận hành nhầm nút "Dừng" trên HMI với thiết bị dừng khẩn cấp.
  - Năng lượng còn lại khi máy đã dừng: cáp căng, đầu sạc còn bị giữ trong cổng, tay máy sụt khi nhả phanh, bộ sạc còn điện.
  - Người khác cho máy chạy lại, hoặc phần mềm tự tiếp tục, khi có người trong vùng (HZ-07).
- Tổn hại có thể: va đập, kẹp do chuyển động bất ngờ; điện giật; bị cáp hay tay máy bật trúng khi lực được giải phóng.
- Biện pháp:
  - Mạch cứng: thiết bị dừng khẩn cấp vật lý; chỉ nút reset vật lý xoá được chốt dừng khẩn cấp, và reset không tự cho máy chạy lại.
  - STO ray: ray mất mô-men khi tay máy dừng. STO chỉ cắt mô-men, không cách ly điện, nên không thay cho khoá năng lượng khi bảo trì.
  - Mạch cứng (ứng viên): rào có cửa khoá liên động nối vào mạch safeguard, nếu đánh giá rủi ro chọn rào cho cell.
  - Quy trình: quy trình tiếp cận và khoá năng lượng tại chỗ cho tay máy, ray và bộ sạc; trạng thái của phần mềm và đèn không cho phép vào vùng; cách gỡ đầu sạc kẹt và giải thoát người bị kẹt; hướng dẫn sử dụng theo [IEC/IEEE 82079-1](https://webstore.iec.ch/en/publication/29075).
  - Phần mềm (quan sát): nút trên HMI tên "Dừng", không gọi "Dừng khẩn cấp" hay "E-Stop" (ADR 0005); HMI và README nêu rõ lệnh dừng của phần mềm không phải chức năng an toàn; trạng thái chờ người (`CONNECTOR_STUCK`) không tự thoát.
- Vùng requirement: HMI, I18N, MIS.

## HZ-07. Chuyển động ngoài ý muốn khi khởi động, chạy lại hoặc khi phần mềm, mạng, dữ liệu hỏng

- Tình huống và pha:
  - Khởi động sau mất điện, sau lỗi phần mềm hay sau cập nhật (`BOOT`, rồi `SAFE_HOLD`); nối lại sau mất mạng; reset dừng khẩn cấp; rời `SAFE_HOLD`, `MAINTENANCE` hay một trạng thái dừng khi đầu sạc có thể còn trong cổng; một lệnh hay xác nhận cũ được dùng lại.
  - Vận hành: phần mềm treo hay chạy sai; mất kết nối với controller hay drive ray; dữ liệu cũ; perception cho kết quả sai mà vẫn đúng định dạng; segment đang chạy trên controller không dừng khi host mất liên lạc; thiết bị thật mất mà phần mềm chuyển sang mô phỏng và báo bình thường; hai nơi cùng ra lệnh.
- Tổn hại có thể: như HZ-01, HZ-02 và HZ-04, nặng hơn vì người trong vùng tin máy đang đứng yên.
- Biện pháp:
  - Hệ an toàn UR: giới hạn an toàn vẫn chặn tốc độ, lực và vùng làm việc của tay máy khi phần mềm chạy sai.
  - Mạch cứng: dừng khẩn cấp và dừng bảo vệ không đi qua phần mềm; reset không tự cho máy chạy lại.
  - STO ray: ray dừng theo đầu ra an toàn của UR, không phụ thuộc lệnh qua Modbus TCP.
  - Phần mềm (quan sát): khởi động luôn vào `SAFE_HOLD`; rời `SAFE_HOLD` cần danh sách kiểm đạt, và cần xác nhận của người khi đầu sạc có thể còn trong cổng; dữ liệu cũ, mất kết nối hay adapter lỗi thì dừng và vào `SAFE_HOLD`; mất thiết bị không bao giờ chuyển sang mô phỏng; nhận SIGTERM thì dừng có kiểm soát (ADR 0004, ADR 0005).
  - Phần mềm (quan sát, ứng viên): controller tự dừng segment đang chạy khi mất liên lạc với host, cách làm chưa quyết (ADR 0004); lệnh và xác nhận mất hiệu lực khi nối lại hay khi trạng thái của máy đổi.
- Vùng requirement: MIS, MOT, HAL, GW, REC.

## HZ-08. Thay đổi trái phép qua HMI, API hoặc mạng

- Tình huống và pha: người không có quyền, hay kẻ tấn công trên LAN của trạm, nới giới hạn của ứng dụng, đổi model tay máy hay tool, bật đầu ra chuyển động, nhập cấu hình, chạy tay hay ra lệnh chuyển động; chiếm phiên HMI từ site khác; bật hỗ trợ từ xa trái phép; cài bản không do Mr.Ròm ký khi chế độ developer bật; đổi cấu hình an toàn của UR ngay trên controller.
- Tổn hại có thể: giới hạn của ứng dụng bị nới hay tắt, máy chạy khi có người trong vùng, dẫn tới HZ-01 tới HZ-05.
- Biện pháp:
  - Hệ an toàn UR: giới hạn an toàn nằm trong cấu hình an toàn của UR, được bảo vệ bằng mật khẩu an toàn riêng của UR; phần mềm không được đổi cấu hình này. Chủ thiết bị cài được bản tự ký qua chế độ developer ([ADR 0013](../decisions/0013-ota-updates.md)), nên không biện pháp an toàn nào được dựa vào phần mềm.
  - Quy trình: mật khẩu an toàn của UR và vai trò bảo trì chỉ giao cho kỹ sư được chỉ định.
  - Phần mềm (quan sát): thao tác liên quan an toàn cần vai trò nâng quyền, xác thực lại và ghi nhật ký kiểm toán; cấu hình trạm chỉ được thu hẹp giới hạn (ADR 0005); session cookie có `Secure`, `HttpOnly`, `SameSite=Strict`, không có token trên URL (ADR 0006); mạng của cell tách riêng, LAN của trạm chỉ thấy cổng HTTPS 443 của HMI, không cổng nào mở vào từ WAN ([IEC 62443-3-3](https://webstore.iec.ch/en/publication/7033)); thiết bị chỉ cài bản cập nhật có chữ ký, chế độ developer có nhật ký kiểm toán (ADR 0013); hỗ trợ từ xa mặc định tắt, đường hầm chiều ra có hạn giờ và nhật ký kiểm toán ([ADR 0016](../decisions/0016-device-identity-and-keys.md)).
- Vùng requirement: AUTH, GW, CFG, OTA, HMI, DEP.

## HZ-09. Môi trường làm hỏng cách điện, cảm biến hoặc chỗ đứng

- Tình huống và pha: trạm ngoài trời hay nhà để xe; mưa, nước đọng, tuyết, băng, hơi nước ngưng tụ, bụi, nhiệt độ cao hay thấp, nắng chói hay tối; nước vào đầu sạc, cổng sạc, tủ điện hay drive; camera bẩn, chói hay mờ; thiết bị bảo vệ bị mưa, sương hay bụi làm tác động sai hoặc không tác động; sàn quanh bay trơn.
- Tổn hại có thể: điện giật, chập, cháy (HZ-05); perception sai làm tay máy tới sai chỗ (HZ-03, HZ-07); thiết bị bảo vệ không thấy người (HZ-01, HZ-02); người trượt ngã vào vùng làm việc.
- Biện pháp:
  - Kết cấu (ứng viên): cấp bảo vệ vỏ (mã IP) của tủ, drive, đầu sạc, camera và thiết bị bảo vệ hợp với nơi lắp; dải môi trường vận hành của từng thiết bị, kể cả thiết bị bảo vệ; mái che cho bay.
  - Bộ sạc: giám sát cách điện khi sạc DC (HZ-05).
  - Quy trình: hướng dẫn sử dụng ghi dải môi trường vận hành, ngoài dải đó thì không chạy tự động; vệ sinh camera và kiểm đầu sạc định kỳ; xử lý sàn trơn.
  - Phần mềm (quan sát): chờ khi thời tiết xấu (`WEATHER_HOLD`); perception có cổng bất định, ảnh kém thì tìm lại hay huỷ; hiệu chuẩn không hợp lệ thì chặn chu trình. ML và video không bao giờ là tín hiệu an toàn.
- Vùng requirement: MIS, PER, CAL, DEP.

## HZ-10. Cập nhật phần mềm, model hoặc firmware làm đổi hành vi đã nghiệm thu

- Tình huống và pha: cập nhật container, hệ điều hành hay model học máy qua OTA; đổi firmware của controller UR, drive ray hay bộ sạc ngoài OTA; chuyển đổi schema cấu hình; cập nhật bắt đầu khi tay máy đang chạy hay đầu sạc đang cắm; bản mới lỗi và quay lại không trọn; sau cập nhật, máy chạy tự động với hành vi khác bản đã nghiệm thu.
- Tổn hại có thể: gián tiếp; hành vi đã nghiệm thu không còn đúng, dẫn tới HZ-01, HZ-03, HZ-04 hay HZ-07.
- Biện pháp:
  - Hệ an toàn UR, Mạch cứng, STO ray: không phụ thuộc phần mềm, nên không đổi theo bản cập nhật container, hệ điều hành hay model (ADR 0005).
  - Quy trình: sau bản cập nhật động tới phần mềm hay cấu hình liên quan an toàn, thiết bị ở lại `SAFE_HOLD`; kỹ sư tại chỗ chạy checklist kiểm tra rút gọn rồi mới cho chạy tự động (ADR 0013); đổi firmware của controller UR, drive ray hay bộ sạc thì kiểm chứng lại các chức năng an toàn liên quan.
  - Phần mềm (quan sát): core chỉ cho cập nhật khi tay máy đã về vị trí an toàn, đang `SAFE_HOLD`, không có phiên sạc, đầu sạc không cắm và không còn lệnh chờ; trong lúc cập nhật chặn mọi lệnh; manifest có chữ ký, image theo digest; kiểm sức khoẻ không đạt thì tự quay lại bản trước; mỗi bản chạy trên một thiết bị trước (ADR 0013); model được kiểm checksum và chữ ký trước khi nạp ([ADR 0015](../decisions/0015-model-lifecycle.md)); schema cấu hình chỉ chuyển đổi theo chiều tiến, có sao lưu.
- Vùng requirement: OTA, CFG, TRN, DEP, AUTH.

## Việc đánh giá rủi ro phải làm

- Bổ sung hazard của các pha chưa xét và của nơi lắp cụ thể.
- Với từng hazard: người bị ảnh hưởng, tần suất và thời gian phơi nhiễm, mức nghiêm trọng, khả năng tránh, rủi ro trước và sau biện pháp.
- Chọn biện pháp theo thứ tự của ISO 12100: thiết kế an toàn tự thân, rồi bảo vệ và biện pháp bảo vệ bổ sung, rồi thông tin cho người dùng; đóng mọi mục `(đề xuất)` và `(ứng viên)`.
- Ghi PLr cho từng chức năng an toàn theo [ISO 13849-1](https://committee.iso.org/standard/73481.html), rồi xét PLd Cat 3 mà UR công bố có đủ hay không (ADR 0005).
- Xác định chuẩn nào áp dụng cho trạm công cộng và cho hộ gia đình, trong đó có [ISO 10218-2](https://committee.iso.org/standard/73934.html) về ứng dụng và cell robot công nghiệp.
- Làm lại khi model UR, drive ray, tool, bộ sạc, bố trí cell hay nơi lắp thay đổi.
