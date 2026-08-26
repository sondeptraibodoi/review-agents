# PHỤ LỤC

## L8 Principal's Agentic Engineering Workflow — Phụ lục tổng hợp nâng cao

---

### A. Danh sách các Tools chính trong hệ thống

1. **WezTerm:** Giả lập Terminal bằng Rust, cấu hình Lua [8, 9, 94, 95].
2. **tmux:** Quản lý đa cửa sổ terminal, duy trì session từ xa [11, 13, 96, 98].
3. **Neovim:** Trình soạn thảo viết code hoàn toàn bằng phím [15, 100].
4. **Cloud Code (Claude Code):** Agent lập trình chính của Anthropic [19, 104].
5. **Codex CLI / Pi / Open Code:** Các Agent harnesses mã nguồn mở thay thế [20, 21, 105, 106].
6. **Open Super Whisper:** Công cụ chuyển giọng nói thành text chạy Whisper cục bộ cực nhạy [41, 125].
7. **AXI Standard:** Hệ quy chuẩn công thái học tối ưu giao diện cho Agent [44, 128].
8. **lavish (lavish axi):** Engine vẽ prototype tương tác trên nền Web [46, 51, 130, 134].
9. **no-mistakes:** Pipeline QA tự động hóa toàn bộ luồng tạo PR sạch [56, 139].
10. **gnhf (Good Night, Have Fun):** Vòng lặp Agent thực thi xuyên đêm [64, 147].
11. **treehouse:** Quản lý tạo và tái sử dụng Git Worktree tự động [71, 154].
12. **firstmate:** Trợ lý AI trung tâm điều phối đa Agent [76, 159].

---

### B. Glossary (Thuật ngữ chuyên ngành)

* **Agentic Software Engineering (Kỹ nghệ phần mềm hướng Agent):** Phương pháp phát triển phần mềm mà trong đó lập trình viên đóng vai trò thiết kế kịch bản, quy chuẩn và giám sát chất lượng, còn các AI Agent tự trị đảm nhận việc gõ mã nguồn và sửa lỗi trực tiếp [4, 89].
* **Worktree:** Tính năng của Git cho phép bạn liên kết một kho lưu trữ (repository) duy nhất với nhiều thư mục làm việc vật lý khác nhau trên đĩa cứng, giúp bạn làm việc trên nhiều nhánh cùng một lúc mà không cần phải thực hiện stash hoặc chuyển đổi nhánh trên thư mục chính [36, 37, 56, 139].
* **Adversarial Review (Đánh giá phản biện):** Phương pháp bảo đảm chất lượng code bằng cách sử dụng một AI độc lập đóng vai trò phản biện, cố gắng tìm ra lỗi hổng, lỗi cú pháp hoặc điểm chưa tối ưu của đoạn code do một AI khác viết ra [57, 140].
* **Token Efficiency (Hiệu quả sử dụng Token):** Kỹ thuật tối ưu hóa câu prompt hoặc dữ liệu trả về của công cụ để sử dụng số lượng từ khóa (tokens) ít nhất có thể, từ đó giảm chi phí hóa đơn API và tăng tốc độ phản hồi của AI [44, 128].

---

### C. Best Practices quan trọng nhất

#### Từ tác giả (Kun Chen):
1. **Never use em dashes:** Luôn ép Agent dùng dấu gạch ngang thường `-` để tránh chữ viết của Agent bị robot [24, 25, 109].
2. **Reproduce before fixing:** Luôn bắt Agent viết code tái hiện lỗi bằng kịch bản test thực tế trước khi bắt tay vào sửa bug [27, 28, 112].
3. **Ignore development cost:** Huấn luyện Agent đưa ra quyết định dựa trên chất lượng và tính bền vững của kiến trúc, triệt tiêu suy nghĩ về chi phí thời gian viết code vì AI gõ code nhanh gấp hàng trăm lần con người [25, 27, 110, 111].
4. **Progressive Disclosure:** Di chuyển tài liệu hướng dẫn kỹ thuật dài dòng ra khỏi Memory chính và chuyển thành các Skills riêng biệt để tiết kiệm hàng ngàn USD tiền token [32, 35, 116, 119].

#### Giải thích bổ sung từ AI:
1. **Strict Token limits on overnight loops:** Khi chạy Agent tự trị qua đêm với `gnhf`, bắt buộc phải giới hạn chặt chẽ hạn mức Token và số vòng lặp tối đa để đề phòng trường hợp Agent rơi vào vòng lặp logic vô hạn do lỗi hệ thống, gây cạn kiệt tài khoản API chỉ sau một đêm [67, 150].
2. **Sandbox Execution for untrusted skills:** Không chạy các skill lạ trực tiếp trên môi trường máy thật chứa các thông tin tài chính nhạy cảm hoặc API key quan trọng [36, 120].

---

### D. Các vấn đề cần kiểm tra thêm (Thông tin chưa có chi tiết trong video)

* **Chi tiết cấu hình cụ thể của file `.tmux.conf` và `wezterm.lua`:** Tác giả chỉ lướt qua giao diện cấu hình thực tế và cho biết có rất nhiều hướng dẫn trên YouTube để tối ưu, do đó người dùng cần tự tìm hiểu sâu thêm để cá nhân hóa phím tắt gõ phím phù hợp với cơ tay của mình [10, 14, 95, 99].
* **Cách thức phân quyền và cấu hình SSH/OAuth cho các Git Worktree tự động trong Treehouse:** Video không mô tả chi tiết cách Treehouse tự động xác thực danh tính với GitHub để tạo PR, người dùng cần tự cấu hình thông qua Git credential helper hoặc SSH keys trên máy chủ cục bộ [71, 154].
* **Các kịch bản tự động kiểm thử cụ thể của No Mistakes:** Việc thiết lập ghi hình (video recording) và lấy screenshot tự động của pipeline phụ thuộc rất nhiều vào thư viện test được sử dụng (ví dụ Playwright hay Cypress) và cần phải được khai báo cụ thể cho từng dự án [57, 58, 140, 141].

---

### E. Timestamp / Source Index (Danh mục đối chiếu nguồn tin)

* **[1] - [4] / [87] - [90]:** Giới thiệu xuất thân của tác giả Kun Chen và mục tiêu của video [1, 4, 87, 90].
* **[5] - [8] / [91] - [94]:** Lý do chọn môi trường Terminal thay vì GUI [5, 8, 91, 94].
* **[8] - [10] / [94] - [96]:** Cấu hình WezTerm bằng file Lua và cơ chế hot reload [8, 10, 94, 96].
* **[11] - [14] / [96] - [99]:** Giới thiệu tmux, dồn kênh terminal và session persistence [11, 14, 96, 99].
* **[15] - [18] / [100] - [103]:** Sử dụng Neovim với Relative Line Numbers và phím tắt tìm kiếm [15, 18, 100, 103].
* **[19] - [22] / [104] - [107]:** So sánh 4 loại Agent Harnesses [19, 22, 104, 107].
* **[23] - [31] / [108] - [116]:** Thiết lập Onboarding qua Global Memory và Project Memory [23, 31, 108, 116].
* **[32] - [39] / [116] - [123]:** Trích xuất Skill, cơ chế Progressive Disclosure và an ninh của Skills [32, 39, 116, 123].
* **[39] - [42] / [123] - [126]:** Prompting bằng giọng nói với Open Super Whisper chạy local [39, 42, 123, 125].
* **[42] - [46] / [126] - [129]:** Agent Ergonomics và tiêu chuẩn thiết kế AXI [42, 46, 126, 129].
* **[46] - [53] / [129] - [137]:** Lập kế hoạch trực quan với Lavish Axi [46, 53, 129, 137].
* **[53] - [62] / [137] - [145]:** Pipeline kiểm tra tự động No Mistakes và tạo PR sạch [53, 62, 137, 145].
* **[62] - [67] / [145] - [150]:** Chạy tác vụ dài hạn qua đêm với gnhf [62, 67, 145, 150].
* **[67] - [75] / [150] - [157]:** Chạy song song đa tác vụ không xung đột với Treehouse [67, 75, 150, 157].
* **[75] - [82] / [157] - [164]:** Trợ lý trung tâm First Mate điều phối tự trị [75, 82, 157, 164].
* **[82] - [84] / [164] - [167]:** Tư duy Thuyền trưởng và tổng kết toàn bộ video [82, 84, 164, 167].
