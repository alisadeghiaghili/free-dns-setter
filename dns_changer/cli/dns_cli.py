"""
Rich interactive CLI for DNS Changer.
Talks only to DNSService — no WMI, no GUI, no OS calls here.

Usage
-----
  python -m dns_changer.cli.dns_cli            # interactive TUI menu
  python -m dns_changer.cli.dns_cli set Shecan # non-interactive one-shot
  python -m dns_changer.cli.dns_cli reset      # revert to DHCP
  python -m dns_changer.cli.dns_cli status     # show current DNS
  python -m dns_changer.cli.dns_cli list       # list all providers
"""

from __future__ import annotations
import sys
import argparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.align import Align

from ..core import DNSService, ServiceError
from ..core.providers import providers_by_category, Category

console = Console()

# ── category styling ────────────────────────────────────────────────────────
CATEGORY_STYLE: dict[Category, tuple[str, str]] = {
    Category.ANTI_SANCTION: ("green", "🔓"),
    Category.ANTI_FILTER: ("cyan", "🚫"),
    Category.GAMING: ("magenta", "🎮"),
    Category.GENERAL: ("yellow", "🌐"),
}


# ── helpers ─────────────────────────────────────────────────────────────────


def _style(cat: Category) -> tuple[str, str]:
    return CATEGORY_STYLE.get(cat, ("white", "•"))


def _dns_status_text(service: DNSService) -> Text:
    servers = service.current_dns()
    if not servers:
        return Text("Automatic", style="dim")
    return Text(", ".join(servers), style="bold white")


def _active_panel(service: DNSService) -> Panel:
    if service.is_active:
        p = service.active_provider
        color, icon = _style(p.category)
        content = (
            f"{icon}  [bold {color}]{p.name}[/] is [bold green]ACTIVE[/]\n"
            f"[dim]{p.description}[/]\n\n"
            f"[dim]Primary  :[/] [bold]{p.primary}[/]\n"
            f"[dim]Secondary:[/] [bold]{p.secondary}[/]\n\n"
            f"[dim]Current OS DNS:[/] {_dns_status_text(service)}"
        )
        return Panel(
            content, title="[bold green]● DNS Status[/]", border_style="green", padding=(1, 2)
        )
    else:
        content = (
            f"[bold red]● No custom DNS active[/]\n\n"
            f"[dim]Current OS DNS:[/] {_dns_status_text(service)}"
        )
        return Panel(content, title="[bold red]● DNS Status[/]", border_style="red", padding=(1, 2))


def _providers_table() -> Table:
    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold bright_white",
        title="[bold]Available DNS Providers[/]",
        title_style="bold cyan",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("Provider", style="bold white", width=14)
    table.add_column("Category", width=14)
    table.add_column("Primary", style="cyan", width=17)
    table.add_column("Secondary", style="cyan", width=17)
    table.add_column("Description", style="dim", min_width=20)

    idx = 1
    for category, providers in providers_by_category().items():
        if not providers:
            continue
        color, icon = _style(category)
        for p in providers:
            table.add_row(
                str(idx),
                p.name,
                f"[{color}]{icon} {category.value}[/]",
                p.primary,
                p.secondary,
                p.description,
            )
            idx += 1

    return table


# ── commands ────────────────────────────────────────────────────────────────


def cmd_list(_service: DNSService) -> None:
    console.print()
    console.print(_providers_table())
    console.print()


def cmd_status(service: DNSService) -> None:
    console.print()
    console.print(_active_panel(service))
    console.print()


def cmd_set(service: DNSService, provider_name: str) -> None:
    from ..core.providers import DNS_PROVIDERS

    # accept both key ("Shecan") and display name ("Radar Game")
    key = provider_name
    if key not in DNS_PROVIDERS:
        # try matching by display name
        key = next(
            (k for k, p in DNS_PROVIDERS.items() if p.name.lower() == provider_name.lower()),
            None,
        )
    if key is None:
        console.print(
            f"\n[bold red]✗[/] Provider [yellow]{provider_name!r}[/] not found. "
            f"Run [cyan]list[/] to see available providers.\n"
        )
        sys.exit(1)

    provider = DNS_PROVIDERS[key]
    color, icon = _style(provider.category)

    with Live(
        Spinner("dots", text=f"  Setting DNS to [bold {color}]{provider.name}[/]…"),
        console=console,
        refresh_per_second=12,
    ):
        try:
            service.activate(key)
        except ServiceError as e:
            console.print(f"\n[bold red]✗ Error:[/] {e}\n")
            sys.exit(1)

    console.print(
        f"\n[bold green]✔[/] {icon} [bold {color}]{provider.name}[/] activated\n"
        f"   [dim]Primary  →[/] [bold]{provider.primary}[/]\n"
        f"   [dim]Secondary→[/] [bold]{provider.secondary}[/]\n"
    )


def cmd_reset(service: DNSService) -> None:
    if not service.is_active:
        console.print("\n[dim]DNS is already on Automatic. Nothing to do.[/]\n")
        return

    provider_name = service.active_provider.name if service.active_provider else "custom DNS"

    with Live(
        Spinner("dots", text=f"  Reverting from [yellow]{provider_name}[/] to Automatic…"),
        console=console,
        refresh_per_second=12,
    ):
        try:
            service.deactivate()
        except ServiceError as e:
            console.print(f"\n[bold red]✗ Error:[/] {e}\n")
            sys.exit(1)

    console.print("\n[bold green]✔[/] DNS reverted to [bold]Automatic[/]\n")


def cmd_interactive(service: DNSService) -> None:
    """Full interactive TUI loop."""
    # Menu numbers must match the table's category-ordered rows, so build the
    # map from providers_by_category() (not raw dict order) via an id lookup.
    key_by_id = {id(p): key for key, p in service.available_providers().items()}
    idx_to_key: dict[str, str] = {}
    i = 1
    for provs in providers_by_category().values():
        for p in provs:
            idx_to_key[str(i)] = key_by_id[id(p)]
            i += 1

    while True:
        console.clear()
        console.print(
            Panel(
                Align.center("[bold cyan]DNS Changer[/]  [dim]— Iran DNS Manager[/]"),
                border_style="cyan",
                padding=(0, 2),
            )
        )
        console.print(_active_panel(service))
        console.print(_providers_table())

        console.print(
            "\n[dim]Enter provider [bold white]#[/] to activate  •  "
            "[bold white]r[/] to reset  •  "
            "[bold white]q[/] to quit[/]\n"
        )

        choice = Prompt.ask("[bold cyan]>[/]", console=console).strip().lower()

        if choice == "q":
            console.print("\n[dim]Goodbye.[/]\n")
            break

        elif choice == "r":
            cmd_reset(service)
            Prompt.ask("[dim]Press Enter to continue[/]", console=console, default="")

        elif choice in idx_to_key:
            key = idx_to_key[choice]
            cmd_set(service, key)
            Prompt.ask("[dim]Press Enter to continue[/]", console=console, default="")

        else:
            console.print(f"[bold red]✗[/] Unknown option: [yellow]{choice!r}[/]")
            Prompt.ask("[dim]Press Enter to continue[/]", console=console, default="")


# ── entry point ─────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dns-changer",
        description="DNS Changer CLI — manage DNS settings on your system",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all available DNS providers")
    sub.add_parser("status", help="Show current DNS status")
    sub.add_parser("reset", help="Revert DNS to Automatic")

    p_set = sub.add_parser("set", help="Activate a DNS provider")
    p_set.add_argument("provider", help="Provider name or key (e.g. Shecan, Electro)")

    return parser


def main() -> None:
    from ..utils.privileges import ensure_admin

    ensure_admin()

    service = DNSService()
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "list": lambda: cmd_list(service),
        "status": lambda: cmd_status(service),
        "reset": lambda: cmd_reset(service),
        "set": lambda: cmd_set(service, args.provider),
    }

    if args.command in dispatch:
        dispatch[args.command]()
    else:
        # no subcommand → interactive TUI
        cmd_interactive(service)


if __name__ == "__main__":
    main()
