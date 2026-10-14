Chuẩn bị repo, môi trường và API key
Về bài lab này
Chạy lần lượt bốn bước của repo Day 26, rồi kết nối một agent Google ADK với MCP server WeatherAPI qua Streamable HTTP và nộp bằng chứng trong repo cá nhân.
Bạn làm được gì sau bài này
Chạy được vòng lặp Function Calling với Gemini và chỉ ra chỗ app tự thực thi tool.
Chạy được MCP client khám phá và gọi tool của một MCP server qua stdio.
Quan sát được bearer token, Tool Registry và versioning trong ba demo production.
Chạy MCP server WeatherAPI ở cổng 8085 và cho agent ADK trả lời bằng dữ liệu thời tiết thật.
Nộp repo KX-DAY26-HoVaTen-MSSV có đủ ảnh chụp bằng chứng cho từng bước.
Cần chuẩn bị
Biết dùng terminal, Git và môi trường ảo Python.
Có tài khoản GitHub để fork repository.
Có Gemini API key và WeatherAPI key của riêng mình.
Python 3.12 trở lên (mcp-client yêu cầu >=3.12)
Git
uv (dùng cho Lab 04)
Trình duyệt để mở ADK web tại http://localhost:8000
Lỗi thường gặp
Agent không kết nối được MCP server, báo 404 hoặc timeout → khởi động server trong mcp-server trước rồi mới chạy adk web; kiểm tra MCP_SERVER_URL là http://localhost:8085/mcp.
adk web không mở được cổng 8000 → auth_server.py của bước 3 vẫn đang chạy ở cổng 8000; dừng nó bằng Ctrl+C.
Server in 'Starting FastMCP server in stdio mode' thay vì 'Starting MCP server on http://0.0.0.0:8085/mcp' → chạy weather.py trực tiếp trong một terminal thật, không qua pipe hay trình chạy nền.
Tool trả 'WeatherAPI key not configured' → đặt biến WEATHERAPI_KEY trong chính terminal chạy server rồi khởi động lại server.
verify_setup.py báo GOOGLE_API_KEY not configured → tạo file .env trong mcp-client với GOOGLE_API_KEY là key thật.
Hai khái niệm Function Calling và MCP rất dễ bị đánh đồng, vì cả hai đều xoay quanh việc "cho model dùng tool". Repo Day 26 tách chúng ra bằng cách cài cùng một tool thời tiết theo bốn cách, mỗi cách thêm đúng một lớp. Bạn sẽ chạy từng cách, chụp lại kết quả, và hiểu lớp nào giải quyết vấn đề gì.

Đích cuối là một agent Google ADK trả lời câu hỏi thời tiết bằng dữ liệu thật lấy từ WeatherAPI.com, qua một MCP server do bạn tự chạy. Bạn làm bài cá nhân và nộp một repo fork đã đổi tên thành KX-DAY26-HoVaTen-MSSV, có ảnh chụp cho từng bước, qua VLearn.

Chặng này dựng sẵn mọi thứ bạn cần cho bốn bước sau: repo cá nhân để nộp bài, môi trường Python cho bước 01–03, và hai API key. Làm cho xong ngay từ đầu để giữa chừng không phải dừng lại đi xin key.

Repository gốc của Lab:

Day 26 — MCP Tools Integration
main
Day 26 — MCP Tools Integration
git clone https://github.com/VinUni-AI20k/Day26-MCP-Tools-Integration.git

Tạo repo nộp bài
Bạn nộp chính repo đã fork, nên hãy đặt đúng tên ngay khi fork để khỏi phải đổi về sau.

1. Trên GitHub, fork repository ở trên về tài khoản của bạn. Ở ô tên repository, nhập KX-DAY26-HoVaTen-MSSV, thay HoVaTen và MSSV bằng họ tên viết liền không dấu và mã số sinh viên của bạn.
2. Clone repo vừa fork về máy rồi cd vào thư mục đó. Mọi lệnh trong Lab đều chạy từ thư mục gốc này hoặc thư mục con mà Lab chỉ định.
3. Tạo thư mục screenshots/ ở gốc repo. Đây là nơi bạn lưu toàn bộ ảnh bằng chứng.
Môi trường cho bước 01–03
Bước 01–03 dùng chung requirements.txt ở thư mục gốc, với MCP Python SDK v2 (mcp[cli]>=2.0.0,<3). Lab 04 có môi trường riêng do uv quản lý, bạn sẽ dựng nó ở bước 4. Chọn lệnh theo hệ điều hành của bạn:

Tạo virtualenv và cài thư viện
macOS / Linux
Windows PowerShell
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Chép
Hai API key bạn cần
Gemini API key — dùng ở bước 01 (biến GEMINI_API_KEY) và bước 4 (biến GOOGLE_API_KEY trong .env). README của mcp-client dẫn tới https://aistudio.google.com/apikey để lấy key.
WeatherAPI key — dùng cho MCP server ở bước 4 (biến WEATHERAPI_KEY). Đăng ký miễn phí tại https://weatherapi.com.
Không commit key
.gitignore của repo đã bỏ qua .env. Đừng dán key vào file .py, README hay ảnh chụp. Trước khi chụp màn hình, kiểm tra để key không lộ trong terminal.

Trước khi sang bước 10/5

Repo fork có tên đúng `KX-DAY26-HoVaTen-MSSV`.

Thư mục `screenshots/` đã có ở gốc repo.

`pip install -r requirements.txt` chạy xong không lỗi.

Đã có Gemini API key và WeatherAPI key.

Máy đã cài `uv` cho Lab 04.

Bước 1 — Function Calling thuần: app tự định nghĩa và tự chạy tool
Bạn bắt đầu từ cách đơn giản nhất để model dùng được tool: không có server, không có giao thức, mọi thứ nằm trong một file Python. Chặng này cần làm rõ một điểm mà toàn bộ phần còn lại của Lab dựa vào: model không bao giờ tự chạy hàm. Nó chỉ trả về yêu cầu kiểu "hãy gọi get_weather với city='Hà Nội'", còn app mới là bên thực thi.

Bài toán của bước này
Gemini giỏi ngôn ngữ nhưng không biết thời tiết hôm nay. Muốn nó trả lời được, app phải cho model biết có một công cụ tên là gì, nhận tham số nào, rồi chờ model quyết định có dùng hay không. Nếu model muốn dùng, app chạy hàm thật, gửi kết quả lại, và model tổng hợp thành câu trả lời.

Bước này là nền để so sánh. Khi sang MCP, bạn sẽ thấy phần "model quyết định gọi tool nào" vẫn giữ nguyên, chỉ có chỗ định nghĩa và chạy tool là thay đổi.

Function Calling nghĩa là gì trong Lab này
Function Calling là một khả năng của model. Khi nhận prompt kèm danh sách tool có schema, model có thể sinh ra function_calls, tức tên tool và tham số dạng JSON. Đây không phải giao thức hay thư viện kết nối nào cả.

Schema ở đây là types.FunctionDeclaration mô tả tool get_weather: tên, mô tả, và tham số city kiểu string, bắt buộc. Model chỉ biết về tool qua schema này, nên schema phải khớp với hàm Python thật. Chỗ dễ nhầm: viết schema xong không có nghĩa là model gọi được hàm. Phải có vòng lặp trong app nối yêu cầu của model với hàm thật.

Ba phần trong 01-function-calling/weather_function_calling.py
File này có ba phần, theo đúng thứ tự README mô tả:

Phần	Trong code	Trách nhiệm
Schema viết tay	get_weather_declaration = types.FunctionDeclaration(...)	Mô tả tool cho model
Hàm thực thi	def get_weather(city: str) -> str	Trả dữ liệu mock cho Hà Nội, Hồ Chí Minh, Đà Nẵng
Vòng lặp	while resp.function_calls:	Nhận yêu cầu, chạy hàm, gửi kết quả lại cho model
Theo README của bước này, cách làm đó có ba nhược điểm. Schema phải viết tay và dễ lệch với hàm thật. Tool gắn chặt vào app, nên app khác muốn dùng thì phải copy cả schema lẫn hàm. Và mỗi nhà cung cấp model có một định dạng schema riêng. Hãy nhớ ba điểm này, vì bước 2 xử lý chính chúng.

Chạy và quan sát
1. Mở file 01-function-calling/weather_function_calling.py. Tìm ba phần trong bảng trên để biết khi chạy bạn sẽ thấy dòng in nào ứng với phần nào.
2. Trong terminal đã kích hoạt .venv, đặt Gemini key rồi chạy file:
Chạy Function Calling
macOS / Linux
Windows PowerShell
export GEMINI_API_KEY=...
cd 01-function-calling
python weather_function_calling.py
Chép
1. Đọc output từ trên xuống. Câu hỏi cố định trong file là "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?". Bạn sẽ thấy các dòng [model yêu cầu] get_weather(...), mỗi dòng theo sau là [app thực thi] -> {...} chứa JSON dữ liệu mock, cuối cùng là dòng Trả lời: do Gemini viết bằng tiếng Việt.
2. Chụp màn hình terminal sao cho thấy cả dòng [model yêu cầu], [app thực thi] và Trả lời:. Lưu thành screenshots/01-function-calling.png.
Checkpoint
Bước này đạt khi output có ít nhất một cặp [model yêu cầu] / [app thực thi] và một câu trả lời cuối dựa trên dữ liệu đó. Cặp dòng ấy là bằng chứng rõ nhất cho việc model chỉ yêu cầu, còn dòng result = get_weather(**fc.args) trong app mới là chỗ chạy hàm.

Nếu lỗi xác thực xảy ra trước khi có dòng [model yêu cầu], kiểm tra lại GEMINI_API_KEY trong đúng terminal đang chạy lệnh. Sang bước 2, bạn sẽ lấy tool ra khỏi app này và đặt nó vào một server riêng.


Bước 2 — Tách tool thành MCP server độc lập
Ở bước 1, schema, hàm và vòng lặp nằm chung một file. Bước 2 tách tool get_weather ra một MCP server riêng, rồi dùng một MCP client để hỏi server có tool gì và gọi nó. Bước này không cần API key nào, vì nó chỉ minh hoạ lớp giao thức, chưa có model tham gia.

Bài toán của bước này
Ba nhược điểm ở bước 1 có chung một nguyên nhân: tool là một phần của app. Muốn tool dùng lại được ở nhiều nơi, nó phải tự mô tả được chính nó và chạy ở một chỗ mà bất kỳ client nào cũng kết nối tới được. MCP chuẩn hoá đúng hai việc đó: server tự công bố tool, còn client khám phá và gọi tool qua một giao thức chung.

Câu hỏi bạn cần trả lời sau bước này: lớp nào biến mất, lớp nào giữ nguyên? Theo README gốc, MCP dùng Function Calling bên dưới. Model vẫn quyết định gọi tool nào, MCP chỉ thay cách client kết nối tới nơi tool thực sự chạy.

Các thuật ngữ cần tách rõ
MCP server (02-mcp-basics/weather_server.py): tạo MCPServer("weather") và khai báo tool bằng @mcp.tool(). Schema được tự sinh từ type hint city: str, kiểu trả về -> str và docstring, nên bạn không phải viết FunctionDeclaration nữa.
MCP client (02-mcp-basics/weather_client.py): mở ClientSession, gọi session.list_tools() để khám phá tool lúc chạy, rồi gọi session.call_tool("get_weather", {"city": ...}).
stdio transport: client tự khởi động server như một tiến trình con và trao đổi qua stdin/stdout, dùng StdioServerParameters(command=sys.executable, args=["weather_server.py"]). Vì vậy bạn không cần mở terminal riêng cho server.
Chỗ dễ nhầm: client không hard-code tên hay tham số của tool. Danh sách tool đến từ server lúc chạy. Client vẫn truyền tên "get_weather" khi gọi, nhưng đó là tên vừa đọc được từ server.

Thay đổi so với bước 1
01-function-calling	02-mcp-basics
Khai báo schema	Viết tay FunctionDeclaration	@mcp.tool() tự sinh
Nơi thực thi tool	Trong app gọi model	Trong MCP server riêng
Khám phá tool	Hard-code danh sách	list_tools() lúc chạy
Dùng lại ở app khác	Copy code	Cắm thêm client
README của bước này cũng chỉ ra rằng cùng một weather_server.py có thể đăng ký với Claude Code (claude mcp add weather -- python /đường/dẫn/tới/weather_server.py) hoặc Gemini CLI mà không phải sửa server. Đó là ý "viết một lần, mọi MCP client dùng được".

Chạy và quan sát
1. Mở 02-mcp-basics/weather_server.py. Tìm @mcp.tool() và hàm get_weather, rồi so độ dài khai báo với schema ở bước 1.
2. Từ thư mục gốc repo, với .venv đang kích hoạt, chạy client:
cd 02-mcp-basics
python weather_client.py
Chép
1. So output với kết quả mong đợi trong README của bước:
Tools server cung cấp:
  - get_weather: Lấy thời tiết hiện tại của một thành phố.

call_tool get_weather(city='Hanoi'):
  -> Hanoi: 29°C, trời mưa

call_tool get_weather(city='Danang'):
  -> Danang: 30°C, nhiều mây

call_tool get_weather(city='Haiphong'):
  -> Haiphong: 33°C, mưa rào
Chép
1. Chụp terminal có đủ dòng Tools server cung cấp: và ba lần call_tool. Lưu thành screenshots/02-mcp-client.png.
Checkpoint
Bước này đạt khi dòng đầu output liệt kê get_weather kèm mô tả, và mô tả đó chính là docstring trong weather_server.py. Đây là bằng chứng schema được server tự công bố. Ba kết quả call_tool cho thấy server là bên thực thi, còn client chỉ nhận chuỗi trả về.

Lưu ý bước này chưa có model. Trong luồng đầy đủ, LLM dùng Function Calling để chọn tool từ danh sách list_tools(). Bạn sẽ thấy luồng đó ở bước 4. Trước đó, bước 3 bổ sung những thứ một MCP server cần có khi chạy qua mạng.


Bước 3 — MCP trong production: auth, Tool Registry và versioning
Server ở bước 2 chạy qua stdio trên cùng máy, ai khởi động được tiến trình là gọi được tool. Khi đưa vào production, README gốc nêu ba vấn đề phải giải quyết: xác thực khi phục vụ qua HTTP, cách agent tìm đúng tool khi có nhiều server, và cách nâng cấp tool mà không làm hỏng client cũ. Thư mục 03-production/ có một demo nhỏ cho từng vấn đề. Bạn chạy cả ba demo, mỗi demo là một ảnh bằng chứng.

3a. Authentication — Bearer token qua Streamable HTTP
auth_server.py không chạy qua stdio nữa mà qua Streamable HTTP, tại http://localhost:8000/mcp. Server được cấu hình AuthSettings và một StaticTokenVerifier. Class này kế thừa TokenVerifier và trả về AccessToken với scope weather:read khi token có trong danh sách hợp lệ. Danh sách gồm giá trị của MCP_AUTH_TOKEN (mặc định dev-token-abc123) và prod-key-xyz789.

Điểm đáng chú ý trong code: hàm get_weather không có dòng nào liên quan đến auth. Theo README, SDK xử lý việc này ở tầng transport. Thiếu token thì server trả 401, token sai thì 403. Phía client, auth_client.py tạo HTTP client bằng create_mcp_http_client(headers={"Authorization": f"Bearer {TOKEN}"}), với TOKEN đọc từ MCP_AUTH_TOKEN hoặc mặc định dev-token-abc123.

1. Mở terminal 1, kích hoạt .venv, rồi khởi động server:
cd 03-production
python auth_server.py
Chép
1. Mở terminal 2, kích hoạt .venv, rồi chạy client với token mặc định:
cd 03-production
python auth_client.py
Chép
Bạn sẽ thấy dòng Tools (có auth): liệt kê get_weather, sau đó là Kết quả: Hanoi: 29°C, trời mưa.

1. Vẫn ở terminal 2, đặt một token không có trong danh sách hợp lệ rồi chạy lại client. Lần này client không in được danh sách tool, vì request bị server từ chối.
Chạy client với token sai
macOS / Linux
Windows PowerShell
MCP_AUTH_TOKEN=wrong-token python auth_client.py
Chép
1. Chụp hai ảnh: lần chạy thành công lưu thành screenshots/03a-auth-ok.png, lần bị từ chối lưu thành screenshots/03a-auth-fail.png. Ảnh lần bị từ chối nên có cả terminal client lẫn log của server nếu server in ra mã lỗi.
2. Quay lại terminal 1 và dừng auth_server.py bằng Ctrl+C.
Giải phóng cổng 8000
auth_server.py dùng cổng 8000, cũng là cổng mà adk web dùng ở bước 4. Nếu quên dừng server này, giao diện ADK sẽ không mở được.

3b. Tool Registry — agent tìm tool theo tag
Trong các bước trước, client biết sẵn phải kết nối tới server nào. registry.json đổi cách tiếp cận đó. Đây là một danh mục tool-centric: mỗi mục là một tool, có description, parameters, tags, server, version và deprecated, kèm phần servers mô tả cách kết nối (stdio hoặc streamable-http, có hoặc không có auth). Agent không hỏi "server nào?" mà hỏi "tool nào có tag weather?".

registry_client.py dùng ToolRegistry.search(tag=...) để lọc tool, best_match() để chọn bản có version cao nhất và không deprecated, rồi connect_and_call() để tự kết nối đúng transport và gọi tool. README ghi rõ đây là bản JSON minh hoạ; production sẽ thay bằng DB hoặc API có semantic search.

1. Từ 03-production/, chạy:
python registry_client.py
Chép
1. Đối chiếu với kết quả mong đợi trong README của bước: phần === Tool Registry === liệt kê các tool, phần --- Agent cần tool có tag "weather" --- cho biết Tìm thấy 2 tool(s) (get_weather v1.0.0 và get_weather_v2 v2.0.0), rồi Best match: get_weather_v2 v2.0.0 và dòng Kết quả:.
2. Chụp phần output từ --- Agent cần tool có tag "weather" --- đến Kết quả:, lưu thành screenshots/03b-registry.png.
3c. Versioning — v1 và v2 chạy song song
Bài toán ở đây: tool v1 get_weather(city) trả về một chuỗi đơn giản, v2 muốn trả JSON chi tiết và thêm forecast. Nếu sửa thẳng tool cũ, mọi client đang dùng nó sẽ hỏng. versioned_server.py kết hợp ba kỹ thuật được README nêu:

Kỹ thuật	Trong versioned_server.py
Tool mới song song	get_weather (v1, deprecated) vẫn chạy bên cạnh get_weather_v2
Tham số optional	include_forecast, units có giá trị mặc định
Server metadata	Resource server://info công bố version, tool deprecated, hướng dẫn chuyển đổi
1. Từ 03-production/, chạy client. Client tự khởi động server qua stdio:
python versioned_client.py
Chép
1. Kiểm tra output theo thứ tự: Server: weather-v2 v2.0.0, Deprecated tools: ['get_weather'], dòng Migration:, danh sách Tools:, kết quả [v1] get_weather('Hanoi'): dạng chuỗi, rồi [v2] get_weather_v2('Hanoi', forecast=True): dạng JSON có "api_version": "2.0".
2. Chụp toàn bộ output, lưu thành screenshots/03c-versioning.png.
Checkpoint
Bước 3 đạt khi bạn có đủ bốn ảnh 03a-auth-ok, 03a-auth-fail, 03b-registry, 03c-versioning và đã dừng auth_server.py. Mỗi ảnh ứng với một dòng trong bảng "Production Checklist" của README gốc: transport HTTP có auth, discovery qua registry thay vì hard-code, và tool v1 + v2 song song có thông báo deprecated.

Bước 4 dùng lại hai ý từ đây: server chạy qua Streamable HTTP thay vì stdio, và client tự khám phá tool thay vì biết trước.


Bước 4 — Chạy MCP server thật với WeatherAPI
Từ bước này bạn rời dữ liệu mock. 04-lab/mcp-server/weather.py là một FastMCP server gọi REST API của WeatherAPI.com và công bố ba tool qua Streamable HTTP tại http://localhost:8085/mcp. Bạn dựng server này trước, vì agent ở bước 5 sẽ kết nối tới nó ngay khi khởi động.

Kiến trúc bạn đang dựng
Lab 04 có ba thành phần, nối với nhau theo một chiều:

Kiến trúc Lab 04
Streamable HTTP :8085/mcp

REST

ADK Agent (mcp-client)

MCP Server (mcp-server)

WeatherAPI.com

Server đứng giữa: phía agent nó nói giao thức MCP, phía WeatherAPI nó gọi REST. Agent không biết gì về WeatherAPI hay API key của nó. Agent chỉ thấy ba tool mà server công bố.

Ba tool và cách server chọn transport
Tool	Việc nó làm
get_current_weather(city)	Gọi current.json, trả nhiệt độ, cảm giác như, điều kiện, độ ẩm, gió, áp suất, UV, tầm nhìn và Last updated
get_forecast(city, days)	Gọi forecast.json, trả dự báo theo ngày; days bị giới hạn tối đa 3 (gói miễn phí)
health_check()	Trả chuỗi xác nhận server đang chạy
Server đọc key từ biến môi trường WEATHERAPI_KEY. Nếu thiếu, tool không lỗi mà trả về chuỗi ❌ WeatherAPI key not configured.... Vì vậy, nếu agent trả lời bằng câu đó thì nguyên nhân nằm ở terminal của server, không phải ở agent.

Phần if __name__ == "__main__": quyết định transport. Server chạy Streamable HTTP khi có biến PORT (trường hợp Cloud Run) hoặc khi được chạy trực tiếp trong terminal tương tác (sys.stdin.isatty()). Ngoài hai trường hợp đó, server chuyển sang chế độ stdio. Đây là lý do bạn phải khởi động server trong một terminal thật.

Chạy server
1. Mở một terminal mới dành riêng cho server. Bạn không cần .venv của bước 01–03, vì uv tự quản lý môi trường của thư mục này.
2. Cài dependency, đặt key và khởi động server:
Khởi động MCP server
macOS / Linux
Windows PowerShell
cd 04-lab/mcp-server
uv sync
export WEATHERAPI_KEY="your_weatherapi_key"
uv run python weather.py
Chép
1. Xác nhận terminal in ba dòng sau, theo đúng các lệnh print trong weather.py:
✅ MCP server initialized with Streamable HTTP transport
🔧 Available tools: get_current_weather, get_forecast, health_check
🚀 Starting MCP server on http://0.0.0.0:8085/mcp
Chép
1. Để nguyên terminal này chạy suốt bước 5. Nếu cổng 8085 đã bị chiếm, README cho phép đổi cổng bằng biến PORT; khi đó bạn cũng phải đổi MCP_SERVER_URL ở phía client cho khớp.
Checkpoint
Server sẵn sàng khi bạn thấy dòng 🚀 Starting MCP server on http://0.0.0.0:8085/mcp và terminal không thoát. Nếu thấy Starting FastMCP server in stdio mode for local client, server đang ở chế độ stdio và agent sẽ không kết nối được. Hãy chạy lại lệnh trực tiếp trong terminal.

Chưa cần chụp ảnh ở đây. Bằng chứng server hoạt động sẽ nằm trong ảnh verify_setup.py và câu trả lời của agent ở bước 5.


Bước 5 — Kết nối agent Google ADK và hỏi thời tiết thật
Đây là chặng ghép mọi thứ lại. Ở bước 2 bạn viết client thủ công bằng ClientSession và tự gọi call_tool. Ở đây, Google ADK đóng vai MCP client và lo toàn bộ vòng lặp Function Calling mà bạn đã thấy ở bước 1, chỉ khác là tool giờ nằm trên server của bước 4.

ADK làm gì trong Lab này
README của Lab 04 mô tả năm việc ADK đảm nhận:

1. Kết nối tới MCP server qua Streamable HTTP bằng StreamableHTTPConnectionParams(url=...).
2. Khám phá tool tự động: McpToolset gọi list_tools và nhận về get_current_weather, get_forecast, health_check.
3. Truyền tool cho model: Agent(model="gemini-2.5-flash", tools=[weather_tools]).
4. Điều phối vòng lặp Function Calling: Gemini chọn tool, ADK gọi MCP server, nhận kết quả rồi đưa lại cho Gemini tổng hợp.
5. Cung cấp giao diện web qua adk web tại http://localhost:8000.
So với bước 1, việc 3 và 4 chính là FunctionDeclaration cùng vòng while resp.function_calls, nhưng giờ ADK làm thay bạn, và schema đến từ server thay vì viết tay. So với bước 2, việc 1 và 2 là ClientSession cùng list_tools(), chỉ đổi transport từ stdio sang HTTP.

Đọc weather_agent/agent.py trước khi chạy
File này đọc MCP_SERVER_URL từ môi trường, mặc định http://localhost:8085/mcp, và đặt timeout=30.0 (comment trong code ghi là để chịu được cold start trên Cloud Run). Nếu tạo McpToolset thất bại, file ghi log lỗi rồi tạo một fallback agent không có tool. Agent đó vẫn chat được, nhưng chỉ bằng kiến thức của model, không có dữ liệu thời tiết thật. Vì thế, "agent trả lời được" chưa đủ để kết luận đạt; bạn phải kiểm tra câu trả lời có dùng dữ liệu từ tool hay không.

Chạy agent
1. Mở terminal thứ hai, giữ terminal server đang chạy. Vào thư mục client, cài dependency và tạo .env chứa Gemini key:
cd 04-lab/mcp-client
uv sync
echo "GOOGLE_API_KEY=your_gemini_api_key" > .env
Chép
Trên Windows PowerShell, đừng dùng echo ... > .env: lệnh này có thể ghi file với encoding mà python-dotenv không đọc được. Thay vào đó, tạo file .env trong 04-lab/mcp-client bằng trình soạn thảo (ví dụ VS Code), lưu ở UTF-8 với đúng một dòng GOOGLE_API_KEY=..., rồi chạy uv sync như trên.

1. Kiểm tra toàn bộ cấu hình bằng script có sẵn. Script kiểm tra .env, dependency, cấu trúc weather_agent/, kết nối tới MCP server và việc import root_agent:
uv run python verify_setup.py
Chép
Kết quả cần có là dòng ✅ All checks passed!. Ở mục kết nối, script gửi một GET thuần tới endpoint MCP; nó vẫn coi là đạt nếu mã trả về dưới 500, kể cả 400, 405 hay 406. Chụp output này, lưu thành screenshots/04-verify-setup.png.

1. Khởi động giao diện web:
uv run adk web
Chép
1. Mở http://localhost:8000, chọn weather_agent trong dropdown, rồi hỏi hai câu, một câu buộc agent dùng get_current_weather và một câu dùng get_forecast. Ví dụ, lấy từ README của client: "What's the weather in Brisbane?" và "Give me a 3-day forecast for Tokyo". Bạn cũng có thể hỏi bằng tiếng Việt về Hanoi, Danang hay Haiphong.
2. Chụp hai ảnh giao diện chat, mỗi ảnh có câu hỏi và câu trả lời. Nếu giao diện hiển thị sự kiện gọi tool, hãy để nó lọt vào khung hình. Lưu thành screenshots/04-adk-current.png và screenshots/04-adk-forecast.png.
Checkpoint
Bước 5 đạt khi câu trả lời chứa dữ liệu chỉ WeatherAPI mới có. Câu hỏi thời tiết hiện tại phải ra các con số cụ thể, như cảm giác như, độ ẩm, UV, kèm thời điểm cập nhật, không phải giá trị mock 29°C, trời mưa của các bước trước. Câu hỏi dự báo phải ra từng ngày với nhiệt độ cao/thấp và khả năng mưa, tối đa 3 ngày.

Nếu agent trả lời chung chung hoặc nói không có dữ liệu, kiểm tra log của adk web xem có dòng ❌ Failed to connect to remote MCP server không. Nếu có, agent đang chạy ở chế độ fallback. Bật lại server ở bước 4, rồi khởi động lại adk web. Đến đây bạn đã đi hết chuỗi: model chọn tool bằng Function Calling, MCP đưa yêu cầu tới server, server lấy dữ liệu thật.


Tùy chọn — Deploy MCP server lên Cloud Run
Phần này không bắt buộc. Nó chỉ dành cho bạn nào muốn agent kết nối tới một server từ xa thay vì localhost. Repo đã chuẩn bị sẵn những gì cần cho việc này, nhưng không kèm lệnh deploy cụ thể. Hãy làm theo tài liệu Cloud Run chính thức của Google Cloud và giữ đúng các điểm sau từ repo:

04-lab/mcp-server/Dockerfile build từ python:3.12-slim, cài dependency từ pyproject.toml và chạy python weather.py.
Cloud Run đặt biến PORT. Khi có PORT, weather.py tự chạy Streamable HTTP ở đúng cổng đó, nên bạn không cần sửa code.
Đặt WEATHERAPI_KEY thành biến môi trường của service. Không đưa key vào Dockerfile.
Trong 04-lab/mcp-client/.env, thêm MCP_SERVER_URL=https://<service>.run.app/mcp, tức URL service của bạn cộng /mcp. Cả agent.py lẫn verify_setup.py đều đọc biến này.
Bạn biết mình đã xong khi verify_setup.py báo MCP server reachable at https://...run.app/mcp và agent trả lời dữ liệu thật như ở bước 5. Nếu làm phần này, chụp output verify_setup.py có URL Cloud Run, lưu thành screenshots/05-cloud-run.png. Tuyệt đối không để key lộ trong ảnh.


Nộp bài
Bạn nộp một repo cá nhân qua VLearn. Repo là bản fork đã đổi tên, chứa toàn bộ code của bạn cùng thư mục ảnh bằng chứng. Người chấm mở repo và đối chiếu từng ảnh với checkpoint của bước tương ứng, nên ảnh cần đủ rõ để đọc được output.

Cấu trúc repo cần có
KX-DAY26-HoVaTen-MSSV/
├── 01-function-calling/
├── 02-mcp-basics/
├── 03-production/
├── 04-lab/
├── screenshots/
│   ├── 01-function-calling.png
│   ├── 02-mcp-client.png
│   ├── 03a-auth-ok.png
│   ├── 03a-auth-fail.png
│   ├── 03b-registry.png
│   ├── 03c-versioning.png
│   ├── 04-verify-setup.png
│   ├── 04-adk-current.png
│   ├── 04-adk-forecast.png
│   └── 05-cloud-run.png      ← chỉ khi làm phần tùy chọn
├── README.md
└── requirements.txt
Chép
Tên repo phải đúng định dạng KX-DAY26-HoVaTen-MSSV. Đây là tên bạn đặt khi fork ở chặng chuẩn bị.

Các bước đóng gói
1. Kiểm tra git status để chắc chắn không có file .env hay file chứa key nào được stage. .gitignore đã bỏ qua .env, nhưng hãy xem lại lần cuối.
2. Mở từng ảnh trong screenshots/ và xác nhận không ảnh nào lộ Gemini key hay WeatherAPI key.
3. Commit thư mục screenshots/ và push lên repo fork của bạn trên GitHub.
4. Mở repo trên GitHub ở chế độ ẩn danh hoặc nhờ bạn khác mở thử, để chắc chắn người chấm xem được repo và ảnh.
5. Nộp link repo qua VLearn.
Trước khi bấm nộp0/5

Tên repo đúng `KX-DAY26-HoVaTen-MSSV`.

Đủ 9 ảnh bắt buộc trong `screenshots/`.

Ảnh `04-adk-current` và `04-adk-forecast` có dữ liệu WeatherAPI thật.

Không có key nào trong commit hay trong ảnh.

Người khác mở được link repo.