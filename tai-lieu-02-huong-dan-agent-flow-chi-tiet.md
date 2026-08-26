# TÀI LIỆU 02

## L8 Principal's Agentic Engineering Workflow — Hướng dẫn xây dựng Agent Flow hoàn chỉnh

> **Tài liệu hướng dẫn thực hành (Implementation Guide / SOP / Hands-on Tutorial)**
> Người chưa xem video có thể thiết lập hệ thống tự trị gần giống tác giả dựa theo tài liệu này.

---

### 1. Agent Flow sẽ xây dựng

Quy trình tự trị này hoạt động như sau:
1. **Khởi đầu (Trigger):** Người dùng (Thuyền trưởng) ra chỉ thị bằng giọng nói yêu cầu phát triển một tính năng hoặc sửa đổi mã nguồn của nhiều dự án cùng lúc [39, 78, 123, 161].
2. **Lập kế hoạch (Planning):** Agent tự động kích hoạt **lavish** để vẽ ra một bản thiết kế HTML tương tác trực quan thay vì trả lời bằng chữ [50, 51, 133, 134]. Thuyền trưởng click duyệt phương án trực tiếp trên trình duyệt [52, 135].
3. **Phân rã & Phân phối (Orchestration):** Trợ lý **First Mate** nhận lệnh, gọi **Treehouse** tách dự án thành các thư mục độc lập (Git Worktrees), tự động mở các cửa sổ **tmux** chạy các Agent độc lập gánh vác từng Task song song [71, 79, 154, 161].
4. **Viết mã (Implementation):** Các Agent thực thi viết code tuân thủ nghiêm ngặt các hướng dẫn công nghệ trong file **Memory & Skills** của dự án [23, 32, 108, 116].
5. **Kiểm tra tự động (Validation):** Sau khi code xong, Agent tự chuyển giao sản phẩm cho pipeline **No Mistakes** chạy trong môi trường Worktree cô lập [56, 139].
6. **Bàn giao kết quả (Final Output):** Pipeline thực hiện Rebase, chạy adversarial review để tự sửa lỗi, chạy test E2E thu thập bằng chứng hình ảnh/video rồi tự động mở PR lên GitHub kèm bản báo cáo phân tích rủi ro chi tiết [56, 57, 58, 60, 139, 140, 141, 143].

---

### 2. Architecture (Sơ đồ vận hành dòng dữ liệu)

```text
               [ THUYỀN TRƯỞNG (KỸ SƯ) ]
                           │
             (1) Chỉ thị bằng giọng nói / Voice [39, 123]
                           ▼
              [ OPEN SUPER WHISPER ]
                           │
             (2) Chữ đã được làm sạch thuật ngữ [77, 160]
                           ▼
          [ FIRST MATE (ORCHESTRATOR AGENT) ]
                           │
             (3) Chia nhỏ task & gọi Treehouse [79, 161]
                           ▼
     ┌─────────────────────┼─────────────────────┐
     ▼ (Task 1)            ▼ (Task 2)            ▼ (Task 3)
[ TREEHOUSE Worktree 1 ] [ TREEHOUSE Worktree 2 ] [ TREEHOUSE Worktree 3 ] [71, 154]
     │                     │                     │
     ├─► [ Agent 1 ]       ├─► [ Agent 2 ]       ├─► [ Agent 3 ]    (Thực thi code) [79, 161]
     │ (Cloud Code/Codex)  │ (Cloud Code/Codex)  │ (Cloud Code/Codex)
     │                     │                     │
     ▼                     ▼                     ▼
[ NO MISTAKES Pipeline ] [ NO MISTAKES Pipeline ] [ NO MISTAKES Pipeline ] [56, 139]
     │                     │                     │
     ▼                     ▼                     ▼
[ GitHub PR + Evidence ] [ GitHub PR + Evidence ] [ GitHub PR + Evidence ] [58, 141]
                           │
                           ▼
               [ THUYỀN TRƯỞNG DUYỆT ]
```

---

### 3. Thành phần cần chuẩn bị

| Thành phần | Mục đích | Trạng thái cần có |
| :--- | :--- | :--- |
| **Dotfiles Repository** | Lưu trữ tập trung các file cấu hình `wezterm.lua`, `.tmux.conf` để dễ đồng bộ [10, 14, 95, 99]. | Đã khởi tạo Git repo cá nhân. |
| **`agents.md` (Global)** | Chứa các quy tắc cốt lõi áp dụng cho mọi dự án (VD: reproducability, anti-bias dev cost) [24, 27, 108, 112]. | Đã viết sẵn, độ dài < 30 dòng [24, 108]. |
| **npx skills CLI** | CLI quản lý và cài đặt các "Kỹ năng" được chuẩn hóa cho Agent [33, 117, 118]. | Đã cài đặt qua npm/Vercel [33, 118]. |
| **lavish repository** | Package cung cấp engine tạo prototype HTML tương tác [46, 51, 130, 134]. | Đã cài đặt và tích hợp vào agent profile [50, 133]. |
| **no-mistakes package** | Bộ kịch bản tự động kiểm tra code, rebase, review chéo và gửi PR [56, 139]. | Đã liên kết và phân quyền push branch lên GitHub origin [58, 141]. |
| **gnhf CLI** | CLI khởi chạy vòng lặp tác vụ dài hạn [64, 147]. | Đã cài đặt toàn cục (global) trên terminal [64, 147]. |
| **treehouse CLI** | Trình quản lý tái sử dụng Git Worktree để tối ưu hóa không gian lưu trữ [71, 154]. | Đã cấu hình và chạy thử `treehouse status` [71, 72, 154]. |
| **firstmate repository** | Mã nguồn của Agent trực ca First Mate điều phối [76, 159]. | Đã clone về thư mục làm việc và setup preferences [76, 77, 159]. |

---

### 4. BUILD FLOW THEO TỪNG BƯỚC

#### BƯỚC 1 — Thiết lập Onboarding cho Crewmate (Memory System)

**Mục tiêu**
Giúp các Agent mới tuyển dụng ("fresh recruits") ngay lập tức nắm được phong cách code, các quy tắc và kiến trúc của dự án mà không cần giải thích lại từ đầu ở mỗi phiên làm việc [23, 107].

**Thao tác**
1. Mở terminal, truy cập thư mục gốc của dự án (ví dụ dự án `high-bit` của tác giả) [29, 113].
2. Tạo file project memory bằng lệnh gõ tay:
   ```bash
   touch .claude-memory.md
   ```
3. Tạo liên kết symbolic link để Agent khác (như Codex) cũng đọc chung dữ liệu này:
   ```bash
   ln -s .claude-memory.md .agents-memory.md
   ```
   *(Cú pháp tượng trưng dựa trên cơ chế chia sẻ symbolic link của tác giả [29, 114]).*
4. Mở file `.claude-memory.md` bằng Neovim và nhập nội dung cấu trúc [15, 114, 115]:
   * Bối cảnh dự án (Project Context - ví dụ: "High Bit là app Twitter dành cho trẻ em") [29, 113].
   * Sơ đồ phân bổ thư mục (Repo Layout).
   * Thuật ngữ của hệ thống (Terminology).
   * Cách thức vận hành các cấu phần quan trọng nhất (Component details).
   * Quy trình kiểm thử End-to-End (E2E testing instructions).

**Configuration**
| Field | Value | Ý nghĩa |
| :--- | :--- | :--- |
| **File Name** | `.claude-memory.md` / `.agents-memory.md` [29, 113] | Tệp lưu trữ collective learning của dự án [30, 115]. |
| **Update Method** | Tự động ghi nhận lỗi của Agent và lưu kịch bản sửa lỗi vào file [31, 115]. | Giúp Agent ngày càng có kinh nghiệm [31, 115]. |

**Input** — Lịch sử lỗi sai và phản hồi điều chỉnh từ kỹ sư [31, 115].
**Output** — Tài liệu hướng dẫn phong cách lập trình của dự án ngày một hoàn thiện [31, 115].
**Vì sao cần bước này?** Tránh việc Agent lặp lại cùng một lỗi ngớ ngẩn nhiều lần, làm lãng phí token và thời gian chỉnh sửa [31, 115].
**Cách kiểm tra** — Bắt đầu một session Agent mới và hỏi: *"Hãy tóm tắt quy trình chạy Test E2E của dự án này"*. Agent phải lấy ra được thông tin chính xác từ file memory vừa tạo [30, 114].
**Kết quả mong đợi** — Agent trích xuất thông tin nhanh chóng và bắt đầu làm việc đúng chuẩn dự án [31, 115].

---

#### BƯỚC 2 — Chuyển đổi thông tin tĩnh thành Skills (Progressive Disclosure)

**Mục tiêu**
Tách các thông tin có tính điều kiện (chỉ dùng khi sửa code/chạy test) ra khỏi file Memory chính để tiết kiệm dung lượng System Prompt lúc khởi tạo Agent [32, 35, 116, 119].

**Thao tác**
1. Mở terminal và khởi chạy Agent bằng lệnh:
   ```bash
   claude
   ```
2. Cài đặt công cụ tạo skill mã nguồn mở của Anthropic:
   ```bash
   npx skills install skill-creator
   ```
   *(Cú pháp tượng trưng dựa trên công cụ `npx skills` và `Skill Creator` của Anthropic [33, 117, 118]).*
3. Ra lệnh trực tiếp cho Agent bằng giọng nói hoặc chat [32, 116]:
   > *"Let's extract the end-to-end testing instructions in our agents.md file into a project level skill."* [32, 117]
4. Agent sẽ tự phân tích, trích xuất đoạn hướng dẫn test E2E ra thành một file skill độc lập (ví dụ `e2e_test.json` hoặc dạng tương đương) và thu gọn file `agents.md` [34, 118].

**Configuration**
| Field | Value | Ý nghĩa |
| :--- | :--- | :--- |
| **Tool cài đặt** | `npx skills` (Vercel call) [33, 118] | Bộ cài đặt skill tiêu chuẩn [33, 118]. |
| **Cơ chế load** | **Progressive Disclosure** [34, 118] | Chỉ load mô tả ngắn khi khởi tạo, load chi tiết khi gọi skill [35, 119]. |

**Input** — Nội dung hướng dẫn kiểm thử thô trong file `agents.md` [32, 117].
**Output** — File skill độc lập và file `agents.md` đã được tối giản hóa dung lượng [34, 118].
**Cách kiểm tra** — Xem cấu trúc thư mục của Agent. Bạn sẽ thấy một thư mục skill được tạo ra chứa file cấu hình của skill mới [34, 118].
**⚠️ Lưu ý** — Tuyệt đối không cài các skill lạ có nhiều sao trên GitHub mà không được kiểm duyệt bảo mật vì chúng có thể đánh cắp credential ngân hàng hoặc API key lưu trên máy [36, 120].

---

#### BƯỚC 3 — Lập kế hoạch Trực quan với Lavish Axi

**Mục tiêu**
Tránh việc phải đọc những "bức tường văn bản" (wall of text) khô khan và khó hiểu khi thảo luận giải pháp với Agent trong terminal [49, 132]. Thay vào đó, lập kế hoạch trực quan bằng HTML prototype có tính tương tác [51, 134].

**Thao tác**
1. Gọi Agent và mô tả tính năng cần làm (ví dụ: gộp hai nút "what I can do" và "my progress" của app Twitter trẻ em thành một hệ thống Achievement thú vị hơn) [47, 131].
2. Không cần gõ phím, Agent sẽ tự động phát hiện yêu cầu lập kế hoạch phức tạp và khởi chạy skill **lavish** [48, 50, 132, 133].
3. Trình duyệt tự động mở ra trang hiển thị **Lavish Editor** [50, 134].
4. Bạn sẽ thấy giao diện mẫu của tính năng mới được dựng sẵn bằng chính UI/Design System của dự án [51, 134].
5. Di chuột vào giao diện, click viết bình luận trực tiếp (annotate/comment) lên các phần giao diện chưa ưng ý để gửi feedback cho Agent [52, 135].
6. Click chọn các nút quyết định (decision buttons) ở phía dưới cùng để duyệt phương án [52, 135].
7. Nhấp gửi phản hồi trực tiếp từ giao diện Web về terminal mà không cần chuyển màn hình [52, 136].
8. Khi đã hài lòng với bản mẫu, chọn nút lệnh:
   > *"Start building and we'll end the session."* [53, 136]

**Configuration**
| Field | Value | Ý nghĩa |
| :--- | :--- | :--- |
| **Planning Engine** | `lavish` [46, 130] | Công cụ kết xuất HTML UI Prototype dựa trên codebase hiện tại [51, 134]. |
| **Giao diện phản hồi** | Tích hợp bình luận và click-to-decide [52, 135]. | Tối ưu hóa giao tiếp hai chiều Người - Máy [52, 135]. |

**Input** — Ý tưởng tính năng thô từ Thuyền trưởng [47, 131].
**Output** — Bản vẽ kỹ thuật HTML có độ chân thực cao kèm danh sách quyết định được phê duyệt [51, 52, 134, 135].
**Vì sao cần bước này?** Tiết kiệm thời gian đọc báo cáo chữ, hạn chế tối đa việc hiểu sai ý giữa người lập trình và AI [51, 52, 135].

---

#### BƯỚC 4 — Tự động hóa QA và Kiểm duyệt mã nguồn với No Mistakes

**Mục tiêu**
Triệt tiêu hoàn toàn nút thắt cổ chai về thời gian khi lập trình viên phải tự mình xem xét từng dòng code thay đổi (review diff) và chạy test thủ công [54, 137].

**Thao tác**
1. Khi Agent báo đã hoàn thành mã nguồn, bạn không tự test. Thay vào đó, kích hoạt pipeline bằng cách gõ lệnh trực tiếp trong console của Agent [59, 142]:
   ```bash
   no mistakes
   ```
2. Hệ thống **No Mistakes** sẽ tự động thực hiện chuỗi hành động sau [56, 57, 58, 139, 140, 141]:
   * **Tách nhánh:** Tạo nhánh Git mới và commit các thay đổi [56, 139].
   * **Chạy Worktree cô lập:** Chuyển giao code sang một thư mục làm việc Git Worktree cô lập để không gây xáo trộn thư mục chính bạn đang thao tác [56, 139].
   * **Đồng bộ mã nguồn:** Rebase các thay đổi lên trên cùng của nhánh `main` mới nhất trên máy chủ (remote origin) và tự động xử lý các xung đột dòng code (merge conflicts) xuất hiện ban đầu [57, 140].
   * **Phản biện chéo (Adversarial Review):** Khởi chạy một phiên Agent độc lập khác trong một ngữ cảnh sạch (fresh context window) để soi lỗi nghiêm khắc. Các lỗi hiển nhiên sẽ tự sửa, các vấn đề mập mờ ảnh hưởng đến logic sản phẩm sẽ được ghi lại để gửi lên con người quyết định [57, 140].
   * **Kiểm thử hành vi E2E:** Chạy các kịch bản test thực tế và tự quay video màn hình, chụp ảnh (screenshot) hoặc ghi log hệ thống để làm bằng chứng (evidence) code hoạt động tốt [57, 58, 140, 141].
   * **Cập nhật tài liệu:** Tự động sửa đổi tất cả các tài liệu kỹ thuật liên quan để khớp với tính năng mới [58, 141].
   * **Kiểm tra cú pháp (Linting):** Đảm bảo không có lỗi trình bày code trước khi đẩy lên remote [58, 141].
   * **Đệ trình PR:** Tạo Pull Request (PR) tự động trên GitHub [58, 141].
3. Bạn mở PR trên GitHub để kiểm tra báo cáo tự động của No Mistakes bao gồm: Tóm tắt ý đồ thay đổi, Video/Hình ảnh kiểm thử, Phân tích mức độ rủi ro (Risk Assessment) [59, 60, 61, 143, 144].
4. Nếu rủi ro thấp (Low Risk), bạn nhấn nút Merge trực tiếp mà không cần đọc diff [61, 144]. Nếu rủi ro cao, bạn tiến hành kiểm tra kỹ hơn dựa trên bằng chứng thu thập được [61, 144].

**Input** — Code thô vừa được viết xong bởi Agent [56, 139].
**Output** — Pull Request hoàn chỉnh kèm bằng chứng kiểm thử hoạt động thành công [58, 60, 141, 143].
**Cách kiểm tra** — Truy cập tab Pull Requests trên GitHub của dự án và kiểm tra xem có PR mới kèm file ảnh/video bằng chứng sinh động hay không [59, 60, 143].

---

#### BƯỚC 5 — Chạy các Tác vụ Kéo dài qua đêm với Good Night, Have Fun (gnhf)

**Mục tiêu**
Giữ cho Agent hoạt động liên tục trong thời gian bạn nghỉ ngơi (7 đến 8 tiếng mỗi đêm) để giải quyết các bài toán tối ưu hóa hoặc kiểm thử không giới hạn [63, 146, 147].

**Thao tác**
1. Trước khi đi ngủ, mở terminal trong dự án và khởi chạy công cụ bằng lệnh [64, 147]:
   ```bash
   gnhf
   ```
2. Nhập một mục tiêu mang tính chất **có thể kiểm chứng (Verifiable Objective)** [64, 66, 147, 149]. Ví dụ:
   > *"Pretend you are a seven year old kid and use the high bit app end to end. Try to do different things and find the first usability problem that will confuse you as a kid, or stop you from knowing how to proceed. If you find a problem, stop and fix it, then rinse and repeat."* [64, 65, 147, 148]
3. Thiết lập các giới hạn kiểm soát để tránh lạm dụng chi phí tài khoản [67, 150]:
   * Đặt giới hạn token tối đa (Token cap).
   * Đặt giới hạn số vòng lặp tối đa (Iteration cap).
   * Đặt điều kiện dừng cụ thể (Stop conditions).
4. Nhấn Enter và tắt máy màn hình. Hệ thống sẽ hiển thị các biểu tượng Mặt Trăng (`🌑🌒🌓`) tương ứng với mỗi vòng lặp thành công và số lượng commit được tạo ra [65, 148, 149].
5. Sáng hôm sau khi thức dậy, kiểm tra nhánh Git mới và xem lại lịch sử các commits sửa lỗi tự động được Agent thực hiện trong đêm để quyết định giữ hay bỏ [65, 66, 149].

**Configuration**
| Field | Value | Ý nghĩa |
| :--- | :--- | :--- |
| **CLI Command** | `gnhf` [64, 147] | Khởi chạy vòng lặp agentic [65, 148]. |
| **Stop Conditions** | Token cap & Iteration cap [67, 150] | Ngăn ngừa việc tiêu tốn hết hạn mức (weekly quota) khi Agent lặp vô hạn [67, 150]. |

**Input** — Ứng dụng đang chạy và mục tiêu hành vi giả lập [64, 147].
**Output** — Nhánh git chứa hàng loạt commit sửa lỗi và tối ưu hóa hệ thống thành công [66, 149].
**⚠️ Lưu ý** — Chỉ áp dụng `gnhf` cho các mục tiêu có tính kiểm chứng rõ ràng hoặc tối ưu chỉ số (Metric optimization), không dùng cho các tính năng mơ hồ cần sự định hướng thẩm mỹ sâu sắc của con người [66, 67, 149, 150].

---

#### BƯỚC 6 — Vận hành Song song Đa tác vụ với Treehouse

**Mục tiêu**
Cho phép bạn chạy 3-4 Agent giải quyết các Task hoàn toàn khác nhau cùng một lúc mà không bị chồng chéo, xung đột file hoặc làm hỏng dữ liệu trong thư mục làm việc hiện tại [68, 69, 151, 152].

**Thao tác**
1. Mở một tab tmux mới [68, 151].
2. Thay vì gõ lệnh tạo Git Worktree thủ công dài dòng (`git worktree add ...`) và phải tự nhớ tên thư mục rác [69, 152, 153], hãy gõ lệnh:
   ```bash
   treehouse
   ```
   [71, 154]
3. Hệ thống sẽ tự động tạo một thư mục clone cô lập (Worktree) sạch sẽ và đưa bạn vào thẳng đó [71, 154].
4. Khởi chạy Agent trong tab này để làm Task số 1 (Ví dụ: Thêm hướng dẫn nhấn giữ phím thu âm) [73, 155].
5. Mở tiếp tab tmux thứ hai, gõ tiếp `treehouse` và mở Agent làm Task số 2 (Ví dụ: Thêm tính năng chụp ảnh màn hình đính kèm) [73, 156].
6. Bạn có thể kiểm tra trạng thái hoạt động của toàn bộ các thư mục làm việc song song bằng lệnh [71, 154]:
   ```bash
   treehouse status
   ```
   *(Hiển thị danh sách các worktrees đang bận hoặc đang rảnh rỗi [72, 154]).*
7. Khi làm việc xong, bạn chỉ cần đóng tab tmux lại. Treehouse sẽ tự động nhận diện tab đã đóng để thu hồi, dọn dẹp hoặc đánh dấu sẵn sàng tái sử dụng worktree đó cho phiên tiếp theo [72, 154].

**Input** — Mã nguồn dự án chính [69, 152].
**Output** — Các môi trường lập trình độc lập được dọn dẹp tự động [71, 72, 154].
**Cách kiểm tra** — Gõ `treehouse status` để xem danh sách thư mục được phân bổ động [71, 72, 154].

---

#### BƯỚC 7 — Tích hợp Trợ lý Trực ca Cấp cao First Mate

**Mục tiêu**
Giải quyết triệt để sự mệt mỏi và kiệt sức (context switch exhaustion) khi bạn phải quản lý, chuyển đổi qua lại giữa hàng chục tab Agent đang chạy song song [75, 157, 158].

**Thao tác**
1. Clone dự án trợ lý điều phối First Mate về máy [76, 159]:
   ```bash
   git clone https://github.com/kunchenguid/firstmate.git
   ```
2. Truy cập thư mục dự án và chạy Agent điều phối trực tiếp trong đó [76, 159].
3. Khi khởi động lần đầu, ra lệnh bằng giọng nói chọn chế độ nghiêm ngặt cho code [77, 78, 159, 160]:
   > *"I want to select full gates to PR"* [78, 161]
   *(Lệnh này chỉ định First Mate luôn sử dụng pipeline **No Mistakes** để kiểm tra mọi thay đổi của các Agent con [78, 161]).*
4. Giao nhiều việc lớn cùng lúc cho First Mate [78, 161]:
   > *"For all three projects (lavish, github axi, chrome dev tools), I'd like to add an update command on the CLI that will update their version to the latest on npm."* [76, 78, 159, 161]
5. **Xem First Mate tự động xử lý:**
   * Tự nhận diện đây là 3 Task riêng biệt chạy trên 3 dự án khác nhau [79, 161].
   * Tự động mở các tab tmux song song [79, 161].
   * Tự động gọi **Treehouse** dựng các phân nhánh Worktree sạch [79, 161].
   * Tự khởi chạy các Agent tương ứng thực thi lập trình [79, 162].
   * Tự động kích hoạt **No Mistakes** chạy test và nộp PR cho bạn duyệt [79, 162].
6. Trong lúc các Agent con đang code ngầm, bạn có thể trò chuyện với First Mate để phân tích các vấn đề khác [80, 162]:
   > *"Hey first mate, let's also look at the most recent three open issues in lavish axi and let's discuss which ones are actionable."* [80, 162]
7. Sau khi First Mate đưa ra phân tích (ví dụ: lỗi nút chế độ vẽ chú thích #87 là rõ ràng nhất), bạn chỉ cần ra lệnh ngắn gọn [80, 163]:
   > *"First mate, let's address number 87."* [80, 163]
   *First Mate sẽ tự động gánh vác việc gác hàng và giám sát cho bạn [81, 163].*

---

### 5. AGENT CONFIGURATION (Cấu hình chi tiết của Agent)

Mẫu cấu hình hệ thống chuẩn của Agent (Agentic System Instruction) được trích xuất trực tiếp từ các quy tắc vàng của tác giả:

* **Mô hình Agent khuyên dùng:** Mô hình lớp Frontier cao cấp nhất (ví dụ: Claude 3.5 Sonnet gán qua Claude Code) [19, 22, 104, 107].
* **System Prompt / Memory File nội dung (Giới hạn tối đa 30 dòng) [24, 108]:**

```markdown
# Agent Core Instructions

## General Coding Styles
1. Never use em dashes (—) for formatting or text separators in any written output or PR descriptions. Always use plain dashes (-). [24, 25, 109]

## Technical Decision Making
2. When evaluating technical design patterns or libraries, do NOT give significant weight to initial development cost. Focus heavily on scalability, maintainability, and architectural cleanlines. [25, 27, 110, 112]

## Bug Fixing Standard Operating Procedure
3. Every bug fix task MUST begin with writing an automated end-to-end (E2E) test case that reproduces the reported issue in an environment mimicking actual end-user behavior as closely as possible. Avoid relying solely on isolated unit tests. [27, 28, 112]
```

---

### 6. TOOLS CỦA AGENT

Khi Agent vận hành, nó được cấp các quyền gọi tool có thiết kế công thái học cao để tiết kiệm tài nguyên hệ thống [44, 128]:

1. **GitHub CLI Tool (AXI Standard):**
   * **Mục đích:** Đọc PRs, tạo branch, đẩy commit và tạo Pull Requests [56, 58, 126, 139, 141].
   * **Vì sao vượt trội MCP?** GitHub MCP tốn token gấp 3 lần và trễ hơn gấp đôi [43, 127]. CLI AXI tối giản hóa dữ liệu trả về để Agent đọc trực tiếp [44, 128].
2. **Chrome DevTools Tool (AXI Standard):**
   * **Mục đích:** Thao tác giả lập trình duyệt, lấy dữ liệu DOM, chụp ảnh màn hình để test giao diện [45, 128].
   * **Ưu điểm:** Giảm bớt số lượt suy nghĩ (turns) của Agent và tiết kiệm token tối đa khi duyệt web [45, 129].

---

### 7. MEMORY

Hệ thống quản lý trí nhớ phân tầng không dùng cơ sở dữ liệu vector phức tạp mà dựa hoàn toàn vào tập tin Markdown đơn giản [31, 116]:

* **Global Memory (`~/agents.md`):** Tự động tải vào hệ thống của *tất cả* các phiên làm việc của mọi Agent ở mọi dự án [24, 108, 109]. Chứa phong cách viết chữ của bạn, định kiến cần sửa của AI [24, 25, 108, 110].
* **Project Memory (`.claude-memory.md`):** Được lưu trực tiếp trong thư mục dự án [29, 113]. Đây là **bộ nhớ học tập tập thể (collective learning)** của toàn bộ các phiên làm việc của Agent từ trước tới nay [30, 115]. Cứ mỗi lần Agent làm sai và được bạn sửa, bắt nó ghi lại kinh nghiệm vào file này để lần sau không tái phạm [31, 115].
* **Hậu quả khi thiếu Memory:** AI sẽ liên tục lặp lại các lỗi lập trình cơ bản của dự án, quên mất kiến trúc phân bổ file, tốn token giải thích lại bối cảnh và dễ chọn giải pháp chắp vá, kém chất lượng [27, 31, 111, 115].

---

### 8. DATA FLOW (Luồng dữ liệu mẫu của một tác vụ)

Dưới đây là hành trình thực tế của tác vụ **"Thêm lệnh CLI tự động cập nhật npm trên cả 3 dự án"** [78, 161]:

1. **Ý định (Intent):** Thuyền trưởng nói: *"First mate, let's update npm cli commands for all three repos."* [76, 78, 159, 161]
2. **First Mate điều phối:**
   * Quét và định vị 3 thư mục dự án trên ổ cứng [76, 159].
   * Gọi `treehouse` để sinh ra 3 Git Worktrees cô lập: `/workspace/lavish-axi-wt`, `/workspace/github-axi-wt`, và `/workspace/chrome-dev-wt` [79, 161].
   * Mở 3 tmux tabs tương ứng [79, 161].
3. **Thực thi song song (Agent execution):** Các Agent gõ code chỉnh sửa file `package.json` và code CLI để thêm lệnh cập nhật [78, 161].
4. **Chạy No Mistakes Pipeline:**
   * Agent gọi `no mistakes` [79, 162].
   * Pipeline thực hiện rebase, chạy test xem lệnh CLI hoạt động đúng không [57, 140, 141].
   * Thu thập log ghi nhận phiên bản npm đã được cập nhật thành công làm bằng chứng [57, 58, 140, 141].
5. **Nộp PR:** 3 Pull Requests được nộp đồng thời lên GitHub kèm báo cáo chi tiết [79, 162].
6. **Bàn giao:** First Mate báo cáo với Thuyền trưởng đã nộp PR thành công [79, 162].

---

### 9. TESTING PLAN (Kế hoạch Kiểm thử Quy trình)

Trước khi đưa Agent Flow này vào vận hành thực tế hàng ngày, hãy thực hiện kịch bản test sau:

#### A. Kịch bản Happy Path (Luồng chạy lý tưởng)
* **Input:** Yêu cầu sửa một dòng chữ thông báo trên giao diện.
* **Cách chạy:** Giao nhiệm vụ cho Agent qua giọng nói -> Cho chạy `no mistakes` [41, 59, 125, 142].
* **Expected Result:** Nhánh git được đẩy lên, một PR xuất hiện trên GitHub kèm ảnh chụp màn hình chứa chữ thông báo mới [58, 60, 141, 143].

#### B. Kịch bản Tool Failure (Lỗi công cụ ngoại vi)
* **Input:** Yêu cầu Agent lấy thông tin PR từ một repo không tồn tại hoặc bị sai phân quyền API key.
* **Cách chạy:** Đưa link repo sai cho Agent gõ lệnh lấy dữ liệu.
* **Expected Result:** Công cụ CLI gán chuẩn AXI trả về mã lỗi rõ ràng. Agent đọc mã lỗi và đề xuất kỹ sư kiểm tra lại quyền truy cập hoặc file `.env` chứa API Key, không bị crash hoặc treo luồng [20, 44, 105, 128].

---

### 10. DEBUGGING & TROUBLESHOOTING (Xử lý sự cố thường gặp)

| Lỗi thường gặp | Nguyên nhân có thể | Cách kiểm tra | Cách xử lý |
| :--- | :--- | :--- | :--- |
| **Open Super Whisper viết sai tên dự án** [77, 160] | Mô hình Whisper chưa có ngữ cảnh từ vựng chuyên môn của bạn [77, 160]. | Nói chữ "lavish" nhưng máy gõ ra chữ "slavish" hoặc "ravish". | Vào cài đặt Open Super Whisper, thêm chính xác danh sách từ vựng vào trường **Initial Prompt** [77, 160]. |
| **Treo luồng khi chạy qua đêm (`gnhf`)** [67, 150] | Agent rơi vào vòng lặp logic vô hạn hoặc đợi nhập liệu từ bàn phím (interactive prompts) [65, 148]. | Kiểm tra màn hình log thấy số lượng vòng lặp tăng vọt mà không tạo thêm commit mới. | **⚠️ Luôn viết quy tắc nghiêm cấm sử dụng câu lệnh tương tác cần bấm phím (như `read` hoặc `input`) trong kịch bản chạy tự động.** Sử dụng tham số `-y` hoặc gán cứng cấu hình mặc định. Thiết lập Token Cap chặt chẽ để hệ thống tự ngắt bảo vệ tài khoản [67, 150]. |
| **Xung đột file khi chạy song song** [68, 151] | Nhiều Agent cùng thao tác và ghi đè file trên cùng một thư mục làm việc vật lý [68, 151]. | Xuất hiện lỗi Git index locked hoặc code của Agent này đè lên code của Agent kia. | Chắc chắn bạn đã khởi động Agent thông qua lệnh `treehouse` để tách biệt không gian lưu trữ [71, 154]. |

---

### 11. BEST PRACTICES (Quy tắc vận hành nâng cao)

#### Thiết kế Prompt (Prompt Design)
* **Luôn viết quy tắc phản biện chéo (Adversarial Review):** Khi viết pipeline, hãy thiết lập một bước bắt buộc để một mô hình AI thứ hai kiểm thử và tìm lỗi trong code của mô hình thứ nhất [57, 140]. Điều này giúp lọc sạch tới 90% lỗi logic ngớ ngẩn trước khi code được trình lên cho con người [57, 140].

#### Kiểm soát Chi phí (Cost Optimization)
* **Chuyển giao thông tin có điều kiện thành Skills:** Tiết kiệm hàng ngàn USD tiền token bằng cách giữ file system prompt cực kỳ tinh gọn và chỉ nạp tài liệu kỹ thuật chi tiết khi Agent thực sự bắt tay vào viết code hoặc chạy test [32, 35, 116, 119].

---

### 12. SECURITY NOTES (Lưu ý An ninh và Bảo mật)

* **🧠 Cảnh báo bảo mật từ AI:** Vì các Agent có toàn quyền chạy các lệnh hệ thống (CLI) trên máy tính của bạn thông qua terminal, việc cho phép Agent tự do cài đặt hoặc chạy các plugin, script tải trực tiếp từ internet là cực kỳ nguy hiểm [36, 120]. Agent có thể bị tấn công tiêm mã độc (prompt injection) từ các trang web ngoài, dẫn đến hành vi tự động đọc các file nhạy cảm chứa private keys hoặc mật khẩu ví và gửi lên các máy chủ độc hại [36, 120].
* **Giải pháp bảo vệ:** Chỉ sử dụng các Skills và CLI do chính bạn viết hoặc đã được kiểm duyệt mã nguồn rõ ràng trong mạng nội bộ [38, 122]. Sử dụng Docker hoặc môi trường ảo hóa cô lập để chạy Agent nếu dự án có tính bảo mật thông tin cao.

---

### 13. PRODUCTION CHECKLIST (Kiểm tra trước khi triển khai thực tế)

- [ ] **Mã hóa Credential:** Tất cả các token GitHub, API key của OpenAI/Anthropic phải được lưu trong biến môi trường hệ thống (`.bashrc`, `.zshrc` hoặc keychain), tuyệt đối không ghi cứng (hardcode) trong file memory hoặc code nguồn [36, 120].
- [ ] **Giới hạn Ngân sách:** Đặt hạn mức chi phí (hard limit) hàng ngày/hàng tuần trên bảng điều khiển API của Anthropic/OpenAI để tránh việc Agent chạy lặp vô hạn đốt tiền khi bạn đang ngủ [67, 150].
- [ ] **Cấu hình Worktree sạch:** Kiểm tra xem lệnh `treehouse` có hoạt động trơn tru và tự động thu hồi tài nguyên sau khi tắt tab tmux hay chưa [72, 154].
- [ ] **Evidence Recording:** Đảm bảo thư viện ghi hình màn hình hoặc chụp ảnh của pipeline No Mistakes đã được phân quyền truy cập hệ thống để xuất báo cáo kèm bằng chứng trực quan [57, 58, 140, 141].

---

### 14. SOURCE TRACEABILITY (Mục lục tra cứu nguồn video gốc)

Dưới đây là các mốc thời gian (timestamp) quan trọng trong video của tác giả Kun Chen để bạn tiện đối chiếu trực quan khi cần:

* **`02:17 – 03:50`**: Lý do vì sao chọn làm việc hoàn toàn trên môi trường Terminal & Triết lý giữ tay trên bàn phím [5, 8, 91, 93].
* **`03:53 – 05:10`**: Giới thiệu và hướng dẫn cấu hình chi tiết cho WezTerm với Lua script [8, 11, 94, 96].
* **`05:13 – 07:11`**: Hướng dẫn sử dụng dồn kênh terminal với tmux [11, 14, 96, 99].
* **`07:17 – 09:20`**: Sử dụng Neovim và cách thức di chuyển, tìm kiếm code thần tốc [15, 18, 100, 103].
* **`09:25 – 11:20`**: Phân tích so sánh 4 loại Agent Harnesses hàng đầu (Claude Code, Codex, Pi, Open Code) [18, 22, 103, 107].
* **`11:25 – 16:10`**: Cách thiết lập Onboarding cho Agent thông qua Global Memory và Project Memory [23, 31, 108, 116].
* **`16:13 – 20:25`**: Kỹ thuật tạo Skills để giảm tải cho Prompt và cảnh báo bảo mật về Skills trôi nổi trên internet [31, 39, 116, 123].
* **`20:31 – 22:10`**: Cách sử dụng Giọng nói (Voice Input) với Open Super Whisper và lợi ích năng suất [39, 42, 123, 125].
* **`22:16 – 24:23`**: Tầm quan trọng của Agent Ergonomics và chuẩn thiết kế AXI [42, 46, 126, 129].
* **`24:28 – 28:34`**: Lập kế hoạch trực quan qua HTML Prototype với Lavish Axi [46, 53, 129, 137].
* **`28:39 – 33:06`**: Quy trình tự động hóa kiểm soát chất lượng code và nộp PR với No Mistakes [53, 62, 137, 145].
* **`33:12 – 36:16`**: Chạy tác vụ xuyên đêm với Good Night, Have Fun (gnhf) [62, 67, 145, 150].
* **`36:23 – 40:17`**: Vận hành song song nhiều Agent cùng lúc sử dụng Treehouse [67, 75, 150, 157].
* **`40:23 – 44:19`**: Tích hợp Trợ lý Trực ca điều phối First Mate [75, 81, 157, 164].
* **`44:26 – 45:43`**: Chuyển đổi tư duy sang "Tư duy Thuyền trưởng" và tổng kết [82, 84, 164, 166].
