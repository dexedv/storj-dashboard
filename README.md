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

**3. Run it:**

```bash
# Windows
Start-Process py -ArgumentList "storj-monitor.py" -WindowStyle Hidden

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

## 🔁 Running it permanently

By default, closing the terminal stops the script. Here's how to keep it running in the background:

### Windows — easy mode (no console)

1. Press `Win+R`, type `shell:startup`, hit Enter
2. Right-click in the folder → **New** → **Shortcut**
3. Set target to:
   ```
   Start-Process py -ArgumentList "storj-monitor.py" -WindowStyle Hidden
   ```
4. Name it "Storj Monitor", click Finish

`pyw` runs Python without a console window. The script will now auto-start with Windows and run silently in the background. To stop it, use Task Manager → find `pythonw.exe` → End Task.

### Windows — robust (Scheduled Task with auto-restart)

Open PowerShell **as Administrator** and run:

```powershell
$action = New-ScheduledTaskAction -Execute "pyw" -Argument "C:\path\to\storj-monitor.py"
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
Register-ScheduledTask -TaskName "StorjMonitor" -Action $action -Trigger $trigger -Settings $settings -RunLevel Limited
```

To remove later:

```powershell
Unregister-ScheduledTask -TaskName "StorjMonitor" -Confirm:$false
```

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

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now storj-monitor
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
