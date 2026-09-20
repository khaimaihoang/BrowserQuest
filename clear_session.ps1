# Script lưu trữ SESSION.md hiện tại vào thư mục sessions và làm sạch SESSION.md
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $projectRoot) {
    $projectRoot = "D:\Develop\Projects\BrowserQuest"
}

$sessionFile = Join-Path $projectRoot "SESSION.md"
$sessionsDir = Join-Path $projectRoot "sessions"

if (-not (Test-Path $sessionFile)) {
    Write-Warning "Không tìm thấy file SESSION.md tại: $sessionFile"
    exit 0
}

# Kiểm tra nội dung file
$content = Get-Content -Path $sessionFile -Raw -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($content)) {
    Write-Host "SESSION.md đang rỗng, không có gì để lưu trữ." -ForegroundColor Yellow
    exit 0
}

# Tạo thư mục sessions nếu chưa có
if (-not (Test-Path $sessionsDir)) {
    New-Item -ItemType Directory -Path $sessionsDir -Force | Out-Null
}

# Đọc dòng đầu tiên có nội dung
$lines = Get-Content -Path $sessionFile -Encoding UTF8
$firstLine = ""
foreach ($line in $lines) {
    $trimmed = $line.Trim()
    if ($trimmed -ne "") {
        $firstLine = $trimmed
        break
    }
}

# Chuẩn hóa tên file từ dòng đầu tiên
# Bỏ ký tự markdown tiêu đề (#, ##, ...)
$cleanedTitle = $firstLine -replace '^#+\s*', ''
# Chuyển ký tự đặc biệt/khoảng trắng thành _
$slug = $cleanedTitle.Trim() -replace '[^\p{L}\p{Nd}]+', '_'
$slug = $slug.Trim('_').ToUpperInvariant()

if ([string]::IsNullOrWhiteSpace($slug)) {
    $slug = "SESSION"
}

# Xác định số index X tiếp theo dựa trên các file đã có trong thư mục sessions
$existingFiles = Get-ChildItem -Path $sessionsDir -Filter "*.md" -File
$maxIndex = 0

foreach ($file in $existingFiles) {
    if ($file.BaseName -match '^(\d+)_') {
        $idx = [int]$matches[1]
        if ($idx -gt $maxIndex) {
            $maxIndex = $idx
        }
    }
}

$nextIndex = $maxIndex + 1
$destFileName = "${nextIndex}_${slug}.md"
$destFilePath = Join-Path $sessionsDir $destFileName

# Lưu/Copy nội dung sang file mới trong thư mục sessions
Copy-Item -Path $sessionFile -Destination $destFilePath -Force
Write-Host "Đã lưu session thành công: $destFilePath" -ForegroundColor Green

# Clear content của SESSION.md
Clear-Content -Path $sessionFile -Force
Write-Host "Đã clear nội dung của $sessionFile" -ForegroundColor Cyan