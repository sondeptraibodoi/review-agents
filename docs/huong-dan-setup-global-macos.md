# Hướng dẫn setup agent trên macOS

Script hỗ trợ macOS Apple Silicon và Intel bằng Python standard library, Homebrew và các installer upstream chính thức.

## Điều kiện ban đầu

- Một tài khoản macOS thường, không chạy setup bằng `sudo` hoặc tài khoản root.
- Python 3.10 trở lên, native.
- Git và Homebrew.
- Kết nối mạng để tải tool khi chạy `tools --install`.

Kiểm tra kiến trúc:

```bash
uname -m
```

Kết quả được hỗ trợ là `arm64` hoặc `x86_64`.

Nếu Command Line Tools chưa có, cài bằng:

```bash
xcode-select --install
```

Cài Homebrew theo hướng dẫn chính thức tại [brew.sh](https://brew.sh/).

Sau khi cài, bảo đảm `brew` có trên `PATH`.

Apple Silicon thường dùng:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Intel thường dùng:

```bash
eval "$(/usr/local/bin/brew shellenv)"
```

Nếu chưa có Python 3:

```bash
brew install python
```

Xác minh script sẽ dùng đúng Python native và đủ phiên bản:

```bash
command -v python3
python3 --version
./scripts/setup-global.sh --version
```

`python3` không được trỏ tới Python của Windows hoặc một môi trường nằm ngoài macOS home đang setup.

## Chuẩn bị repository và token

Clone hoặc mở repository setup rồi tạo file credential local:

```bash
cd ~/Projects/agent_advance_setup_tutorial
cp .env.example .env
```

Điền các giá trị cần dùng vào `.env`:

```dotenv
GH_TOKEN=ghp_REPLACE_WITH_REAL_TOKEN
GITLAB_TOKEN=glpat_REPLACE_WITH_REAL_TOKEN
GITLAB_HOST=https://git.mattech.vn
```

Không commit hoặc đưa token lên command line.

## Cài public toolchain

Xem kế hoạch mà không thay đổi hệ thống:

```bash
./scripts/setup-global.sh tools
```

Cài các prerequisite và tool còn thiếu:

```bash
./scripts/setup-global.sh tools --install
```

Trên macOS, installer thực hiện các việc sau:

1. Dùng NVM để cài Node.js 22.19 nếu `~/.nvm/nvm.sh` đã tồn tại.
2. Nếu không có NVM, dùng Homebrew để cài bản Node.js hiện hành đáp ứng yêu cầu tối thiểu.
3. Dùng Homebrew để cài `git`, `tmux`, `gh` và `glab` khi còn thiếu.
4. Clone và chạy bootstrap chính thức của Firstmate.
5. Cài các AXI tool do Firstmate quản lý và cài `gnhf` từ npm.

Script không tự cài Homebrew vì bootstrap package manager là thay đổi cấp máy cần được người dùng thực hiện theo hướng dẫn chính thức.

## Áp dụng global instructions và skills

Xem kế hoạch:

```bash
./scripts/setup-global.sh init --agents codex,agy
```

Áp dụng symlink sau khi kiểm tra kế hoạch:

```bash
./scripts/setup-global.sh init --agents codex,agy --apply
```

Các file được quản lý nằm dưới macOS home hiện tại, ví dụ `~/.codex`, `~/.agents` và `~/.gemini`.

Nếu đã có file cũ, script tạo backup trước khi thay bằng symlink và lưu ownership trong state của setup.

## Cài Chrome cho browser E2E

Chrome là tải xuống dung lượng lớn nên không được cài tự động bởi setup script.

Cài khi cần bằng lệnh chủ động sau:

```bash
brew install --cask google-chrome
```

Kiểm tra Chrome:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
```

Doctor nhận diện Chrome hoặc Chromium trong `/Applications`, `~/Applications`, trên `PATH`, hoặc qua `CHROME_DEVTOOLS_AXI_BROWSER_URL`.

## Xác minh

Mở terminal mới để shell nạp lại Homebrew hoặc NVM, sau đó chạy:

```bash
cd ~/Projects/agent_advance_setup_tutorial
./scripts/setup-global.sh auth
./scripts/setup-global.sh doctor --agents codex,agy
```

Một setup hoàn chỉnh phải nhận diện Codex, Agy, `gh`, `glab`, `lavish-axi`, `chrome-devtools-axi` và toàn bộ managed link.

Nếu một npm CLI vừa được cài nhưng doctor chưa thấy, kiểm tra `command -v node`, `command -v npm` và `npm prefix -g`, rồi mở terminal mới.

## Gỡ setup được quản lý

Xem trước kế hoạch:

```bash
./scripts/setup-global.sh unlink --agents codex,agy
```

Gỡ symlink do setup quản lý và khôi phục backup hợp lệ:

```bash
./scripts/setup-global.sh unlink --agents codex,agy --apply
```

Lệnh này không tự gỡ Homebrew formula, npm package hoặc Chrome.
