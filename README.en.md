# 🌐 Free DNS Setter

> A Windows DNS manager for Iranian users — GUI + CLI, built with Python.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://www.microsoft.com/windows)

---

[نسخه فارسی (Persian README)](README.md)

---

## About the Author

**Name:** Ali Sadeghi Aghili
**GitHub:** [github.com/alisadeghiaghili](https://github.com/alisadeghiaghili)
**Email:** [alisadeghiaghili@gmail.com](mailto:alisadeghiaghili@gmail.com)

---

## Overview

Free DNS Setter is a Windows desktop application that lets you switch between DNS providers with a single click or command. It supports 9 active providers across three categories — anti-sanction, gaming, and general-purpose — and ships both a **Tkinter** GUI (right-to-left) and a Rich-powered interactive CLI. The GUI is built on the Python standard library, so it needs no external GUI dependency.

---

## Features

- **9 pre-configured DNS providers** across three active categories
- **GUI** — Tkinter window with a right-aligned (RTL) dropdown and per-provider descriptions; no external GUI dependency
- **CLI** — interactive TUI menu *and* non-interactive one-shot commands
- Automatic **DNS snapshot** before any change — safe rollback to DHCP
- **UAC elevation** — auto-relaunches with admin privileges if needed
- WMI return-code checking — surfaces real errors instead of silent failures
- Every internal provider IP is a **verified public address** (via PTR / public resolution)
- Layered architecture (core / ui / cli / utils) — each layer independently testable

---

## DNS Providers

| Provider   | Category      | Primary          | Secondary         |
|------------|---------------|------------------|-------------------|
| Shecan     | Anti-Sanction | 178.22.122.100   | 185.51.200.2      |
| Begzar     | Anti-Sanction | 185.55.224.24    | 185.55.226.26     |
| Electro    | Anti-Sanction | 78.157.42.100    | 78.157.42.101     |
| HostIran   | Anti-Sanction | 37.27.81.177     | 5.144.130.130     |
| AsiaTech   | Gaming        | 185.98.113.113   | 185.98.114.114    |
| Cloudflare | General       | 1.1.1.1          | 1.0.0.1           |
| Google     | General       | 8.8.8.8          | 8.8.4.4           |
| Quad9      | General       | 9.9.9.9          | 149.112.112.112   |
| DNS Pro    | General       | 87.107.110.109   | 87.107.110.110    |

> The "Anti-Filter" category has no verified public provider right now
> (`403` used a private address and could not work). It will be added as soon
> as a valid public IP is confirmed.

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- Administrator privileges

```bash
pip install wmi rich
```
(The GUI only needs `wmi`; `rich` is for the CLI. `Tkinter` ships with Python.)

---

## Usage

### GUI

```bash
python -m dns_changer.main
```

> **Must be run as Administrator.** It re-launches itself with elevation via UAC if not.

### CLI

```bash
# Interactive TUI menu
python -m dns_changer.cli.dns_cli

# One-shot commands
python -m dns_changer.cli.dns_cli list             # list all providers
python -m dns_changer.cli.dns_cli status           # show current DNS
python -m dns_changer.cli.dns_cli set Shecan       # activate a provider
python -m dns_changer.cli.dns_cli reset            # revert to DHCP
```

---

## Project Structure

```
dns_changer/
├── main.py                  # GUI entry point
├── core/
│   ├── providers.py         # DNSProvider dataclass + registry (edit here only)
│   ├── adapter.py           # WMI calls (isolated here only)
│   └── dns_service.py       # business logic + state machine
├── ui/
│   └── main_window.py       # Tkinter window (RTL)
├── cli/
│   └── dns_cli.py           # Rich CLI (interactive + one-shot)
└── utils/
    └── privileges.py        # UAC elevation helpers
```

---

## How to Contribute

1. Fork the repository from [github.com/alisadeghiaghili/free-dns-setter](https://github.com/alisadeghiaghili/free-dns-setter)
2. Create a new branch for your changes
3. Commit with descriptive messages following [Conventional Commits](https://www.conventionalcommits.org/)
4. Push and open a pull request

To add a new DNS provider, edit **only** `core/providers.py` — no other file needs to change.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
