<p align="center">
  <img src="docs/gui.png" width="440" alt="Free DNS Setter — GUI" />
</p>

<p align="center">
  <strong>🌐 Free DNS Setter</strong><br>
  <sub>Change your DNS with a click or a command — built for Iranian users</sub>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg"></a>
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue"></a>
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows%20%C2%B7%20Linux%20(Ubuntu)%20%C2%B7%20macOS-lightgrey">
  <a href="https://github.com/alisadeghiaghili/free-dns-setter/releases"><img alt="Release" src="https://img.shields.io/badge/Release-v2.1.0-brightgreen"></a>
</p>

<br>

---

<p align="center"><a href="README.md">🇮🇷 نسخه فارسی (Persian README)</a></p>

---

## Why Free DNS Setter?

In Iran you may need to switch DNS: to reach services that are restricted, to
reduce game ping, or simply to use a fast, reliable resolver. This tool does
that in one click (or one terminal line) — and it runs on **Windows, Linux
(Ubuntu/Debian), and macOS**, without touching your network settings by hand.

## Features

- ⚡ **One click** — a simple, right-to-left GUI; or one line in a terminal
- 🖥️ **No GUI dependency** — the UI is Tkinter (ships with Python); no PyQt/PySide to install
- 🐧🍎🪟 **Cross-platform** — Windows (WMI), Linux/Ubuntu (NetworkManager), and macOS (`networksetup`)
- 📦 **Standalone Windows build** — single-file `free-dns-setter.exe`, no Python needed
- 🔄 **Safe rollback** — the current DNS is snapshotted before any change; `Deactivate`/`reset` restores it
- 🔐 **Runs elevated** — auto-elevates via UAC on Windows, `sudo` on Linux & macOS
- 🧩 **9 ready-to-use providers** across three categories, all on **verified public** IPs
- 🩹 **Real diagnostics** — OS return codes are checked and errors are surfaced (no silent failure)

## Categories

| Category | Purpose |
|----------|---------|
| 🔓 **Anti-Sanction** | Reach foreign services that restrict Iran |
| 🎮 **Gaming** | Lower ping and better access to game servers |
| 🌐 **General** | Fast, stable, secure resolvers for everyday use |

> ⚠️ Every internal IP was verified as a public address (via PTR / public
> resolution) before being added. The "Anti-Filter" category currently has no
> verified public provider and is unavailable.

## Providers

| Provider | Category | Primary | Secondary |
|----------|----------|---------|-----------|
| Shecan | Anti-Sanction | `178.22.122.100` | `185.51.200.2` |
| Begzar | Anti-Sanction | `185.55.224.24` | `185.55.226.26` |
| Electro | Anti-Sanction | `78.157.42.100` | `78.157.42.101` |
| HostIran | Anti-Sanction | `37.27.81.177` | `5.144.130.130` |
| AsiaTech | Gaming | `185.98.113.113` | `185.98.114.114` |
| Cloudflare | General | `1.1.1.1` | `1.0.0.1` |
| Google | General | `8.8.8.8` | `8.8.4.4` |
| Quad9 | General | `9.9.9.9` | `149.112.112.112` |
| DNS Pro | General | `87.107.110.109` | `87.107.110.110` |

## Install & Run

### Option 1 — Standalone Windows build (easiest)

1. Download `free-dns-setter.exe` from the
   [releases](https://github.com/alisadeghiaghili/free-dns-setter/releases).
2. Double-click it. If a UAC prompt appears, click **Yes**.
3. Pick a provider and hit **Activate**.

> No Python or anything else to install.

### Option 2 — From source (Linux, macOS, and Windows)

Requires **Python 3.11+** and admin privileges (the app asks for them via
`sudo`/UAC on first run). The GUI is the same Tkinter window on every OS.

**Windows 10/11**
```bash
pip install wmi rich
```
**Linux (Ubuntu/Debian)**
```bash
sudo apt update && sudo apt install -y network-manager python3-tk
pip install rich
```
> NetworkManager (`nmcli`) is pre-installed on Ubuntu; the line above is just
> in case. `python3-tk` provides the Tkinter backend.

**macOS**
```bash
brew install python-tk      # Tkinter, if missing
pip install rich
```
> macOS ships `networksetup` by default; the GUI needs Tkinter.

**Run the GUI:**
```bash
python -m dns_changer.main
```

<p align="center">
  <img src="docs/dropdown.png" width="300" alt="Categorised right-to-left dropdown" />
</p>

**CLI (any OS):**
```bash
# interactive TUI menu
python -m dns_changer.cli.dns_cli

# one-shot commands
python -m dns_changer.cli.dns_cli list             # list all providers
python -m dns_changer.cli.dns_cli status           # show current DNS
python -m dns_changer.cli.dns_cli set Shecan       # activate a provider
python -m dns_changer.cli.dns_cli reset            # revert to automatic DNS
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "DNS change failed" message | The app needs elevated rights. It re-launches automatically (UAC on Windows, `sudo` on Linux/macOS). If the prompt is blocked, run it manually: `sudo python -m dns_changer.main` (Linux/macOS) or *Run as administrator* (Windows). |
| `nmcli not found` (Linux) | NetworkManager isn't installed. `sudo apt install network-manager` (Ubuntu/Debian), or install your distro's equivalent. |
| Antivirus flags the exe | Single-file PyInstaller builds are sometimes flagged. Run from source (`pip install` + `python -m`) or whitelist the exe. |
| DNS reverts after reboot | Changes apply to the active network connection. NetworkManager (Linux) or DHCP (Windows) may reset it on reconnect — just re-run the app after a network change. |

## Architecture

Layered structure; each layer is independent and testable:

```
dns_changer/
├── main.py                  # GUI entry point
├── core/                    # logic — no UI import side effects
│   ├── providers.py         # provider definitions (add here only)
│   ├── adapter.py           # the only OS seam — WMI / nmcli / networksetup
│   └── dns_service.py       # state machine + DNS snapshot
├── ui/
│   └── main_window.py       # Tkinter window (RTL)
├── cli/
│   └── dns_cli.py           # interactive + one-shot CLI (rich)
└── utils/
    └── privileges.py        # elevation — UAC (Windows) / sudo (Linux, macOS)
```

**Adding a new provider:** add one entry to `core/providers.py` — no other
file needs to change. **Adding a new OS:** add one backend to
`core/adapter.py` and one branch to `utils/privileges.py`.

**Adding a new provider:** add one entry to `core/providers.py` — no other
file needs to change.

## Contributing

1. Fork the repo:
   [github.com/alisadeghiaghili/free-dns-setter](https://github.com/alisadeghiaghili/free-dns-setter)
2. Create a branch and commit with descriptive messages
   (following [Conventional Commits](https://www.conventionalcommits.org/))
3. Open a Pull Request

## License

This project is licensed under the [Apache License 2.0](LICENSE).

---

<div align="center">
  <strong>Ali Sadeghi Aghili</strong><br>
  <a href="https://github.com/alisadeghiaghili">github.com/alisadeghiaghili</a>
  · <a href="mailto:alisadeghiaghili@gmail.com">alisadeghiaghili@gmail.com</a>
</div>
