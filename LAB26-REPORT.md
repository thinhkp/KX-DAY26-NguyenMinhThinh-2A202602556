# Lab 26 — MCP Tools Integration

Sinh viên: **Nguyen Minh Thinh**  
MSSV: **2A202602556**  
Repo nộp dự kiến: `K04-DAY26-NguyenMinhThinh-2A202602556`  
Ngày thực hiện: **14/10/2026 (Asia/Bangkok)**

## Kết quả chạy thực tế

| Bước | Kết quả | Bằng chứng |
|---|---|---|
| 01 Function Calling | Gemini yêu cầu `get_weather` cho Hà Nội và Đà Nẵng; app thực thi và Gemini tổng hợp | [Ảnh](screenshots/01-function-calling.png), [log](evidence/01-function-calling.txt) |
| 02 MCP stdio | `list_tools` thấy `get_weather`; gọi thành công Hanoi, Danang, Haiphong | [Ảnh](screenshots/02-mcp-client.png), [log](evidence/02-mcp-client.txt) |
| 03a Auth hợp lệ | Khám phá tool và gọi thời tiết Hanoi thành công | [Ảnh](screenshots/03a-auth-ok.png), [log](evidence/03a-auth-ok.txt) |
| 03a Auth sai | Client bị từ chối; server ghi HTTP **401 Unauthorized** | [Ảnh](screenshots/03a-auth-fail.png), [client log](evidence/03a-auth-fail.txt), [server log](evidence/03a-auth-server.txt) |
| 03b Registry | Tìm 2 tool tag weather; chọn `get_weather_v2` v2.0.0 | [Ảnh](screenshots/03b-registry.png), [log](evidence/03b-registry.txt) |
| 03c Versioning | Đọc metadata/deprecation, gọi v1 và v2 có forecast | [Ảnh](screenshots/03c-versioning.png), [log](evidence/03c-versioning.txt) |
| 04 Verify setup | **All checks passed**, MCP initialize/list_tools/health_check thành công | [Ảnh](screenshots/04-verify-setup.png), [log](evidence/04-verify-setup.txt) |
| 04 ADK current | Gọi `get_current_weather("Hanoi")`; trả 32.9°C, cảm giác 35.4°C, độ ẩm 47%, UV 6.9; cập nhật 11:15 ngày 14/10/2026 | [Ảnh giao diện ADK](screenshots/04-adk-current.png) |
| 04 ADK forecast | Gọi `get_forecast`; trả nhiệt độ cao/thấp và xác suất mưa cho 14–16/10/2026 | [Ảnh giao diện ADK](screenshots/04-adk-forecast.png), [session gồm tool calls và responses](evidence/04-adk-session.json) |

Dữ liệu WeatherAPI là dữ liệu nhận được lúc chạy bài, không phải dự báo cố định trong code.
Cloud Run là phần tùy chọn và chưa thực hiện.

**Nguồn ảnh:** hai ảnh ADK được chụp trực tiếp từ giao diện ADK web. Bảy ảnh
demo/verify được chụp trong trình duyệt hiển thị stdout/stderr đã lưu từ tiến trình
thật, có nhãn nguồn và thời điểm; chúng **không phải ảnh cửa sổ terminal**.
VLearn yêu cầu ảnh terminal cho các bước này, nên cần chụp lại từ terminal nếu
người chấm yêu cầu đúng hình thức đó. Log gốc và mã thoát được giữ để đối chiếu.

## Những điểm rút ra

- Function Calling là khả năng model sinh tên hàm và tham số. `handler(**(fc.args or {}))`
  trong app mới thực thi tool, rồi gửi kết quả về Gemini.
- MCP chuẩn hóa việc kết nối, khám phá và gọi tool. Demo stdio không có LLM;
  server tự sinh schema từ khai báo tool, client dùng `list_tools` và `call_tool`.
- Authentication được xử lý ở transport; hàm thời tiết không kiểm tra bearer token.
  Lần thử token sai trong môi trường này trả **401**, không phải 403 như mô tả ban đầu.
- Registry tìm tool theo tag, ưu tiên phiên bản mới không deprecated.
- Versioning giữ v1 hoạt động, thêm v2 và các tham số optional, công bố metadata migration.
- ADK khám phá tool qua HTTP và tự điều phối vòng lặp Function Calling.
  MCP server gọi REST WeatherAPI; agent chỉ thấy các tool MCP.

## Thay đổi để chạy được trên Windows và dùng .env

- Thêm `get_forecast` dùng API thật trong bài 01, schema và bộ điều phối theo tên tool.
- Đọc `.env` cạnh script hoặc tại gốc repo. ADK dùng `GOOGLE_API_KEY`, hoặc lấy
  `GEMINI_API_KEY` khi chưa có `GOOGLE_API_KEY`.
- Đọc `registry.json` bằng UTF-8, khắc phục lỗi encoding mặc định của Windows.
- Verify setup che toàn bộ key và kiểm tra giao thức MCP thật thay vì chỉ GET endpoint.
- MCP server không in URL/exception có thể chứa WeatherAPI key.

## Chạy lại

Ở gốc repo, `.env` chứa `GEMINI_API_KEY` và `WEATHERAPI_KEY` (giá trị thật,
không commit). Cài môi trường:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/collect_evidence.py
```

Script trên chạy demo 01–03 và lưu log; token sai có mã thoát 1 là kết quả mong đợi.
Ảnh không được script tạo giả: chụp terminal sau khi chạy để đáp ứng VLearn.
Auth server được dừng trong `finally` để giải phóng cổng 8000.

Terminal server:

```powershell
cd 04-lab/mcp-server
uv sync --frozen
$env:PORT="8085"
uv run python weather.py
```

Terminal client:

```powershell
cd 04-lab/mcp-client
uv sync --frozen
uv run python verify_setup.py
uv run adk web --host 127.0.0.1 --port 8000
```

Mở http://localhost:8000, chọn `weather_agent`, hỏi thời tiết hiện tại và dự báo 3 ngày.
`PORT=8085` giúp server chọn HTTP ngay cả khi stdin không phải terminal tương tác.

## Trước khi nộp

- Đổi tên fork cá nhân thành tên repo đúng khóa học (K04 được suy ra từ khóa VLearn đang mở).
- Chụp lại bảy ảnh terminal nếu cần đúng hình thức yêu cầu VLearn.
- Kiểm tra không đưa `.env`, `.venv`, `.adk` hay API key vào commit.
- Commit code, báo cáo và ảnh; push lên fork cá nhân và nộp URL qua VLearn.
- Chưa đổi tên repo GitHub, chưa push và chưa nộp qua VLearn trong lần thực hiện này.
