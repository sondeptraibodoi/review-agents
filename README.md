# Agent Advance Setup Tutorial

Repository này cung cấp một bộ script Python standard library để chuẩn hóa môi trường coding agent trên WSL2.

Profile mặc định hiện tại là Codex và Agy, trong đó Agy là Antigravity CLI.

Claude Code được hỗ trợ bởi implementation nhưng không nằm trong luồng setup mặc định.

Script ưu tiên tái sử dụng installer và package public chính chủ thay vì tự viết lại các tool upstream.

## Kết quả mong đợi

Sau khi hoàn tất quick start, môi trường WSL2 có:

- Node.js 22.19 trở lên từ NVM trong Linux home.

- Git, tmux, GitHub CLI `gh` và GitLab CLI `glab`.

- Firstmate cùng backend `tmux` và các dependency public của nó.

- `gnhf` được cài riêng từ package npm chính thức.

- Global instructions dùng chung cho Codex và Agy.

- Bốn global situational skills là `tuln-opinions`, `python-tools`, `lavish` và `chrome-devtools-axi`.

- Xác thực GitHub và GitLab từ file `.env` local không được Git track.

- Lệnh `doctor` để kiểm tra lại toàn bộ setup theo cách read-only.

## Phạm vi tự động hóa

Script có thể tự động:

- Cài hoặc chọn Node.js 22.19 bằng NVM hiện có.

- Cài `git` và `tmux` bằng apt khi còn thiếu.

- Cài `gh` và `glab` vào `~/.local/bin` từ release chính thức.

- Clone và bootstrap Firstmate từ `kunchenguid/firstmate`.

- Cài các public AXI tools do Firstmate quản lý.

- Cài `gnhf` riêng bằng npm.

- Backup global instruction hoặc skill cũ trước khi tạo symlink.

- Tạo project memory theo quy trình proposal rồi apply.

Script không tự động:

- Cài Codex CLI.

- Đăng nhập tương tác vào tài khoản GitHub hoặc GitLab.

- Tải Chrome browser dung lượng lớn.

- Push source code lên GitHub hoặc GitLab.

- Ghi proposal do model tạo vào project trước khi người dùng review.

## Môi trường mục tiêu

- WSL2 hoặc Linux.

- Python 3 của Linux distribution.

- Python standard library, không cần `pip install`.

- NVM trong Linux home.

- Node.js 22.19 trở lên.

- npm Linux, không dùng npm hoặc Node từ `/mnt/c`.

- Codex CLI và Agy nếu dùng profile mặc định.

Mở Ubuntu WSL2 và vào repository:

```bash
cd /mnt/u/Projects/agent_advance_setup_tutorial
```

## Quick start cho Codex và Agy

### 1. Cấu hình provider token

Sao chép file mẫu nếu `.env` chưa tồn tại:

```bash
cp .env.example .env
```

Điền credential vào `.env`:

```dotenv
GH_TOKEN=ghp_REPLACE_WITH_REAL_TOKEN
GITLAB_TOKEN=glpat_REPLACE_WITH_REAL_TOKEN
GITLAB_HOST=https://git.mattech.vn
```

Với GitHub Personal Access Token classic, bộ scope tối thiểu cho GitHub CLI là `repo`, `read:org` và `gist`.

Scope GitLab phải tuân theo chính sách của GitLab công ty và các thao tác mà bạn thực sự sử dụng.

Không đặt token trên command line, trong commit, log hoặc ảnh chụp màn hình.

`.env` đã nằm trong `.gitignore`.

Gitignore chỉ ngăn commit nhầm và không mã hóa file trên ổ đĩa.

### 2. Xác thực token

```bash
./scripts/setup-global.sh auth
```

Lệnh phải báo cả `gh: ok` và `glab: ok`.

Script phân tích `.env` bằng Python và không dùng `source`, vì vậy nội dung file không được thực thi như shell code.

Chỉ bốn key sau được chấp nhận:

- `GH_TOKEN`

- `GITHUB_TOKEN`

- `GITLAB_TOKEN`

- `GITLAB_HOST`

Chỉ đặt một trong hai key `GH_TOKEN` hoặc `GITHUB_TOKEN`.

Có thể chọn credential file khác bằng `--env-file`:

```bash
./scripts/setup-global.sh auth --env-file config/local-auth.env
```

### 3. Cài public toolchain

Xem kế hoạch mà không thay đổi filesystem:

```bash
./scripts/setup-global.sh tools
```

Cài toàn bộ prerequisite và public tool còn thiếu:

```bash
./scripts/setup-global.sh tools --install
```

Lệnh `--install` thực hiện theo thứ tự:

1. Xác thực các token đã cấu hình.

2. Kiểm tra WSL2, Python, Node, npm, Git, tmux, `gh`, `glab` và Codex.

3. Kích hoạt hoặc cài Node.js 22.19 bằng NVM.

4. Cài prerequisite nền còn thiếu.

5. Clone và kiểm tra Firstmate checkout.

6. Chạy Firstmate detect-only để lấy danh sách dependency còn thiếu.

7. Gọi installer chính chủ của Firstmate cho đúng nhóm tool đó.

8. Cài `gnhf` nếu còn thiếu.

9. Chạy lại detect-only để xác minh kết quả.

Nếu script vừa thay Node.js, mở shell WSL mới hoặc chạy:

```bash
nvm use 22.19
```

### 4. Áp dụng global instructions và skills

Xem kế hoạch:

```bash
./scripts/setup-global.sh init --agents codex,agy
```

Áp dụng setup:

```bash
./scripts/setup-global.sh init --agents codex,agy --apply
```

Cú pháp parameter tương thích:

```bash
./scripts/setup-global.sh --init=codex,agy --apply
```

### 5. Kiểm tra kết quả

```bash
./scripts/setup-global.sh doctor --agents codex,agy
```

Một setup hoàn chỉnh phải có:

- `authentication: gh: ok`

- `authentication: glab: ok`

- `agent: codex: ok`

- `agent: agy: ok`

- Tất cả global link ở trạng thái `managed-ok`.

- `doctor_complete` với exit code `0`.

Kiểm tra nhanh binary và phiên bản:

```bash
command -v python3 node npm git tmux gh glab codex agy
python3 --version
node --version
tmux -V
```

## Tool inventory và ownership

Firstmate universal toolchain khai báo các thành phần sau:

- `node`

- `git`

- `gh`

- `no-mistakes`

- `gh-axi`

- `chrome-devtools-axi`

- `lavish-axi`

- `tasks-axi`

- `quota-axi`

Backend `tmux` bổ sung `tmux` và `treehouse`.

Phạm vi cài đặt được chia rõ như sau:

| Nhóm | Thành phần | Owner cài đặt |
| --- | --- | --- |
| Firstmate user-level | `no-mistakes`, `gh-axi`, `chrome-devtools-axi`, `lavish-axi`, `tasks-axi`, `quota-axi` | `fm-bootstrap.sh` của Firstmate |
| Firstmate backend `tmux` | `treehouse` | `fm-bootstrap.sh` của Firstmate |
| Prerequisite nền | `git`, `tmux` | Setup script qua apt khi thiếu |
| Node.js | `node>=22.19`, `npm` | Setup script qua NVM |
| Provider CLI | `gh`, `glab` | Setup script từ official release |
| Tool độc lập | `gnhf` | Setup script qua npm |
| Generator | `codex` | Cài riêng, script chỉ kiểm tra |
| Browser runtime | Chrome hoặc Chromium | Cài hoặc cấu hình riêng |

Firstmate không bao gồm `gnhf` hoặc `glab`.

`chrome-devtools-axi` và Chrome browser là hai thành phần khác nhau.

Codex `skill-creator` là system skill có sẵn và script không cài một bản trùng tên.

## Global file mapping

Profile mặc định tạo các mapping sau:

| Agent | Global instructions | Global situational skills |
| --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | `~/.agents/skills/<skill>/SKILL.md` |
| Agy | `~/.gemini/GEMINI.md` | `~/.gemini/antigravity-cli/skills/<skill>/SKILL.md` |

Nguồn global instruction duy nhất là [`global/AGENTS.md`](global/AGENTS.md).

Các global situational skill hiện có:

- [`skills/OPINIONS.md`](skills/OPINIONS.md), được publish thành skill `tuln-opinions`.

- [`skills/PYTHON.md`](skills/PYTHON.md), được publish thành skill `python-tools`.

- [`skills/LAVISH.md`](skills/LAVISH.md), được publish thành skill route `lavish`.

- [`skills/CHROME_DEVTOOLS_AXI.md`](skills/CHROME_DEVTOOLS_AXI.md), được publish thành skill route `chrome-devtools-axi`.

Hai AXI skill là route mỏng, không phải bản sao implementation của public tool.

Route định nghĩa khi nào agent phải dùng tool, yêu cầu agent đọc hướng dẫn hiện hành từ CLI đã cài, và ngăn tải thêm một bản package bằng `npx -y` khi binary global đã có.

`lavish` được kích hoạt cho kế hoạch phức tạp, so sánh, kiến trúc, UI proposal, báo cáo hoặc artifact cần review trực quan.

`chrome-devtools-axi` được kích hoạt cho frontend, UI, browser debugging và E2E cần Chrome thật, bao gồm kiểm tra giao diện, console, network, viewport và screenshot.

Sau khi thêm hoặc thay đổi global skill, hãy mở phiên Codex/Agy mới để agent nạp lại danh sách skill.

Kiểm tra các route đã được publish:

```bash
test -L ~/.agents/skills/lavish/SKILL.md
test -L ~/.agents/skills/chrome-devtools-axi/SKILL.md
test -L ~/.gemini/antigravity-cli/skills/lavish/SKILL.md
test -L ~/.gemini/antigravity-cli/skills/chrome-devtools-axi/SKILL.md
```

Codex dùng `$HOME/.agents/skills` làm vị trí user-skill chuẩn.

Khi nâng cấp từ setup `0.3.0` trở xuống, `init --apply` tự tạo link chuẩn rồi gỡ các link Codex cũ dưới `~/.codex/skills` nếu chúng vẫn do script quản lý và chưa bị thay đổi bên ngoài.

Nếu đường dẫn cũ từng chứa file hoặc symlink của người dùng, migration khôi phục backup đã xác minh thay vì xóa nội dung đó.

Kiểm tra public CLI tương ứng:

```bash
command -v lavish-axi
command -v chrome-devtools-axi
lavish-axi --version
chrome-devtools-axi --version
```

Implementation vẫn hỗ trợ các agent sau khi được yêu cầu rõ:

- `codex`

- `agy`

- `gemini`

- `claude`

Alias `antigravity` và `antigravity-cli` được chuẩn hóa thành `agy`.

Claude không nằm trong profile mặc định của hướng dẫn này.

## Backup, state và unlink

Nếu instruction file đích đã tồn tại, script tạo backup trước khi thay bằng symlink.

Backup đầu tiên có dạng `AGENTS-bak.md`, `CLAUDE-bak.md` hoặc `GEMINI-bak.md`.

Nếu tên backup đã tồn tại, script thêm timestamp và không ghi đè file cũ.

Backup skill được đặt ngoài skill directory đang hoạt động để agent không phát hiện nhầm nó như một skill mới.

State và recovery journal nằm tại:

```text
~/.local/state/agent-advance-setup/
```

Sửa một link quản lý đã bị xóa:

```bash
./scripts/setup-global.sh init --agents codex,agy --repair --apply
```

Xem kế hoạch gỡ:

```bash
./scripts/setup-global.sh unlink --agents codex,agy
```

Gỡ ownership và khôi phục backup khi có:

```bash
./scripts/setup-global.sh unlink --agents codex,agy --apply
```

Nếu một destination còn owner khác, script giữ symlink dùng chung.

## GitLab công ty và Firstmate

Project chính có thể tiếp tục dùng GitLab remote, `glab`, Merge Request và GitLab CI.

GitLab hiện được cấu hình tại:

```text
https://git.mattech.vn
```

Firstmate vẫn được clone từ GitHub vì upstream chính thức nằm tại `github.com/kunchenguid/firstmate`.

Không cần sửa, fork hoặc chuyển Firstmate sang GitLab chỉ vì project công ty dùng GitLab.

Đăng nhập GitHub không làm phát sinh push source code.

Code chỉ được push khi người dùng hoặc agent chủ động chạy một lệnh Git có thay đổi remote.

## Firstmate checkout safety

Script chỉ chạy bootstrap khi checkout Firstmate đáp ứng toàn bộ điều kiện:

- Origin canonical là `github.com/kunchenguid/firstmate`.

- Working tree không dirty.

- Current branch có tracked upstream.

- Local branch không có local-only commit.

- Local và upstream không divergent.

`Dirty` nghĩa là checkout có file được sửa, xóa hoặc tạo mới nhưng chưa commit.

`Ahead` nghĩa là local branch có commit chưa tồn tại trên upstream đã biết.

`Behind` nghĩa là upstream đã biết có commit chưa tồn tại ở local branch.

`Divergent` nghĩa là local và upstream đều có commit riêng.

Doctor không chạy `git fetch`, vì vậy ahead và behind dựa trên remote-tracking refs hiện có.

## Chrome DevTools AXI

Firstmate cài `chrome-devtools-axi`, nhưng package này vẫn cần một Chrome hoặc Chromium runtime khi chạy browser automation.

Chrome không bắt buộc cho Firstmate core.

Browser package có dung lượng lớn nên setup script không tự tải nó.

### Cài Google Chrome trong Ubuntu WSL2

Các lệnh dưới đây dành cho Ubuntu hoặc Debian `amd64`.

Kiểm tra kiến trúc trước khi tải:

```bash
dpkg --print-architecture
```

Chỉ tiếp tục với URL bên dưới khi kết quả là `amd64`.

Tải gói Google Chrome stable chính thức vào thư mục tạm:

```bash
cd /tmp

curl --proto '=https' --tlsv1.2 -fL --retry 3 \
  -o google-chrome-stable_current_amd64.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
```

Kiểm tra metadata của package trước khi cài:

```bash
dpkg-deb --field ./google-chrome-stable_current_amd64.deb \
  Package Version Architecture
```

Package phải có tên `google-chrome-stable` và architecture `amd64`.

Cài package bằng apt để dependency được xử lý đúng:

```bash
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

Lệnh `sudo` sẽ yêu cầu mật khẩu Linux của user WSL2.

Kiểm tra binary và phiên bản:

```bash
command -v google-chrome
google-chrome --version
```

Chạy một smoke test headless:

```bash
google-chrome --headless --disable-gpu --dump-dom https://example.com
```

Xóa package tạm sau khi cài thành công:

```bash
rm -f /tmp/google-chrome-stable_current_amd64.deb
```

Quay lại repository và chạy doctor:

```bash
cd /mnt/u/Projects/agent_advance_setup_tutorial
./scripts/setup-global.sh doctor --agents codex,agy
```

Doctor phải nhận diện `google-chrome` và vẫn kết thúc bằng exit code `0`.

Có thể kiểm tra trực tiếp AXI sau khi Chrome đã hoạt động:

```bash
chrome-devtools-axi open https://example.com
chrome-devtools-axi snapshot
chrome-devtools-axi stop
```

Cold start đầu tiên có thể lâu hơn vì Chrome DevTools AXI cần khởi động browser backend.

Tài liệu package Chrome Linux chính thức nằm tại [Google Chrome Enterprise Help](https://support.google.com/chrome/a/answer/9025903).

### Dùng browser endpoint thay cho Chrome cài trong WSL2

Doctor coi browser sẵn sàng khi tìm thấy một trong các command sau:

- `google-chrome`

- `chromium`

- `chromium-browser`

Doctor cũng chấp nhận một browser endpoint đã cấu hình:

```bash
export CHROME_DEVTOOLS_AXI_BROWSER_URL=http://127.0.0.1:9222
```

Chỉ bind DevTools endpoint vào localhost.

Không mở DevTools port ra LAN hoặc internet.

## Tạo project memory

Project setup dùng hai phase để nội dung do model tạo luôn được review trước khi ghi vào repository.

### Phase 1: phân tích và tạo proposal

```bash
./scripts/setup-global.sh project-setup \
  --url https://git.mattech.vn/group/project.git \
  --agents codex,agy \
  --model gpt-5.6-sol \
  --effort xhigh
```

```bash
./scripts/setup-global.sh project-setup \
    --url git@gitlab.com:comic-project1/comic-platform.git \
    --clone-root /mnt/f/my_project/commic-platform \
    --dest /mnt/f/my_project/commic-platform \
    --agents codex,agy \
    --model gpt-5.6-sol \
    --effort xhigh
```

Cú pháp parameter tương thích:

```bash
./scripts/setup-global.sh \
  --project_setup=https://git.mattech.vn/group/project.git \
  --agents=codex,agy \
  --model=gpt-5.6-sol_xhigh
```

Repository mặc định được clone dưới `~/src/<host>/<group>/<project>`.

Generator chỉ nhận snapshot của tracked files tại `HEAD`.

File untracked, ignored và thay đổi chưa commit không được đưa cho generator.

Codex chạy trong sandbox read-only và không chạy build, test, package manager hoặc project hook.

Proposal được lưu ngoài repository cùng URL, commit, model, effort và hash kiểm tra.

### Phase 2: review và apply

Sau khi review proposal, áp dụng đúng proposal ID:

```bash
./scripts/setup-global.sh project-setup --apply --proposal-id <proposal-id>
```

Apply không gọi model lần thứ hai.

Apply dừng nếu HEAD, origin, proposal hoặc destination thay đổi sau phase phân tích.

Với profile `codex,agy`, apply tạo project `AGENTS.md` và symlink `GEMINI.md` tương ứng.

## Command reference

| Lệnh | Chức năng | Thay đổi hệ thống |
| --- | --- | --- |
| `auth` | Xác minh GitHub và GitLab token từ `.env` | Không |
| `tools` | Kiểm tra prerequisite và lập kế hoạch | Không |
| `tools --install` | Cài prerequisite, Firstmate và public tools còn thiếu | Có |
| `tools --apply` | Bootstrap public tools khi prerequisite đã sẵn sàng | Có |
| `init --agents ...` | Xem kế hoạch global links | Không |
| `init --agents ... --apply` | Backup và tạo global links | Có |
| `doctor --agents ...` | Kiểm tra toàn bộ setup | Không |
| `unlink --agents ...` | Xem kế hoạch gỡ ownership | Không |
| `unlink --agents ... --apply` | Gỡ ownership và khôi phục backup | Có |
| `project-setup --url ...` | Clone hoặc phân tích project và tạo proposal | Có |
| `project-setup --apply --proposal-id ...` | Ghi proposal đã review vào project | Có |

Thêm `--json` nếu cần structured output.

## Cấu trúc implementation

[`scripts/setup-global.sh`](scripts/setup-global.sh) là shell entrypoint cho WSL2 và Linux.

[`scripts/agent_setup.py`](scripts/agent_setup.py) là Python entrypoint mỏng để giữ tương thích.

Logic nằm trong package `scripts/agent_setup_lib`:

| Module | Trách nhiệm |
| --- | --- |
| `common.py` | Type, validation, path và state store |
| `global_setup.py` | Backup, symlink, init, unlink và recovery |
| `repositories.py` | Git URL, clone và repository status |
| `project.py` | Project analysis, proposal và apply |
| `doctor.py` | Kiểm tra read-only |
| `public_tools.py` | Firstmate bootstrap và `gnhf` |
| `system_tools.py` | Node 22.19, apt và official release package |
| `auth_env.py` | Parse `.env` và tạo subprocess credential scope hẹp |
| `cli.py` | Argument parser và command routing |

Toàn bộ Python implementation chỉ dùng standard library.

## Kiểm thử

Chạy trong WSL2:

```bash
python3 -B -m unittest discover -s scripts/tests -v
python3 -B -m tabnanny scripts
sh -n scripts/setup-global.sh
```

Bộ test dùng HOME tạm và không thay đổi global setup thật của user.

## Tài liệu chi tiết

Xem [`docs/huong-dan-setup-global-wsl2.md`](docs/huong-dan-setup-global-wsl2.md) để đọc luồng setup chi tiết và các giới hạn an toàn.

## Upstream

- [Firstmate](https://github.com/kunchenguid/firstmate)

- [gnhf](https://github.com/kunchenguid/gnhf)

- [GitHub CLI](https://cli.github.com/)

- [GitLab CLI](https://docs.gitlab.com/cli/)

- [Google Chrome for Linux](https://support.google.com/chrome/a/answer/9025903)
