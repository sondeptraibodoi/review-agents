# Agent Advance Setup Tutorial

Bộ công cụ này chuẩn hóa môi trường coding agent trên WSL2.

Nó hỗ trợ cài public toolchain, liên kết global instructions, liên kết global situational skills và tạo project memory có bước review trước khi ghi vào repository.

Mục tiêu chính là dùng chung một nguồn cấu hình cho Codex, Claude Code, Gemini CLI và Antigravity CLI mà không ghi đè âm thầm setup cũ.

## Phạm vi

Repository cung cấp các khả năng sau:

- Clone và bootstrap Firstmate từ upstream chính thức.

- Cài các dependency user-level do Firstmate quản lý.

- Cài `gnhf` từ package npm chính thức.

- Kiểm tra hoặc tự cài các prerequisite WSL2 và từ chối dùng nhầm binary Windows dưới `/mnt/c`.

- Tạo symlink global instructions và skills cho nhiều agent.

- Backup file global đã tồn tại trước khi thay bằng symlink.

- Kiểm tra setup bằng lệnh `doctor`.

- Phân tích project bằng Codex trong sandbox read-only và tạo proposal trước khi ghi `AGENTS.md`.

Script chỉ điều phối installer và repository public có sẵn.

Script không chép hoặc viết lại source của các upstream tool.

## Môi trường mục tiêu

- WSL2 hoặc Linux.

- Python 3 từ Linux distribution.

- Node.js 22.19 trở lên.

- npm cài trong WSL2.

- Git và tmux.

- GitHub CLI `gh` vì Firstmate yêu cầu.

- GitLab CLI `glab` nếu làm việc với GitLab.

- Codex CLI nếu dùng project memory generator.

Không chạy script bằng Windows Python hoặc Windows Node thông qua `/mnt/c`.

Kiểm tra nhanh:

```bash
command -v python3 node npm git tmux gh glab codex
python3 --version
node --version
tmux -V
```

## Firstmate quản lý những tool nào

Clone Firstmate chưa tự động cài dependency.

Firstmate detect tool còn thiếu và chỉ cài những tool được truyền rõ ràng vào `fm-bootstrap.sh install`.

Universal toolchain mà Firstmate khai báo gồm `node`, `git`, `gh`, `no-mistakes`, `gh-axi`, `chrome-devtools-axi`, `lavish-axi`, `tasks-axi` và `quota-axi`.

Backend `tmux` bổ sung `tmux` và `treehouse`.

Với backend mặc định `tmux`, phạm vi được chia như sau:

| Nhóm | Thành phần | Cách xử lý |
| --- | --- | --- |
| Firstmate user-level | `no-mistakes`, `gh-axi`, `chrome-devtools-axi`, `lavish-axi`, `tasks-axi`, `quota-axi` | Giao cho bootstrap chính chủ của Firstmate |
| Firstmate backend `tmux` | `treehouse` | Giao cho bootstrap chính chủ của Firstmate |
| Prerequisite nền | `git`, `tmux` | `--install` dùng apt nếu còn thiếu |
| Node.js | `node>=22.19`, `npm` | `--install` dùng NVM đã có trong Linux home |
| Provider CLI | `gh`, `glab` | `--install` tải `.deb` mới nhất và cài vào `~/.local/bin` |
| Generator | `codex` | Cài riêng và script chỉ kiểm tra |
| Tool độc lập | `gnhf` | Script cài bằng `npm install -g gnhf` |
| Skill có sẵn | Codex `skill-creator` | Doctor kiểm tra và không cài bản trùng tên |
| Browser runtime | Chrome hoặc Chromium | Tùy chọn và không tự tải |

Firstmate không bao gồm `gnhf` hoặc `glab` trong universal toolchain.

Chrome DevTools AXI và Chrome browser là hai thành phần khác nhau.

## Bắt đầu nhanh

Mở WSL2 và vào repository:

```bash
cd /mnt/u/Projects/agent_advance_setup_tutorial
```

### 1. Xem kế hoạch cài public tools

```bash
./scripts/setup-global.sh tools
```

Dry-run không cài package, không clone repository và không thay đổi filesystem.

Nếu checkout Firstmate đã tồn tại, script chỉ chạy detect-only với network phase bị tắt.

### 2. Tự động cài toàn bộ tool còn thiếu

Lệnh được khuyến nghị cho một WSL2 mới:

```bash
./scripts/setup-global.sh tools --install
```

`--install` thực hiện các bước sau:

1. Dùng NVM hiện có để cài và chọn Node.js 22.19 nếu Node đang thiếu hoặc quá cũ.

2. Dùng apt để cài `git` hoặc `tmux` nếu còn thiếu.

3. Tải `.deb` mới nhất của `gh` và `glab` từ release API chính thức, xác minh SHA-256 rồi cài binary vào `~/.local/bin`.

4. Clone và bootstrap Firstmate.

5. Cài `gnhf` nếu còn thiếu.

Lệnh chỉ hỏi mật khẩu `sudo` khi phải cài `git` hoặc `tmux` bằng apt.

Nếu script nâng cấp Node.js, nó đặt alias NVM mặc định thành Node.js 22.19 và dùng bản đó cho toàn bộ phần cài còn lại.

Sau khi script kết thúc, chạy `nvm use 22.19` hoặc mở shell WSL mới để cập nhật PATH của shell cha hiện tại.

Codex CLI, Chrome browser và bước xác thực tài khoản không được tự động hóa.

### 3. Cài public tools khi prerequisite đã sẵn sàng

```bash
./scripts/setup-global.sh tools --apply
```

`--apply` thực hiện các bước sau:

1. Kiểm tra prerequisite và Node.js major version.

2. Clone `kunchenguid/firstmate` vào `~/agent-tools/firstmate` nếu chưa có.

3. Xác minh origin, working tree và tracked upstream của Firstmate.

4. Chạy Firstmate detect-only để lấy danh sách dependency còn thiếu.

5. Gọi chính `bin/fm-bootstrap.sh install` cho nhóm tool Firstmate quản lý.

6. Cài `gnhf` riêng bằng npm nếu còn thiếu.

7. Chạy lại detect-only để xác nhận kết quả.

Cả `--install` và `--apply` đều hỗ trợ checkout khác bên dưới Linux home:

```bash
./scripts/setup-global.sh tools \
  --firstmate-dir ~/tools/firstmate \
  --apply
```

Có thể bỏ qua `gnhf`:

```bash
./scripts/setup-global.sh tools --skip-gnhf --apply
```

Script không chạy login tương tác, nhưng có thể tự dùng token từ `.env`.

### 4. Xác thực provider

#### Token tự động từ `.env` trong repo

Repository đã có file `.env` local và `.env.example` làm mẫu.

`.env` đã nằm trong `.gitignore`, nên Git không track file này.

Điền token và hostname thật vào `.env`:

```dotenv
GH_TOKEN=github_pat_REPLACE_WITH_REAL_TOKEN
GITLAB_TOKEN=glpat_REPLACE_WITH_REAL_TOKEN
GITLAB_HOST=https://gitlab.company.com
```

Không thêm dấu cách quanh dấu `=` và không đặt comment phía sau token.

Kiểm tra cả hai token:

```bash
./scripts/setup-global.sh auth
```

Sau đó `tools --install`, `tools --apply` và `doctor` sẽ tự đọc `.env` trong repository root.

```bash
./scripts/setup-global.sh tools --install
./scripts/setup-global.sh doctor --agents codex,agy,claude
```

Các lệnh mutating của `tools` xác minh token đã cấu hình trước khi cài hoặc bootstrap.

Script phân tích `.env` bằng Python và không dùng `source`, nên nội dung file không được thực thi như shell code.

Chỉ bốn key `GH_TOKEN`, `GITHUB_TOKEN`, `GITLAB_TOKEN` và `GITLAB_HOST` được chấp nhận.

Có thể chọn file khác bằng `--env-file`:

```bash
./scripts/setup-global.sh auth --env-file config/local-auth.env
```

Không đưa `.env` vào log, ảnh chụp màn hình hoặc nội dung gửi cho agent.

Gitignore chỉ ngăn commit nhầm và không mã hóa file trên ổ đĩa.

#### GitHub cho Firstmate và các GitHub tool

Chạy trong terminal WSL2:

```bash
gh auth login --hostname github.com --git-protocol https --web
```

Nếu trình duyệt không tự mở, sao chép mã một lần và mở URL mà `gh` hiển thị bằng trình duyệt Windows.

Hoàn thành đăng nhập trên trang GitHub rồi kiểm tra:

```bash
gh auth status --hostname github.com
```

Không dùng `gh auth status --show-token` khi chia sẻ log hoặc ảnh chụp màn hình.

Đăng nhập `gh` không tự push source code lên GitHub.

Nó chỉ lưu thông tin xác thực để các lệnh `gh` hoặc tool dựa trên GitHub có thể chạy khi bạn chủ động gọi chúng.

Muốn xóa đăng nhập GitHub khỏi WSL2:

```bash
gh auth logout --hostname github.com
```

#### GitLab công ty

Thay `gitlab.company.com` bằng hostname GitLab thật của công ty rồi chạy:

```bash
glab auth login \
  --hostname gitlab.company.com \
  --git-protocol ssh \
  --web
```

Nếu GitLab công ty hỗ trợ OAuth device flow nhưng WSL2 không mở được trình duyệt, dùng:

```bash
glab auth login \
  --hostname gitlab.company.com \
  --git-protocol ssh \
  --device
```

Device flow yêu cầu GitLab 17.9 trở lên.

Nếu công ty bắt buộc HTTPS cho Git, đổi `--git-protocol ssh` thành `--git-protocol https`.

Kiểm tra trạng thái sau khi đăng nhập:

```bash
glab auth status --hostname gitlab.company.com
```

Muốn xóa đăng nhập GitLab khỏi WSL2:

```bash
glab auth logout --hostname gitlab.company.com
```

Không truyền token trực tiếp trên command line và không ghi token vào repository.

Nếu chính sách công ty bắt buộc Personal Access Token, dùng tùy chọn `--stdin` và scope tối thiểu theo chính sách GitLab nội bộ.

Tham khảo thêm tài liệu chính thức của [GitHub CLI](https://cli.github.com/manual/gh_auth_login) và [GitLab CLI](https://docs.gitlab.com/cli/auth/login/).

Project công ty vẫn dùng GitLab remote, `glab`, Merge Request và GitLab CI.

Không cần sửa hoặc fork Firstmate chỉ vì source code chính nằm trên GitLab.

### 5. Setup global instructions và skills

Xem kế hoạch:

```bash
./scripts/setup-global.sh init --agents codex,agy,claude
```

Áp dụng:

```bash
./scripts/setup-global.sh init --agents codex,agy,claude --apply
```

Cú pháp tương thích dạng parameter cũng được hỗ trợ:

```bash
./scripts/setup-global.sh --init=codex,agy,claude --apply
```

Agent hợp lệ gồm `codex`, `claude`, `gemini` và `agy`.

Alias `antigravity` và `antigravity-cli` được chuẩn hóa thành `agy`.

### 6. Kiểm tra kết quả

```bash
./scripts/setup-global.sh doctor --agents codex,agy,claude
```

Doctor kiểm tra source, frontmatter, symlink, state, agent CLI, public tools, xác thực provider, Firstmate checkout, Chrome runtime và Codex `skill-creator`.

## Global file mapping

| Agent | Global instructions | Global situational skills |
| --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills/<skill>/SKILL.md` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills/<skill>/SKILL.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.gemini/skills/<skill>/SKILL.md` |
| Antigravity CLI | `~/.gemini/GEMINI.md` | `~/.gemini/antigravity-cli/skills/<skill>/SKILL.md` |

Nguồn global instruction duy nhất là [`global/AGENTS.md`](global/AGENTS.md).

Các global situational skill hiện có:

- [`skills/OPINIONS.md`](skills/OPINIONS.md)

- [`skills/PYTHON.md`](skills/PYTHON.md)

Gemini CLI và Antigravity CLI dùng chung global `GEMINI.md` nhưng có skill directory riêng.

## Backup, state và unlink

Nếu instruction file đích đã tồn tại, script sao lưu trước khi tạo symlink.

Tên backup đầu tiên có dạng `AGENTS-bak.md`, `CLAUDE-bak.md` hoặc `GEMINI-bak.md`.

Nếu tên backup đã tồn tại, script tạo tên có timestamp và không ghi đè backup cũ.

Backup của skill cũ được giữ ngoài thư mục skill đang hoạt động để agent không phát hiện nhầm backup như một skill mới.

State và recovery journal mặc định nằm tại:

```text
~/.local/state/agent-advance-setup/
```

Nếu link do script quản lý bị xóa, sửa bằng:

```bash
./scripts/setup-global.sh init --agents codex --repair --apply
```

Gỡ setup bằng dry-run rồi apply:

```bash
./scripts/setup-global.sh unlink --agents codex
./scripts/setup-global.sh unlink --agents codex --apply
```

Nếu destination còn owner khác, `unlink` chỉ bỏ owner được chọn và giữ symlink dùng chung.

## Firstmate checkout safety

Script chỉ chấp nhận origin canonical `github.com/kunchenguid/firstmate`.

Script từ chối thực thi bootstrap khi checkout có một trong các trạng thái sau:

- Origin không đúng.

- Working tree dirty.

- Current branch không có tracked upstream.

- Local branch có local-only commit.

- Local và upstream divergent.

`Dirty` nghĩa là checkout có tracked file đã sửa, file đã xóa hoặc file mới chưa được Git track.

`Ahead` nghĩa là local branch có commit chưa có trên upstream đã biết.

`Behind` nghĩa là upstream đã biết có commit chưa có ở local branch.

`Divergent` nghĩa là local branch và upstream đều có commit riêng.

Doctor không chạy `git fetch`, vì vậy ahead và behind dựa trên remote-tracking refs hiện có.

## Chrome trong WSL2

Chrome không bắt buộc cho Firstmate core.

Chrome chỉ cần khi dùng browser automation hoặc test UI thật.

Doctor coi browser sẵn sàng khi tìm thấy `google-chrome`, `chromium`, `chromium-browser` hoặc một browser endpoint đã cấu hình.

Ví dụ dùng browser endpoint có sẵn:

```bash
export CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222
```

Chỉ bind DevTools endpoint vào localhost.

Không mở port DevTools ra LAN hoặc internet.

## Tạo project memory

Project setup dùng hai phase để tránh ghi nội dung do model tạo ra mà chưa review.

### Phase 1: phân tích và tạo proposal

```bash
./scripts/setup-global.sh project-setup \
  --url https://gitlab.company.com/group/project.git \
  --agents codex,agy \
  --model gpt-5.6-sol \
  --effort xhigh
```

Cú pháp parameter tương thích:

```bash
./scripts/setup-global.sh \
  --project_setup=https://gitlab.company.com/group/project.git \
  --agents=codex,agy \
  --model=gpt-5.6-sol_xhigh
```

Repository mặc định được clone dưới `~/src/<host>/<group>/<project>`.

Phân tích chỉ dùng snapshot của tracked files tại `HEAD`.

File untracked, ignored và thay đổi chưa commit không được đưa cho generator.

Codex chạy trong sandbox read-only và không chạy build, test, package manager hoặc project hook.

Proposal được lưu ngoài repository cùng URL, commit, model, effort và các hash kiểm tra.

### Phase 2: review và apply

Sau khi đọc proposal, áp dụng đúng proposal ID:

```bash
./scripts/setup-global.sh project-setup --apply --proposal-id <proposal-id>
```

Apply không gọi model lần thứ hai.

Apply tạo `AGENTS.md` và các symlink `CLAUDE.md` hoặc `GEMINI.md` tương ứng với agent đã chọn.

Nếu HEAD, origin, proposal hoặc destination thay đổi sau phase phân tích, apply sẽ dừng.

## Command reference

| Lệnh | Chức năng | Có thay đổi hệ thống |
| --- | --- | --- |
| `tools` | Kiểm tra prerequisite và kế hoạch public tools | Không |
| `tools --install` | Cài prerequisite còn thiếu, Firstmate và public tools | Có |
| `tools --apply` | Clone Firstmate và cài tool đã duyệt | Có |
| `auth` | Đọc `.env` và xác minh GitHub cùng GitLab token | Không |
| `init --agents ...` | Xem kế hoạch global symlink | Không |
| `init --agents ... --apply` | Backup và tạo global symlink | Có |
| `doctor --agents ...` | Kiểm tra setup | Không |
| `unlink --agents ...` | Xem kế hoạch gỡ setup | Không |
| `unlink --agents ... --apply` | Gỡ ownership và khôi phục backup | Có |
| `project-setup --url ...` | Clone hoặc phân tích project và tạo proposal | Có |
| `project-setup --apply --proposal-id ...` | Ghi proposal đã review vào project | Có |

Thêm `--json` vào các lệnh nếu cần structured output.

## Cấu trúc implementation

[`scripts/agent_setup.py`](scripts/agent_setup.py) là entrypoint mỏng để giữ tương thích.

Logic nằm trong package `scripts/agent_setup_lib`:

| Module | Trách nhiệm |
| --- | --- |
| `common.py` | Type, validation, path và state store |
| `global_setup.py` | Backup, symlink, init, unlink và recovery |
| `repositories.py` | Git URL, clone và repository status |
| `project.py` | Project analysis, proposal và apply |
| `doctor.py` | Kiểm tra read-only |
| `public_tools.py` | Firstmate bootstrap và gnhf |
| `system_tools.py` | Node 22.19, apt và official release packages |
| `auth_env.py` | Parse `.env` và chuẩn bị credential scope hẹp |
| `cli.py` | Argument parser và command routing |

Toàn bộ implementation chỉ dùng Python standard library.

## Kiểm thử

Chạy trong WSL2:

```bash
python3 -B -m unittest discover -s scripts/tests -v
python3 -B -m tabnanny scripts
sh -n scripts/setup-global.sh
```

Bộ test dùng HOME tạm và không thay đổi global setup thật của user.

## Tài liệu chi tiết

Xem [`docs/huong-dan-setup-global-wsl2.md`](docs/huong-dan-setup-global-wsl2.md) để đọc giải thích chi tiết hơn về luồng setup và các giới hạn an toàn.

## Upstream

- [Firstmate](https://github.com/kunchenguid/firstmate)

- [gnhf](https://github.com/kunchenguid/gnhf)

- [GitHub CLI](https://cli.github.com/)

- [GitLab CLI](https://docs.gitlab.com/cli/)
