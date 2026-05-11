# Storj Multi-Node Monitor

> A simple, self-hosted dashboard to monitor multiple Storj storage nodes on a single page.

![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)

Tired of opening four browser tabs to check on your storage nodes? This little Python tool aggregates all your node dashboards into a single clean overview page. No more tab juggling.

---

## ✨ Features

- 📊 **Single page overview** of all your storage nodes
- 💾 **Disk space breakdown** — used / trash / free with a stacked bar
- 📡 **Bandwidth tracking** — ingress and egress per node, monthly totals
- 💰 **Earnings overview** — estimated payout for current month, held amount, all-time earnings
- 🛰️ **Satellite scores** — audit, suspension, and online scores per satellite
- 🔍 **Node details** — version, QUIC status, last ping, wallet address, node age
- 📈 **Aggregated totals** — sum of all nodes' disk, bandwidth, and earnings at the top
- 🔄 **Auto-refresh** — configurable (15s / 30s / 1min / 5min / off)
- 🎨 **Dark themed UI** — easy on the eyes
- 🔒 **100% local** — your data never leaves your machine
- 🪶 **Zero dependencies** — pure Python standard library, no `pip install` needed


<img width="1727" height="1210" alt="024f49b4f08d2297f510867f32c08323" src="https://github.com/user-attachments/assets/4ca8904c-f0b5-48f0-acd5-9d030cf6563a" />



---

## 🚀 Quick Start

### Requirements

- **Python 3.7+** (uses only standard library)
- Your Storj nodes' dashboards reachable on `127.0.0.1` (default Storj setup)

### Installation

**1. Install Python** (if you don't have it):

<details>
<summary><b>Windows</b></summary>

Open PowerShell and run:

```powershell
winget install Python.Python.3.13
```

Then **close and reopen PowerShell**. Verify with:

```powershell
py --version
```

</details>

<details>
<summary><b>Linux</b></summary>

Python 3 is usually pre-installed. Otherwise:

```bash
sudo apt install python3        # Debian/Ubuntu
sudo dnf install python3        # Fedora
sudo pacman -S python           # Arch
```

</details>

<details>
<summary><b>macOS</b></summary>

Python 3 comes with macOS. If needed:

```bash
brew install python3
```

</details>

**2. Download the script:**

Grab `storj-monitor.py` from this repo and save it somewhere convenient (e.g. Desktop).

**3. Run it (foreground, with console):**

```bash
# Windows
py storj-monitor.py

# Linux / macOS
python3 storj-monitor.py
```

You should see:

```
  ╔════════════════════════════════════════════╗
  ║   STORJ MULTI-NODE MONITOR (extended)      ║
  ╠════════════════════════════════════════════╣
  ║   Dashboard: http://localhost:8080         ║
  ║                                            ║
  ║   Stop with Ctrl+C                         ║
  ╚════════════════════════════════════════════╝
```

**4. Open your browser:**

👉 **http://localhost:8080**

That's it! By default it monitors ports `14002`, `14003`, `14004`, `14005`. You can change these directly in the input field at the top of the dashboard.

---

## 🛠️ Configuration

Most things can be configured directly in the web UI:

| Setting | Default | Description |
|---------|---------|-------------|
| **Ports** | `14002, 14003, 14004, 14005` | Comma-separated list of node dashboard ports |
| **Auto-Refresh** | `30s` | How often to refresh the data (or off) |

If you need to change the listening port (default `8080`), edit the top of `storj-monitor.py`:

```python
LISTEN_PORT = 8080      # Port the dashboard runs on
LISTEN_HOST = "127.0.0.1"
NODE_HOST = "127.0.0.1" # Where your nodes are running
```

---

## 🔁 Running in the background

By default, the script stops when you close the terminal. Here's how to keep it running in the background so you can close PowerShell/terminal and it keeps going.

### Windows — recommended method

Open PowerShell, navigate to your script folder, then start it as a hidden background process:

```powershell
cd path\to\dashboard
Start-Process py -ArgumentList "storj-monitor.py" -WindowStyle Hidden
```

The script now runs in the background with no visible window. You can safely close PowerShell — the dashboard stays up.

**Check if it's running:**

```powershell
Get-Process python -ErrorAction SilentlyContinue
```

**Stop it when you're done:**

```powershell
Get-Process python | Stop-Process -Force
```

### Windows — one-click start (recommended for daily use)

Create a `start.bat` file in your dashboard folder with this content:

```bat
@echo off
cd /d "%~dp0"
start "" /B py storj-monitor.py
```

Save it next to `storj-monitor.py`. From now on, just **double-click `start.bat`** — the script launches silently in the background. No PowerShell needed.

> 💡 The `/B` flag launches without a new window; `%~dp0` ensures it always runs from the correct folder.

You can also create a desktop shortcut: right-click `start.bat` → **Send to** → **Desktop (create shortcut)**.

### Linux — systemd service

Create `/etc/systemd/system/storj-monitor.service`:

```ini
[Unit]
Description=Storj Multi-Node Monitor
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
ExecStart=/usr/bin/python3 /path/to/storj-monitor.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now storj-monitor
sudo systemctl status storj-monitor    # check it's running
```

### macOS — launchd

Save as `~/Library/LaunchAgents/com.user.storj-monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.storj-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/storj-monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load with:

```bash
launchctl load ~/Library/LaunchAgents/com.user.storj-monitor.plist
```

---

## 🔬 How it works

The script does two things:

1. **Serves the dashboard** — a single self-contained HTML page with embedded JavaScript
2. **Acts as a proxy** — your browser requests `/api/node/14002`, the script fetches data from `http://127.0.0.1:14002/api/sno`, and returns the JSON

The proxy step is necessary because browsers block direct cross-origin requests to `localhost`. A static HTML file can't talk to the node dashboards directly — but the Python script can.

It calls these standard Storj Node API endpoints:

- `/api/sno` — main dashboard data (disk space, bandwidth, version, status)
- `/api/sno/satellites` — per-satellite scores and bandwidth breakdown
- `/api/sno/estimated-payout` — earnings and held amount

---

## 🔒 Privacy

- Everything runs locally on `127.0.0.1`
- No telemetry, no analytics, no external API calls (except Google Fonts for typography — remove the `<link>` tag in the HTML if you want to avoid even that)
- The script is a single file you can read top to bottom

---

## 🐛 Troubleshooting

<details>
<summary><b>"Connection failed" for all nodes</b></summary>

- Verify your nodes' dashboards are accessible by opening them manually: `http://127.0.0.1:14002`, etc.
- Make sure the ports in the UI match your actual node dashboard ports

</details>

<details>
<summary><b>Browser shows ERR_EMPTY_RESPONSE or ERR_CONNECTION_REFUSED</b></summary>

Usually means either nothing is running on port 8080, or multiple instances are conflicting.

**Fix:** kill all Python processes and start cleanly:

```powershell
Get-Process python*,pythonw* -ErrorAction SilentlyContinue | Stop-Process -Force
```

Wait a few seconds, then start the script again. Verify only one process listens on the port:

```powershell
netstat -ano | findstr :8080
```

You should see exactly one line with `LISTENING` (German Windows shows `ABHÖREN`).

</details>

<details>
<summary><b>"Address already in use" on startup</b></summary>

Port 8080 is taken by another program. Edit `storj-monitor.py` and change `LISTEN_PORT = 8080` to something else (e.g. `8090`), then run again.

</details>

<details>
<summary><b>Earnings look wrong</b></summary>

The Storj API returns earnings values in slightly different scales depending on the node version. If the numbers look off compared to your normal dashboard, please open an issue with your node version so I can fix the conversion.

</details>

<details>
<summary><b>"py: command not found" on Windows</b></summary>

Either install Python via `winget install Python.Python.3.13`, or use `python` instead of `py`. After installing, **close and reopen** PowerShell.

If you only have the Python install manager but no Python runtime yet, run:

```powershell
py install default
```

</details>

<details>
<summary><b>Background start with pyw doesn't work on Windows</b></summary>

If `Start-Process pyw ...` results in no working dashboard, use `py` with hidden window instead:

```powershell
Start-Process py -ArgumentList "storj-monitor.py" -WindowStyle Hidden
```

This is the same effect (no visible console, runs in background) but more reliable across systems.

</details>

---

## 🤝 Contributing

Feedback, bug reports, and pull requests are welcome. The whole thing is one Python file with an embedded HTML/JS dashboard — easy to read, easy to modify.

Ideas for future features:

- Historical earnings chart (per month)
- Notifications when a satellite's score drops
- Per-satellite earnings breakdown
- Export to CSV
- Mobile-optimized layout

---

## 📜 License

MIT License — see [LICENSE](./LICENSE) for details.

You're free to use, modify, and distribute this however you like.

---

## ⚠️ Disclaimer

This is an unofficial tool not affiliated with Storj Labs. It only reads data from your local node dashboards using the same APIs your browser uses. Use at your own risk.

---

## 💬 Acknowledgments

Built for the Storj node operator community. If this tool is useful to you, drop a ⭐ on the repo!
