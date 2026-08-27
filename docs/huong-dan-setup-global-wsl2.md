# Hướng dẫn setup agent trên WSL2

## Mục tiêu

Bộ script này cài public toolchain, tạo global instructions, liên kết global skills và tạo project memory cho nhiều agent.

Môi trường mục tiêu là WSL2 với `python3`, Node.js 22.19 và `tmux`.

Script chỉ điều phối installer public có sẵn.

Script không chép hoặc viết lại source của Firstmate, Lavish AXI, No Mistakes, Treehouse, gnhf, gh-axi hay Chrome DevTools AXI.

## Firstmate thực sự quản lý tool nào

Firstmate là một agent distro và một checkout Git, không phải một binary đơn lẻ.

Clone Firstmate chưa tự cài dependency.

Lệnh `tools --apply` của repository này chạy chế độ detect của Firstmate, lấy danh sách còn thiếu, rồi gọi chính `bin/fm-bootstrap.sh install` với danh sách đã được duyệt.

Với backend `tmux`, phạm vi được chia như sau:

| Nhóm | Thành phần | Cách xử lý |
| --- | --- | --- |
| Firstmate quản lý | `no-mistakes`, `gh-axi`, `chrome-devtools-axi`, `lavish-axi`, `tasks-axi`, `quota-axi`, `treehouse` | Giao cho `fm-bootstrap.sh` |
| Prerequisite nền | `git`, `tmux` | `--install` dùng apt nếu còn thiếu |
| Node.js | `node>=22.19`, `npm` | `--install` dùng NVM hiện có |
| Provider CLI | `gh`, `glab` | `--install` tải `.deb` mới nhất và cài vào `~/.local/bin` |
| Generator | `codex` | Cài riêng và script chỉ kiểm tra |
| Tool độc lập | `gnhf` | Cài từ package npm chính thức |
| Skill có sẵn | Codex `skill-creator` | Chỉ kiểm tra, không cài bản trùng tên |
| Browser runtime | Chrome hoặc Chromium | Tùy chọn và không tự tải |

`gnhf` không phải dependency bắt buộc của Firstmate.

`glab` không thuộc universal toolchain của Firstmate.

Chrome DevTools AXI và Chrome browser là hai thành phần khác nhau.

Script có thể cài `chrome-devtools-axi`, nhưng không tự tải browser dung lượng lớn.

## Cài public tools

Mở WSL2 và vào repository:

```bash
cd /mnt/u/Projects/agent_advance_setup_tutorial
```

Kiểm tra prerequisite hiện có:

```bash
git --version
node --version
npm --version
tmux -V
gh --version
glab --version
codex --version
```

Node.js phải từ major version 20 trở lên.

Các prerequisite phải là binary cài trong WSL2.

Nếu `command -v npm` hoặc một tool khác trả về đường dẫn dưới `/mnt/c`, hãy sửa PATH hoặc cài bản Linux trước khi apply.

Xem kế hoạch mà không clone, không cài package và không truy cập mạng:

```bash
./scripts/setup-global.sh tools
```

Tự động cài prerequisite còn thiếu rồi áp dụng toàn bộ kế hoạch:

```bash
./scripts/setup-global.sh tools --install
```

Chế độ này dùng NVM hiện có cho Node.js 22.19, apt cho `git` và `tmux`, release `.deb` chính thức kèm xác minh SHA-256 cho `gh` và `glab`, rồi cài hai provider CLI vào `~/.local/bin` trước khi tiếp tục Firstmate cùng `gnhf`.

Nó chỉ hỏi mật khẩu `sudo` khi `git` hoặc `tmux` còn thiếu và phải được cài bằng apt.

Nếu Node.js được nâng cấp, script đặt alias NVM mặc định thành Node.js 22.19 và dùng bản đó trong phần cài còn lại.

Chạy `nvm use 22.19` hoặc mở shell WSL mới sau khi script kết thúc để cập nhật PATH của shell cha hiện tại.

Nếu prerequisite đã được chuẩn bị thủ công, chỉ áp dụng public toolchain:

```bash
./scripts/setup-global.sh tools --apply
```

Mặc định Firstmate được clone vào:

```text
~/agent-tools/firstmate
```

Có thể chọn một đường dẫn khác bên dưới Linux home:

```bash
./scripts/setup-global.sh tools \
  --firstmate-dir ~/tools/firstmate \
  --apply
```

Có thể bỏ qua `gnhf`:

```bash
./scripts/setup-global.sh tools --skip-gnhf --apply
```

Script không tự chạy bước đăng nhập tương tác, nhưng có thể tự dùng token từ `.env`.

Script cũng không tự cài Codex CLI hoặc Chrome browser.

### Token tự động từ `.env` trong repo

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

### GitHub cho Firstmate và các GitHub tool

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

### GitLab công ty

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

Project công ty vẫn sử dụng GitLab remote, `glab`, Merge Request và GitLab CI.

Không cần sửa hoặc fork Firstmate chỉ vì project chính nằm trên GitLab.

## Firstmate checkout an toàn

Remote đúng của Firstmate là `kunchenguid/firstmate` trên GitHub.

Script từ chối chạy bootstrap nếu origin không đúng.

Script cũng từ chối chạy một checkout dirty, divergent hoặc có local-only commit.

Current branch phải có tracked upstream trước khi bootstrap được thực thi.

`Dirty` nghĩa là checkout có tracked file đã sửa, file đã xóa hoặc file mới chưa được Git track.

`Ahead` nghĩa là local branch có commit chưa có trên upstream đã biết.

`Behind` nghĩa là upstream đã biết có commit chưa có ở local branch.

`Divergent` nghĩa là local branch và upstream đều có commit riêng.

Doctor không chạy `git fetch`, vì vậy số ahead và behind dựa trên remote-tracking refs hiện có.

Nếu checkout chỉ behind và vẫn clean, script cảnh báo nhưng có thể tiếp tục với bootstrap hiện có.

## Setup global instructions và skills

Xem kế hoạch trước:

```bash
./scripts/setup-global.sh init --agents codex,agy,claude
```

Áp dụng sau khi đã đọc kế hoạch:

```bash
./scripts/setup-global.sh init --agents codex,agy,claude --apply
```

Cú pháp rút gọn tương đương:

```bash
./scripts/setup-global.sh --init=codex,agy,claude --apply
```

Tên hợp lệ là `codex`, `claude`, `gemini` và `agy`.

Alias `antigravity` và `antigravity-cli` được chuẩn hóa thành `agy`.

Các destination được tạo như sau:

| Agent | Global instructions | Global personal skills |
| --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/skills/<skill>/SKILL.md` |
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/skills/<skill>/SKILL.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` | `~/.gemini/skills/<skill>/SKILL.md` |
| Antigravity CLI | `~/.gemini/GEMINI.md` | `~/.gemini/antigravity-cli/skills/<skill>/SKILL.md` |

Nguồn global instruction duy nhất là `global/AGENTS.md`.

Hai global skill tình huống là `skills/OPINIONS.md` và `skills/PYTHON.md`.

Gemini CLI và Antigravity CLI dùng chung global `GEMINI.md`.

## Backup và khôi phục

Nếu instruction file đã tồn tại, script sao lưu trước khi tạo symlink.

Tên backup đầu tiên có dạng `AGENTS-bak.md`, `CLAUDE-bak.md` hoặc `GEMINI-bak.md`.

Nếu tên đó đã tồn tại, script tạo tên có timestamp và không ghi đè backup cũ.

Backup của skill cũ được giữ ngoài thư mục skill đang hoạt động.

State mặc định nằm tại:

```text
~/.local/state/agent-advance-setup/
```

Nếu một link do script quản lý bị xóa, có thể sửa bằng:

```bash
./scripts/setup-global.sh init --agents codex --repair --apply
```

Để gỡ setup và khôi phục file trước đó, chạy dry-run rồi apply:

```bash
./scripts/setup-global.sh unlink --agents codex
./scripts/setup-global.sh unlink --agents codex --apply
```

## Doctor

Chạy kiểm tra read-only:

```bash
./scripts/setup-global.sh doctor --agents codex,agy,claude
```

Doctor kiểm tra source, frontmatter, symlink, state, agent CLI, public tools, xác thực `gh` và `glab`, Firstmate checkout, Chrome runtime và Codex `skill-creator`.

Doctor không cài package và không mở browser.

## Chrome trong WSL2

Chrome không bắt buộc cho Firstmate core.

Chrome chỉ cần khi dùng browser automation hoặc test UI thật.

Nếu dùng một browser endpoint đã chạy sẵn, cấu hình:

```bash
export CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222
```

Chỉ bind DevTools endpoint vào localhost.

Không mở port DevTools ra LAN hoặc internet.

## Tạo project memory

Phân tích repository và tạo proposal nhưng chưa ghi file vào project:

```bash
./scripts/setup-global.sh project-setup \
  --url https://gitlab.company.com/group/project.git \
  --agents codex,agy \
  --model gpt-5.6-sol \
  --effort xhigh
```

Cú pháp rút gọn tương đương:

```bash
./scripts/setup-global.sh \
  --project_setup=https://gitlab.company.com/group/project.git \
  --agents=codex,agy \
  --model=gpt-5.6-sol_xhigh
```

Phân tích chỉ dùng snapshot của tracked files tại `HEAD`.

Generator chạy bằng `codex exec` trong sandbox read-only.

Sau khi đọc và duyệt proposal, áp dụng đúng proposal ID:

```bash
./scripts/setup-global.sh project-setup --apply --proposal-id <proposal-id>
```

Bước apply không gọi model lần thứ hai.

## Cấu trúc source của script

`scripts/agent_setup.py` chỉ là entrypoint tương thích.

Logic được chia theo trách nhiệm:

| File | Trách nhiệm |
| --- | --- |
| `agent_setup_lib/common.py` | Type, validation, path và state store |
| `agent_setup_lib/global_setup.py` | Backup, symlink, init, unlink và recovery |
| `agent_setup_lib/repositories.py` | URL Git, clone và repository status |
| `agent_setup_lib/project.py` | Project analysis, proposal và apply |
| `agent_setup_lib/doctor.py` | Kiểm tra read-only |
| `agent_setup_lib/public_tools.py` | Firstmate bootstrap và gnhf |
| `agent_setup_lib/system_tools.py` | Node 22.19, apt và official release packages |
| `agent_setup_lib/auth_env.py` | Parse `.env` và chuẩn bị credential scope hẹp |
| `agent_setup_lib/cli.py` | Argument parser và command routing |

## Kiểm thử

Chạy toàn bộ test trong WSL2:

```bash
python3 -m unittest discover -s scripts/tests -v
```

Bộ test chỉ dùng Python standard library và HOME tạm.

Bộ test không thay đổi global setup thật của user.

## Upstream

- [Firstmate](https://github.com/kunchenguid/firstmate)

- [gnhf](https://github.com/kunchenguid/gnhf)

- [GitHub CLI](https://cli.github.com/)

- [GitLab CLI](https://docs.gitlab.com/cli/)
