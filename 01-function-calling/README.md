# 01 — Function Calling thuần (Google Gemini SDK)

Tool `get_weather` được **định nghĩa schema thủ công** và **thực thi ngay trong app**.
Model chỉ quyết định gọi tool nào — app mới là nơi chạy.

```
User hỏi  →  Model quyết định gọi get_weather(city="Hà Nội")
                     │
                     ▼
              App TỰ THỰC THI hàm get_weather
                     │
                     ▼
              Model tổng hợp câu trả lời
```

## Cách chạy

### Tool dự báo dùng API thật (miễn phí)

`get_forecast(city, days=3)` gọi HTTPS tới WeatherAPI và trả dự báo theo ngày:
nhiệt độ thấp/cao/trung bình, khả năng mưa, lượng mưa, độ ẩm và gió.
Gói Free hỗ trợ dự báo 3 ngày, bao gồm hôm nay theo giờ địa phương của thành phố.
`get_weather` vẫn là tool giả lập của ví dụ ban đầu.

**Lấy WeatherAPI key miễn phí:**

1. Vào https://www.weatherapi.com/ và chọn **Sign Up / Get Free API Key**.
2. Đăng ký tài khoản, xác nhận email nếu được yêu cầu rồi đăng nhập.
3. Sao chép **API Key** trong trang tài khoản; dùng gói **Free**, không cần thẻ.
4. Đặt key trong biến môi trường `WEATHERAPI_KEY`; không ghi key vào source code.

Nguồn: [Getting Started](https://www.weatherapi.com/docs/getting-started/),
[gói Free](https://www.weatherapi.com/).

Gemini dùng key riêng: đăng nhập https://aistudio.google.com/apikey,
chọn **Create API key** rồi đặt `GEMINI_API_KEY`.

Chạy trên **PowerShell**, từ thư mục gốc repo:

```powershell
python -m pip install google-genai
cd 01-function-calling
$env:GEMINI_API_KEY="key_gemini_cua_ban"
$env:WEATHERAPI_KEY="key_weatherapi_cua_ban"
python weather_function_calling.py "Dự báo Hà Nội ngày mai có mưa không?"
```

Hoặc dùng **file `.env`** để không cần đặt `$env:` mỗi lần:

```powershell
python -m pip install google-genai python-dotenv
cd 01-function-calling
Copy-Item .env.example .env
```

Điền key thật trong `01-function-calling/.env`:

```dotenv
GEMINI_API_KEY=key_gemini_cua_ban
WEATHERAPI_KEY=key_weatherapi_cua_ban
```

Sau đó chạy `python weather_function_calling.py`.
Script cũng đọc `.env` ở thư mục gốc repo nếu thiếu key trong `.env` cạnh script.
Thứ tự ưu tiên: biến môi trường của terminal, `.env` cạnh script, `.env` gốc repo.
File `.env` đã được bỏ qua trong `.gitignore`; không commit key thật.

Kiểm tra riêng WeatherAPI, không gọi Gemini:

```powershell
python -c "from weather_function_calling import get_forecast; import json; print(json.dumps(get_forecast('Hanoi', 3), ensure_ascii=False, indent=2))"
```

Hỏi ngày mai dùng `days=2`; ngày kia dùng `days=3`. Tool trả lỗi rõ ràng
khi thiếu key, key sai, hết hạn mức hoặc không kết nối được API.

### Chạy trên Bash

```bash
pip install -r ../requirements.txt
export GEMINI_API_KEY=...
export WEATHERAPI_KEY=...
python weather_function_calling.py
```

## File

| File | Mô tả |
|---|---|
| `weather_function_calling.py` | Định nghĩa schema, thực thi tool, gọi model Gemini, xử lý vòng lặp function calling |

---

## Function Calling là gì? Giải thích đơn giản

Hình dung bạn có một **trợ lý ảo** rất giỏi ngôn ngữ, nhưng **không biết gì về thế giới thật** — không biết thời tiết, không truy cập được database, không gọi được API.

Function Calling là cách bạn **dạy trợ lý ảo sử dụng công cụ**:

```
Không có Function Calling:                 Có Function Calling:

User: "Thời tiết HN?"                     User: "Thời tiết HN?"
       │                                         │
       ▼                                         ▼
   ┌────────┐                                ┌────────┐
   │ Model  │                                │ Model  │
   │        │                                │        │ ← biết có tool get_weather
   │ "Tôi   │                                │ "Hãy   │
   │ không  │                                │  gọi   │
   │ biết"  │                                │ get_   │
   │        │                                │ weather│
   └────────┘                                │("HN")  │
                                             └───┬────┘
   Model bó tay vì                               │
   không có dữ liệu                              ▼
                                             App chạy hàm
                                                  │
                                                  ▼
                                             ┌────────┐
                                             │ Model  │
                                             │ "HN:   │
                                             │ 29°C,  │
                                             │ mưa"   │
                                             └────────┘
```

**Điểm mấu chốt:** Model **KHÔNG chạy** hàm. Nó chỉ nói *"hãy gọi hàm X với tham số Y"*.

---

## Minh hoạ từng bước chi tiết

User hỏi: **"Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"**

```
Bước 1 — App chuẩn bị "hộp công cụ" cho model
═══════════════════════════════════════════════

    App định nghĩa schema THỦ CÔNG:
    ┌────────────────────────────────────────┐
    │  Tool: get_weather                     │
    │  Mô tả: "Lấy thời tiết thành phố"      │
    │  Tham số:                              │
    │    city: string (bắt buộc)             │
    │                                        │
    │   Schema viết TAY - 15 dòng code       │
    │     phải khớp với hàm thật             │
    └────────────────────────────────────────┘

Bước 2 — Gửi prompt + schema cho model
═══════════════════════════════════════

    App ──────────────────────────────────────────▶ Gemini
    │  "Thời tiết HN và ĐN?"                      │
    │  + schema get_weather                       │
    │                                             │
    │  Model hiểu: "À, có tool get_weather,       │
    │   tôi cần gọi nó 2 lần cho HN và ĐN"        │

Bước 3 — Model TRẢ VỀ yêu cầu gọi tool (không tự chạy!)
═════════════════════════════════════════════════════════

    Gemini ──────────────────────────────────────▶ App
    │  function_calls:                             │
    │    [                                         │
    │      get_weather(city="Hà Nội"),             │
    │      get_weather(city="Đà Nẵng")             │
    │    ]                                         │
    │                                              │
    │    Model CHỈ sinh JSON — không hề chạy       │

Bước 4 — App TỰ THI HÀNH hàm get_weather
═════════════════════════════════════════

    App nhận yêu cầu → CHẠY hàm Python:
    ┌──────────────────────────────────────────┐
    │  get_weather("Hà Nội")   → "29°C, mưa"   │ ← App chạy
    │  get_weather("Đà Nẵng")  → "30°C, mây"   │ ← App chạy
    └──────────────────────────────────────────┘

Bước 5 — Gửi kết quả lại cho model tổng hợp
════════════════════════════════════════════

    App ──────────────────────────────────────────▶ Gemini
    │  Kết quả: HN 29°C mưa, ĐN 30°C mây         │
    │                                            │
    │  Gemini: "Hà Nội 29°C, mưa nhẹ 🌧️          │
    │           nhớ mang ô nhé!                  │
    │           Đà Nẵng 30°C, nhiều mây 🌤️       │
    │           thời tiết dễ chịu!"              │
```

---

## Nhìn vào code thật

3 phần quan trọng trong `weather_function_calling.py`:

**Phần 1 — Schema viết tay** (model cần biết tool trông như thế nào):

```python
# App phải TỰ MÔ TẢ tool cho model — viết tay, dễ sai
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(type=types.Type.STRING, description="Tên thành phố")
        },
        required=["city"],
    ),
)
```

**Phần 2 — Hàm thực thi** (app tự chạy khi model yêu cầu):

```python
# App phải CÓ hàm thật để chạy — model không chạy hàm này
def get_weather(city: str) -> str:
    return json.dumps({"city": city, "nhiệt_độ": "29°C", ...})
```

**Phần 3 — Vòng lặp** (nhận yêu cầu → chạy → trả lại):

```python
while resp.function_calls:
    for fc in resp.function_calls:
        result = get_weather(**fc.args)   # ← APP chạy, không phải model
    # gửi result lại cho model để tổng hợp câu trả lời
```

---

## Luồng hoạt động

1. App định nghĩa `FunctionDeclaration` với schema viết tay (tên, tham số, kiểu)
2. App gửi prompt + danh sách tool tới Gemini
3. Model trả về `function_calls` — yêu cầu gọi `get_weather`
4. App **tự chạy** hàm `get_weather()` và đưa kết quả trả lại model
5. Model tổng hợp câu trả lời cuối cho user

## Nhược điểm

```
┌─────────────────────────────────────────────────────────────┐
│  ❌ Schema viết tay                                         │
│     FunctionDeclaration(name=..., parameters=...)           │
│     → 15+ dòng boilerplate, dễ lệch với hàm thật            │
│                                                             │
│  ❌ Tool gắn chặt trong app                                 │
│     App A có get_weather → App B muốn dùng?                 │
│     → Copy schema + hàm sang App B                          │
│     → Sửa hàm ở A? Phải nhớ sửa cả B                        │
│                                                             │
│  ❌ Mỗi provider 1 format                                   │
│     Google: FunctionDeclaration(...)                        │
│     OpenAI: {"type": "function", "function": {...}}         │
│     Anthropic: {"name": ..., "input_schema": {...}}         │
│     → Đổi model = viết lại schema                           │
└─────────────────────────────────────────────────────────────┘
```

**MCP giải quyết tất cả các vấn đề trên** → xem [02-mcp-basics/](../02-mcp-basics/)

Bước tiếp theo: [02-mcp-basics/](../02-mcp-basics/) — tách tool ra MCP server độc lập.
