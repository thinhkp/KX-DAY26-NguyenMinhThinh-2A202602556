"""Minh hoạ FUNCTION CALLING thuần với Google Gemini SDK.

Tools `get_weather` (mock), `get_forecast` (WeatherAPI thật) được định nghĩa schema thủ công VÀ thực thi ngay trong
chính file app này. Model chỉ QUYẾT ĐỊNH gọi tool nào; app mới là nơi chạy.

Cách chạy:
    pip install -r ../requirements.txt
    # Điền GEMINI_API_KEY và WEATHERAPI_KEY trong .env (xem .env.example)
    python weather_function_calling.py
"""

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from google import genai
from google.genai import types
from dotenv import load_dotenv

# Ưu tiên biến môi trường > .env cạnh script > .env ở thư mục gốc repo.
# Đường dẫn dựa trên file script nên chạy từ thư mục nào cũng được.
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env", override=False)
load_dotenv(SCRIPT_DIR.parent / ".env", override=False)

MODEL = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
    "Dùng get_forecast khi người dùng hỏi dự báo, ngày mai hoặc những ngày tới. "
    "get_weather chỉ trả dữ liệu minh họa, hãy nói rõ đó là dữ liệu giả lập. "
    "Dự báo bao gồm hôm nay theo giờ địa phương của thành phố. "
    "Nếu tool trả lỗi, giải thích lỗi và không tự bịa dữ liệu thời tiết."
)

# 1. App tự định nghĩa schema của tool
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING, description="Tên thành phố"
            )
        },
        required=["city"],
    ),
)

get_forecast_declaration = types.FunctionDeclaration(
    name="get_forecast",
    description=(
        "Lấy dự báo thời tiết thật từ WeatherAPI, tối đa 3 ngày, bao gồm hôm nay. "
        "Hỏi ngày mai thì dùng days=2, ngày kia thì dùng days=3."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(type=types.Type.STRING, description="Tên thành phố, ví dụ Hanoi"),
            "days": types.Schema(
                type=types.Type.INTEGER,
                description="Số ngày dự báo từ 1 đến 3, bao gồm hôm nay; mặc định 3",
            ),
        },
        required=["city"],
    ),
)

TOOLS = [types.Tool(function_declarations=[get_weather_declaration, get_forecast_declaration])]


# 2. App tự thực thi tool (trong thực tế sẽ gọi API thời tiết thật)
def get_weather(city: str) -> str:
    """Trả về thời tiết (mock) của *city*. Dùng làm tool cho model."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }
    import json

    default = {"nhiệt_độ": "28°C", "thời_tiết": "không có dữ liệu chi tiết"}
    return json.dumps({"city": city, **mock_data.get(city, default)}, ensure_ascii=False)


def get_forecast(city: str, days: int = 3) -> dict:
    """Gọi WeatherAPI thật qua HTTPS; giới hạn 1–3 ngày cho gói Free.

    Lấy key tại https://www.weatherapi.com/ rồi đặt WEATHERAPI_KEY.
    Không dùng dữ liệu giả lập khi API thất bại.
    """
    if not isinstance(city, str) or not city.strip():
        return {"error": "Tên thành phố không được để trống."}
    if type(days) is not int or not 1 <= days <= 3:
        return {"error": "days phải là số nguyên từ 1 đến 3, bao gồm hôm nay."}
    api_key = os.getenv("WEATHERAPI_KEY")
    if not api_key:
        return {"error": "Chưa đặt WEATHERAPI_KEY. Lấy key miễn phí tại https://www.weatherapi.com/."}

    query = urlencode({"key": api_key, "q": city.strip(), "days": days,
                       "aqi": "no", "alerts": "no", "lang": "vi"})
    try:
        with urlopen(f"https://api.weatherapi.com/v1/forecast.json?{query}", timeout=20) as response:
            data = json.load(response)
        location = data["location"]
        forecast = []
        for item in data["forecast"]["forecastday"]:
            day = item["day"]
            forecast.append({
                "date": item["date"],
                "condition": day["condition"]["text"],
                "min_temperature_c": day["mintemp_c"],
                "max_temperature_c": day["maxtemp_c"],
                "average_temperature_c": day["avgtemp_c"],
                "chance_of_rain_percent": day["daily_chance_of_rain"],
                "total_precipitation_mm": day["totalprecip_mm"],
                "max_wind_kph": day["maxwind_kph"],
                "average_humidity_percent": day["avghumidity"],
            })
        if not forecast:
            return {"error": "WeatherAPI không trả dữ liệu dự báo."}
        return {
            "source": "WeatherAPI.com",
            "city": location["name"],
            "country": location["country"],
            "timezone": location["tz_id"],
            "localtime": location["localtime"],
            "forecast": forecast,
        }
    except HTTPError as exc:
        # Không trả str(exc): URL trong exception có thể chứa API key.
        error_code = None
        try:
            error_code = json.load(exc).get("error", {}).get("code")
        except (ValueError, AttributeError):
            pass
        messages = {
            1006: "Không tìm thấy thành phố. Thử tên như Hanoi hoặc Danang.",
            2006: "WEATHERAPI_KEY không hợp lệ.",
            2007: "Đã hết hạn mức gọi WeatherAPI của gói hiện tại.",
            2008: "WeatherAPI key đã bị vô hiệu hóa.",
            2009: "Gói WeatherAPI hiện tại không có quyền dùng chức năng này.",
        }
        return {"error": messages.get(error_code, f"WeatherAPI trả lỗi HTTP {exc.code}. Thử lại sau.")}
    except (URLError, TimeoutError, OSError):
        return {"error": "Không kết nối được WeatherAPI hoặc yêu cầu quá thời gian. Thử lại sau."}
    except (ValueError, KeyError, TypeError):
        return {"error": "Dữ liệu WeatherAPI trả về không đúng định dạng mong đợi."}


TOOL_HANDLERS = {"get_weather": get_weather, "get_forecast": get_forecast}


def run(prompt: str) -> str:
    """Gửi *prompt* tới Gemini, tự động xử lý function calling và trả về câu trả lời cuối."""
    client = genai.Client()
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=TOOLS,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while resp.function_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        contents.append(resp.candidates[0].content)

        function_responses = []
        for fc in resp.function_calls:
            print(f"  [model yêu cầu] {fc.name}({fc.args})")
            handler = TOOL_HANDLERS.get(fc.name)
            if handler is None:
                result = {"error": f"Tool không được hỗ trợ: {fc.name}"}
            else:
                try:
                    result = handler(**(fc.args or {}))  # App chạy tool được model chọn
                except TypeError:
                    result = {"error": "Tham số gọi tool không hợp lệ."}
            print(f"  [app thực thi]  -> {result}")
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name, response={"result": result}
                )
            )

        # Gửi kết quả tool trả về cho model
        contents.append(types.Content(role="user", parts=function_responses))
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 5. Model tổng hợp câu trả lời cuối
    return resp.text


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Ngày mai đi chơi hà nội có cần mang ô không"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
