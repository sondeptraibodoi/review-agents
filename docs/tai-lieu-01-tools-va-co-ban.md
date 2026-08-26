# TÀI LIỆU 01

## L8 Principal's Agentic Engineering Workflow — Tools & Hướng dẫn sử dụng cơ bản

> **Tác giả video:** Kun Chen (Cựu Late Principal Engineer tại Meta, Microsoft, và Atlassian) [87]
> **Tài liệu được biên soạn bởi:** Gemini Notebook (Senior Technical Writer & AI Tools Analyst)

---

### 1. Tổng quan

Trong kỷ nguyên phát triển phần mềm được hỗ trợ bởi trí tuệ nhân tạo, kỹ sư lập trình cần phải chuyển dịch tư duy từ một **"thủy thủ" (sailor) tự mình gõ code thủ công** sang một **"thuyền trưởng" (captain) điều hành một thủy thủ đoàn gồm các AI Agent tự trị** [4, 89, 165]. 

Hệ thống được giới thiệu trong video giải quyết bài toán **tối ưu hóa hiệu suất lập trình hàng ngày (shipping 40-50 production-ready commits/PRs mỗi ngày)** bằng cách xây dựng một môi trường làm việc tập trung vào bàn phím (terminal-centric) kết hợp với các công cụ tự động hóa quy trình (agentic workflows) [2, 5, 88, 91]. Mục tiêu cuối cùng là giảm thiểu tối đa "context switch" (chuyển đổi ngữ cảnh), giải phóng lập trình viên khỏi các công việc lặp đi lặp lại (như duyệt diff, viết test thủ công) để tập trung hoàn toàn vào tầm nhìn sản phẩm và tư duy chiến lược [5, 6, 54, 55, 62].

Hệ thống này phù hợp với:
* Các kỹ sư phần mềm chuyên nghiệp muốn nhân bản hiệu suất lập trình cá nhân lên gấp nhiều lần.
* Các Tech Lead, Engineering Manager muốn áp dụng các quy trình tiêu chuẩn hóa (SOPs) cho AI để đảm bảo chất lượng code đầu ra.
* Những ai muốn xây dựng quy trình lập trình tự động, chạy xuyên đêm ngay cả khi đang ngủ [63].

---

### 2. Kiến trúc tổng quan

Kiến trúc vận hành của quy trình kỹ thuật Agentic này được chia thành các tầng rõ rệt, phối hợp mượt mà từ lúc tiếp nhận yêu cầu bằng giọng nói cho đến khi xuất bản mã nguồn an toàn lên Production:

```text
+---------------------------------------------------------------------------------+
|                                USER (CAPTAIN)                                   |
|               Nhập lệnh bằng giọng nói (3x tốc độ gõ phím thông thường)          |
+---------------------------------------------------------------------------------+
                                        │ (Open Super Whisper - Local Whisper) [41, 125]
                                        ▼
+---------------------------------------------------------------------------------+
|                              FIRST MATE (TRỢ LÝ TRỰC CA)                        |
|       Nhận chỉ thị từ Thuyền trưởng, điều phối và phân rã thành nhiều Task con     |
+---------------------------------------------------------------------------------+
                                        │ (Tự động hóa qua tmux & Treehouse) [79, 161]
                                        ▼
+---------------------------------------------------------------------------------+
|                           TREEHOUSE (MÔI TRƯỜNG SONG SONG)                      |
|       Tự động clone và quản lý độc lập các Git Worktrees để tránh xung đột file   |
+---------------------------------------------------------------------------------+
        │                               │                               │
        ▼ (Nhánh song song 1)            ▼ (Nhánh song song 2)            ▼ (Nhánh song song 3)
+───────────────────────+       +───────────────────────+       +───────────────────────+
|     AI CREWMATE 1     |       |     AI CREWMATE 2     |       |     AI CREWMATE 3     |
| (Cloud Code/Codex...) |       | (Cloud Code/Codex...) |       | (Cloud Code/Codex...) |
+───────────────────────+       +───────────────────────+       +───────────────────────+
  (Tuân thủ Global/Project Memory, giao tiếp qua AXI Standards để tối ưu chi phí token) [23, 29, 44]
        │                               │                               │
        └───────────────────────────────┼───────────────────────────────┘
                                        ▼ (Chuyển giao mã nguồn)
+---------------------------------------------------------------------------------+
|                        NO MISTAKES PIPELINE (QA TỰ ĐỘNG)                        |
|   Rebase origin -> Adversarial Review -> End-to-End Test (Lấy bằng chứng) -> PR  |
+---------------------------------------------------------------------------------+
                                        │
                                        ▼
+---------------------------------------------------------------------------------+
|                               MERGED & SHIPPED                                  |
|   Thuyền trưởng chỉ việc kiểm tra bằng chứng (screenshot/video/log) & click Merge|
+---------------------------------------------------------------------------------+
```

---

### 3. Danh sách tools

| Tool | Vai trò | Bắt buộc? | Dùng ở bước nào |
| :--- | :--- | :--- | :--- |
| **WezTerm** | Trình giả lập Terminal hiệu năng cao, hỗ trợ đa nền tảng và cấu hình bằng Lua [8, 9, 94, 95]. | Có | Toàn bộ quy trình |
| **tmux** | Bộ dồn kênh terminal (multiplexer), phân chia màn hình thành nhiều pane/tab và giữ session chạy liên tục trên server [11, 12, 96, 97]. | Có | Quản lý đa nhiệm, chạy Agent song song |
| **Neovim** | Trình soạn thảo văn bản hiện đại kế thừa Vim, tập trung thao tác 100% trên bàn phím [15, 100]. | Có | Soạn thảo, tìm kiếm và viết mã nguồn |
| **Cloud Code (Claude Code)** | Agent harness chính thức của Anthropic để trực tiếp thao tác code [19, 104]. | Không (có thể thay thế) | Viết code, debug, phân tích và thực thi tác vụ |
| **Codex CLI / Pi / Open Code** | Các Agent harnesses mã nguồn mở, hỗ trợ đa model và có khả năng tùy biến cao [20, 21, 105, 106]. | Không | Giải pháp thay thế hoặc chạy đa model |
| **Open Super Whisper** | Công cụ chuyển giọng nói thành văn bản cục bộ (local Whisper), giúp giao tiếp với Agent nhanh hơn gấp 3 lần [41, 125]. | Không | Giao chỉ thị (Prompting) cho Agent |
| **AXI Standard** | Chuẩn thiết kế tối ưu công thái học cho Agent (Agent Ergonomics), giảm token và latency [44, 128]. | Không | Giao tiếp API và CLI của Agent với các công cụ ngoài |
| **Lavish Axi** | Editor trực quan giúp hiển thị Prototype dưới dạng HTML và thu thập feedback tương tác từ người dùng [46, 50, 130, 133]. | Không | Lập kế hoạch (Planning) cho tính năng phức tạp |
| **No Mistakes** | Pipeline tự động hóa kiểm soát chất lượng từ code nháp đến PR hoàn chỉnh [56, 139]. | Có (trong Agent Flow) | Kiểm duyệt, test và tạo PR |
| **gnhf (Good Night, Have Fun)** | Vòng lặp Agent chạy liên tục qua đêm với điều kiện dừng thiết lập trước [34, 147]. | Không | Tác vụ dài hạn (Long-running tasks) |
| **Treehouse** | Công cụ quản lý Git Worktree tự động để chạy nhiều Agent cùng lúc không bị xung đột [71, 154]. | Có (khi chạy song song) | Tách biệt thư mục dự án cho từng Agent |
| **First Mate** | Agent điều phối cấp cao quản lý toàn bộ các Agent con và các công cụ khác [75, 76, 158, 159]. | Không | Quản lý quy trình khi số lượng Agent tăng lên nhiều |

---

### 4. Hướng dẫn từng tool

#### A. WezTerm
* **WezTerm là gì?** Là một trình giả lập terminal hiện đại, viết bằng Rust, cực kỳ mượt mà và hỗ trợ kết xuất đồ họa bằng GPU [8, 9, 94].
* **Vai trò:** Đóng vai trò là "vỏ tàu" - nơi chứa toàn bộ giao diện làm việc của bạn [4, 90].
* **Khi nào nên dùng:** Dùng mọi lúc khi phát triển phần mềm vì nó có khả năng tùy biến vô hạn và hiệu suất vẽ chữ cực nhanh [9, 10, 95].
* **Thành phần liên quan:** File cấu hình `wezterm.lua` [10, 95].
* **Dependency:** Chạy trực tiếp trên hệ điều hành (Mac, Windows, Linux) và hỗ trợ hoàn hảo phông chữ lập trình [9, 94].

#### B. tmux
* **tmux là gì?** Là bộ dồn kênh terminal (Terminal Multiplexer) cho phép bạn chia một cửa sổ terminal thành nhiều pane (ô) và window (tab) độc lập [11, 12, 96, 97].
* **Vai trò:** Là "boong tàu" - nơi phân chia không gian cho các thành viên trong đoàn [4, 90]. Bạn có thể để một pane cho Agent chạy, một pane mở Neovim soạn thảo, một pane gõ lệnh riêng [12, 97]. Sessions của tmux lưu trên server, giúp bạn có thể tắt máy tính ở công ty, về nhà mở điện thoại hoặc laptop ra kết nối lại đúng trạng thái cũ [13, 98].
* **Thành phần liên quan:** File cấu hình `.tmux.conf` [14, 99].
* **Dependency:** Cần cài đặt trên môi trường Linux/Mac thông qua terminal [14, 99].

#### C. Neovim
* **Neovim là gì?** Là phiên bản hiện đại hóa của trình soạn thảo Vim huyền thoại, tối ưu cho việc viết code bằng bàn phím [15, 100].
* **Vai trò:** "Bút vẽ" của lập trình viên, giúp di chuyển, tìm kiếm và chỉnh sửa code với tốc độ cực nhanh mà không cần dùng đến chuột [15, 17, 100, 102].
* **Khi nào nên dùng:** Khi bạn muốn đạt trạng thái "Flow" tối đa trong lúc code, không bị gián đoạn vì phải di chuyển tay sang chuột [6, 92].
* **Thành phần liên quan:** relative line numbers (dòng tương đối), Telescope (hoặc plugin tìm kiếm qua phím `Space S` và `Space F`) [16, 17, 101, 102].

#### D. Agent Harnesses (Khung vận hành Agent)
* **Cloud Code (Claude Code):** Phù hợp nhất nếu bạn dùng gói trả phí của Anthropic, có trải nghiệm mặc định cực tốt và nhiều tính năng đi kèm nhưng khó tùy chỉnh và đôi khi gặp lỗi vặt [19, 104].
* **Codex CLI:** Viết bằng Rust, mượt mà hơn Claude Code, mã nguồn mở nên Agent tự sửa lỗi của chính nó được, nhưng thiếu các tính năng trang trí rườm rà [20, 105].
* **Pi:** Cực kỳ tối giản, được thiết kế để mở rộng và can thiệp (tinker) theo ý muốn [21, 105].
* **Open Code:** Giao diện TUI đẹp mắt, hỗ trợ mượt mà mọi mô hình AI, đầy đủ tính năng ăn liền [21, 106].
* **Mối quan hệ:** Tất cả các Agent harnesses này đều đọc chung một quy chuẩn Memory và Skills để hoạt động đồng nhất (Agent-agnostic workflow) [22, 107].

#### E. Open Super Whisper
* **Open Super Whisper là gì?** Ứng dụng transcription cục bộ chạy mô hình Whisper của OpenAI ngay trên phần cứng của bạn [41, 125].
* **Vai trò:** "Bộ đàm" truyền tin. Thay vì gõ tay một câu prompt dài, bạn chỉ cần nói và phần mềm sẽ gõ lại chính xác [39, 41, 123, 125].
* **Khi nào nên dùng:** Khi gõ prompt lập kế hoạch hoặc mô tả lỗi (nhanh hơn gõ phím gấp 3 lần) [39, 40, 123, 124]. Chỉ gõ tay khi cần đưa vào đường dẫn file hoặc URL [42, 125].

#### F. AXI (Agent Ergonomics Standards)
* **AXI là gì?** Tiêu chuẩn thiết kế dành riêng cho Agent, coi Agent là "công dân hạng nhất" khi sử dụng các công cụ [44, 128].
* **Vai trò:** Giảm hao phí token và latency. Ví dụ, sử dụng GitHub MCP mặc định tốn gấp 3 lần token và gấp đôi latency so với sử dụng CLI chi tiết thông qua AXI [43, 127].
* **Khi nào nên dùng:** Khi viết công cụ hoặc CLI cho Agent gọi, áp dụng định dạng xuất dữ liệu tiết kiệm token thay vì JSON cồng kềnh (tiết kiệm đến 40% token) [44, 128].

---

### 5. Setup Tool

Dưới đây là các bước thiết lập thực tế được tác giả chia sẻ trực tiếp:

#### Bước 1: Cấu hình WezTerm
1. Tạo file cấu hình `wezterm.lua` trong thư mục dotfiles của bạn [10, 95].
2. Để thay đổi giao diện, viết Lua script gán giá trị màu sắc, ví dụ:
   ```lua
   config.color_scheme = 'Rose Pine Moon' -- Hoặc 'Chalk' để đổi giao diện tức thì
   ```
   [10, 95, 96]
3. Lưu file, WezTerm sẽ tự động thực hiện **hot reload** ngay lập tức mà không cần khởi động lại terminal [10, 96].

#### Bước 2: Khởi động tmux
1. Mở WezTerm, gõ lệnh khởi động tmux session:
   ```bash
   tmux
   ```
   [11, 96, 97]
2. Cấu hình file `.tmux.conf` để hiển thị thanh trạng thái (status bar) chứa metadata hữu ích và tab bar (thường hiển thị ở đầu màn hình) [11, 14, 96, 97, 99].

#### Bước 3: Cấu hình Neovim hiển thị số dòng tương đối (Relative Line Numbers)
1. Trong file config của Neovim (thường là `init.lua`), bật tính năng relative line numbers:
   ```lua
   vim.wo.number = true
   vim.wo.relativenumber = true
   ```
   [16, 101] (Tính năng này giúp bạn biết chính xác dòng đích cách dòng hiện tại bao nhiêu dòng để nhảy nhanh bằng phím tắt, ví dụ: gõ `11k` để nhảy lên 11 dòng [16, 17, 101, 102]).
2. Cấu hình các phím nóng tìm kiếm:
   * `Space S`: grep tìm chữ trong toàn bộ thư mục [17, 102].
   * `Space F`: tìm file theo tên [17, 102].

#### Bước 4: Tạo liên kết biểu tượng (Symbolic Link) cho Memory của Agent
Tác giả chia sẻ mẹo liên kết file memory của các Agent khác nhau về cùng một file vật lý để dùng chung nội dung onboarding [23, 24, 108]:
1. Sử dụng lệnh tạo symbolic link để liên kết file memory của Claude Code và các Agent khác:
   ```bash
   ln -s ~/.config/claude/memory.md ~/agents.md
   ```
   *(Cú pháp tượng trưng dựa trên hành động tạo link của tác giả để đồng nhất file `MD` của các agent [24, 108]).*

#### Bước 5: Cấu hình từ vựng chuyên ngành trong Open Super Whisper
1. Mở phần cấu hình của **Open Super Whisper** trên máy Mac của bạn [41, 125].
2. Vào **Model menu** -> **Transcription menu** -> Tìm mục **Initial Prompt** [77, 160].
3. Điền các từ vựng kỹ thuật hay dùng trong dự án của bạn (ví dụ: *lavish axi, github axi, chrome dev tools axi, no-mistakes, treehouse*) vào trường này [76, 77, 125, 159, 160].
4. Lưu cấu hình. Mô hình Whisper sẽ tự động nhận diện cực kỳ chính xác các thuật ngữ khó này khi bạn nói [77, 78, 160].

---

### 6. Hướng dẫn sử dụng cơ bản

Để làm quen với môi trường này trước khi đi vào workflow lớn, bạn hãy thực hành một luồng công việc tối giản sau:

#### Quy trình: Thao tác bằng Giọng nói -> Agent Thực thi -> Tạo Skill

1. **Kích hoạt Voice Input:** Nhấn phím nóng của Open Super Whisper và nói chỉ thị của bạn [41, 125]:
   > *"Explain this repo in a concise way and give me a recap of what the recent PRs have been working on."* [39, 123]
2. **Nhận diện kết quả:** Hệ thống tự động chuyển giọng nói thành text chuẩn xác vào ô nhập liệu của Agent [41, 125].
3. **Agent xử lý:** Nhấn Enter. Agent (ví dụ Claude Code) sẽ tự động gọi CLI của Git để quét các PR gần nhất và trả lời ngắn gọn [42, 126].
4. **Trích xuất nội dung thành Skill (Rút gọn Token):**
   * Giả sử bạn thấy file `agents.md` bị phình to bởi các hướng dẫn Test End-to-End dài dòng [31, 32, 116].
   * Chạy lệnh gõ tay hoặc nói với Agent:
     > *"Let's extract the end-to-end testing instructions in our agents.md file into a project level skill."* [32, 117]
   * Agent sẽ tự động tạo một file skill riêng trong thư mục của dự án và loại bỏ phần test dài dòng khỏi file memory chính [34, 118]. Từ nay, Agent chỉ load mô tả ngắn của skill khi bắt đầu, và chỉ đọc toàn bộ hướng dẫn test khi nó thực sự cần chạy test (được gọi là cơ chế **Progressive Disclosure - Tiết lộ tăng tiến**), giúp tiết kiệm lượng lớn token [35, 118, 119].

---

### 7. Thuật ngữ cần biết

* **Agent Harness:** Khung phần mềm chạy ở phía client để quản lý vòng đời, phân quyền, cung cấp API và giao tiếp với Agent AI (ví dụ: Claude Code, Codex CLI) [19, 21, 104, 106].
* **Terminal Multiplexer (tmux):** Công cụ quản lý nhiều phiên làm việc ảo trong một màn hình console duy nhất [11, 96].
* **Relative Line Numbers:** Chế độ hiển thị số dòng tương đối so với dòng hiện tại, giúp lập trình viên Vim/Neovim nhảy dòng không cần chuột [16, 101].
* **Progressive Disclosure (Tiết lộ tăng tiến):** Kỹ thuật quản lý context của AI bằng cách chỉ cung cấp thông tin chi tiết của một "Skill" khi AI quyết định kích hoạt nó, tránh nhồi nhét vào System Prompt ngay từ đầu [35, 118, 119].
* **Symbolic Link (Symlink):** Liên kết ảo trên hệ thống file trỏ tới một file vật lý thực thụ, giúp đồng bộ hóa cấu hình bộ nhớ của nhiều Agent khác nhau [23, 24, 108].
* **Agent Ergonomics (Công thái học cho Agent):** Triết lý thiết kế công cụ, CLI hoặc API tối ưu riêng cho cách đọc/hiểu của AI (như tối giản token, xuất kết quả không dùng JSON) để tăng hiệu suất và độ chính xác của Agent [44, 128].

---

### 8. Lưu ý & Best Practices

#### ⚠️ Lưu ý quan trọng từ tác giả (Cực kỳ quan trọng)
* **Tuyệt đối không cài đặt các "Skills" ngẫu nhiên trên mạng:** Ngay cả khi các repo đó có hàng chục nghìn đến hàng trăm nghìn ngôi sao GitHub (ví dụ repo `Android Skills` có tới 177,000 stars nhưng khi benchmark thực tế bằng *Program Bench* lại khiến Agent tốn thêm 5% token và cho ra kết quả tệ hơn) [36, 37, 120, 121]. Nguy hiểm hơn, các skill trôi nổi có thể ra lệnh cho Agent quét sạch ổ cứng, đánh cắp API keys, mật khẩu hoặc thông tin ngân hàng của bạn gửi ra ngoài mà bạn không hề hay biết [36, 120].
* **Không nhồi nhét quá nhiều vào Global Memory:** File global memory sẽ được gửi đi kèm với *mọi câu lệnh* trong *mọi session* của bạn. Nếu viết quá dài, bạn sẽ nhanh chóng đốt cháy hàng triệu token một cách lãng phí [24, 109]. Chỉ giữ file này dưới 30 dòng (file của tác giả là 27 dòng) [24, 108].

#### 💡 Best Practice từ tác giả
* **Sửa lỗi bằng việc Tái hiện (Reproduce) trước:** Khi Agent sửa bug, hãy huấn luyện nó luôn bắt đầu bằng việc viết một kịch bản test tái hiện lại lỗi trong môi trường thực tế (End-to-End) giống như người dùng gặp phải, thay vì chỉ viết unit test hời hợt [27, 28, 112].
* **Triệt tiêu định kiến về Chi phí Phát triển (Development Cost) của AI:** AI thường ước lượng thời gian làm việc dựa trên dữ liệu huấn luyện của con người (ví dụ ước tính làm game 3D mất vài tháng, nhưng thực tế Agent tự code chỉ mất vài phút) [26, 110, 111]. Định kiến này khiến AI thường chọn các giải pháp "mì ăn liền" kém chất lượng vì nghĩ giải pháp tốt tốn quá nhiều thời gian xây dựng [27, 111]. Hãy viết quy tắc ép AI bỏ qua yếu tố phát triển tốn kém khi đưa ra quyết định kỹ thuật [25, 110].

#### 🧠 Giải thích bổ sung (Lý do kỹ thuật)
* **Tại sao terminal lại vượt trội GUI đối với Agentic Workflow?** Vì terminal ép lập trình viên rèn luyện kỷ luật "tay luôn đặt trên bàn phím" [7, 93]. Sự nhất quán này giúp tư duy liền mạch (Flow state) [6, 92]. Đồng thời, các công cụ dòng lệnh (CLI) cực kỳ dễ dàng để Agent gọi và tương tác hơn nhiều so với việc cố gắng bắt Agent thao tác trên giao diện đồ họa phức tạp [43, 126, 127].

---

### 9. Checklist chuẩn bị trước khi build Agent Flow

Trước khi bắt đầu cấu hình Agent Flow hoàn chỉnh ở TáI LIỆU 02, hãy chắc chắn bạn đã tích vào đầy đủ các mục sau:

- [ ] **Môi trường Terminal:** Đã cài đặt WezTerm, tmux và Neovim ổn định [8, 11, 15, 94, 96, 100].
- [ ] **API Keys & Accounts:** Đã đăng ký gói trả phí Anthropic (cho Claude Code) hoặc chuẩn bị sẵn API key của các mô hình frontier (GPT-4o, Claude 3.5 Sonnet) [19, 21, 104, 106].
- [ ] **Thư mục lưu trữ:** Đã tạo thư mục lưu trữ cấu hình chung (dotfiles) để dễ liên kết symbolic link [10, 95].
- [ ] **Whisper cục bộ:** Đã tải cài đặt ứng dụng Open Super Whisper (hoặc tương đương) hoạt động bình thường trên máy [41, 125].
- [ ] **Git CLI:** Máy tính đã cài đặt Git và có quyền đẩy code (SSH/OAuth) lên GitHub cá nhân [42, 126].
