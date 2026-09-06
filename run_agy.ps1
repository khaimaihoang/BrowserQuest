$ErrorActionPreference = "Stop"

# 1. Start the Headroom proxy in the background
Start-Process -FilePath "headroom" -ArgumentList "proxy", "--port", "8787" -WindowStyle Hidden
Start-Sleep -Seconds 1

# 2. Route general traffic to Headroom
$env:OPENAI_BASE_URL = "http://localhost:8787/v1"
$env:HTTP_PROXY = "http://localhost:8787"
$env:HTTPS_PROXY = "http://localhost:8787"

# 3. CRITICAL: Bypass the proxy for all of Google's internal/auth domains
$env:NO_PROXY = "localhost, 127.0.0.1, .googleapis.com, .googleusercontent.com, .google.com"

# 4. Run the Antigravity CLI
agy --dangerously-skip-permissions $args