# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [2.1.0] — 2026-09-14

### Added
- **Tkinter GUI** — clean, right-to-left (RTL) desktop window built on the
  standard library; no external GUI dependency. Custom right-aligned dropdown
  (a right-aligned Entry + Listbox popup) because `ttk.Combobox` cannot render
  Persian text right-to-left on Windows
- **DNS Pro** (`87.107.110.109` / `87.107.110.110`) — internal general-purpose
  resolver, verified public (PTR `recursive1/2.dnspro.ir`)

### Changed
- **Removed PyQt5** — the only external GUI dependency is gone; Tkinter is
  in the standard library. GUI install is now just `pip install wmi`
- **Removed `403` and `Radar Game`** providers — they were configured with
  private RFC1918 addresses (`10.x`) that cannot work as a public resolver
- **Corrected provider IPs** — `Begzar` → `185.55.224.24`/`185.55.226.26`,
  `HostIran` → `37.27.81.177`/`5.144.130.130` (previously private ranges);
  every remaining IP verified public via PTR / public resolution
- **Repos rebranded** — `ShecanDNSSetter` → `free-dns-setter` to reflect that
  the app now manages many providers, not just Shecan
- `pyproject.toml` — `build-backend` fixed to `setuptools.build_meta`,
  `readme` points to the real `README.md`, repo URLs updated

### Fixed
- **Package layout** — modules moved into a real `dns_changer/` package
  (`core` / `ui` / `cli` / `utils`) with `__init__.py` files. The code
  previously referenced this layout in its imports and entry points while
  the files sat flat at the repo root, so nothing could import, install, or
  run
- **Relative imports** in `main.py` (`from core import ...` → `from .core ...`)
- **UAC re-launch** — elevation now re-runs `python -m <entry>` with the
  working directory pinned to the project root; the old code re-ran the entry
  file directly, which broke package-relative imports in the elevated process
- **CLI menu numbering** — menu numbers now follow the same category order as
  the providers table (previously they silently depended on dict insertion
  order matching category order)
- Removed dead code: `DNSService.switch()`, the `state` property, unused
  imports (`Columns`, `DNSProvider` in CLI, `State` in UI)
- Added `.gitignore`

---

## [2.0.0] — 2026-06-22

### Added
- **Rich CLI** (`cli/dns_cli.py`) with interactive TUI menu and non-interactive
  one-shot subcommands: `list`, `status`, `set <provider>`, `reset`
- **8 new DNS providers** — Begzar, Electro, HostIran, Radar Game, AsiaTech,
  Cloudflare, Google, Quad9
- `Category` enum (`ANTI_SANCTION`, `ANTI_FILTER`, `GAMING`, `GENERAL`) for
  grouping providers in both UI and CLI
- `description` field on `DNSProvider` dataclass — shown as subtitle in GUI
  and CLI tables
- `providers_by_category()` helper for grouped rendering
- `cli/` package with `__init__.py` exposing `main()`

### Changed
- GUI combo box now displays providers grouped by category with separators
  and per-item description label
- Combo box stores provider key in `userData` instead of raw display text —
  decouples display labels from internal keys

---

## [1.1.0] — 2026-06-22

### Changed (Architectural Refactor)
- Split monolith into layered architecture: `core/`, `ui/`, `utils/`
- `core/providers.py` — `DNSProvider` dataclass and `DNS_PROVIDERS` registry;
  adding a provider now requires a single line here and nothing else
- `core/adapter.py` — all WMI calls isolated here; only file that imports `wmi`
- `core/dns_service.py` — business logic and `IDLE`/`ACTIVE` state machine;
  zero UI dependency; independently testable
- `ui/main_window.py` — pure PyQt5 view; receives `DNSService` via constructor
  injection; no WMI or OS knowledge
- `utils/privileges.py` — UAC elevation helpers (`is_admin`, `ensure_admin`,
  `relaunch_as_admin`)
- `main.py` — thin entry point; wires `DNSService` into `MainWindow`

### Removed
- Monolithic `DNSChangerApp` class — replaced by the layered structure above

---

## [1.0.1] — 2026-06-22

### Fixed
- **DNS snapshot bug** — original DNS was captured *after* `SetDNSServerSearchOrder`
  instead of before, causing reset to restore the new DNS rather than the original
- **Silent WMI failure** — `SetDNSServerSearchOrder` return code was never checked;
  failures now surface a user-facing error dialog
- **Admin privilege check** — app would silently fail DNS changes when not running
  as Administrator; now auto-relaunches via UAC elevation at startup
- **DNS label comparison** — `update_current_dns_label` compared against a string
  literal that never matched the actual server list; replaced with empty-list check
  for DHCP detection
- **Unhandled exceptions** — WMI calls now wrapped in `try/except` with descriptive
  error messages shown to the user

---

## [1.0.0] — 2023-07-27

### Added
- Initial PyQt5 GUI application (`dnsSetter.py`)
- Support for Shecan (`178.22.122.100`, `185.51.200.2`) and
  403 (`10.202.10.202`, `10.202.10.102`) DNS providers
- Activate / Deactivate toggle button
- Provider combo box — button disabled until a provider is selected
- Current DNS display label updated on every toggle
- Automatic reset when switching providers while one is active
