"""Config command for Hyper-Extract CLI."""

from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..config import ConfigManager
from hyperextract.utils.logging import get_logger
import typer

logger = get_logger("he.config")
console = Console()

_PROVIDER_HELP = "Provider preset: openai, anthropic, bailian, vllm, litellm"

app = typer.Typer(
    name="config",
    help="Manage LLM and Embedder configuration",
    invoke_without_command=True,
)


def _normalize_proxy_url(url: str) -> str:
    """Ensure proxy URL uses http(s) and ends with /v1 when appropriate."""
    url = url.strip().rstrip("/")
    if not url:
        return url
    if not url.startswith(("http://", "https://")):
        console.print(
            "  [yellow]URL should start with http:// or https:// — prepending https://[/yellow]"
        )
        url = f"https://{url}"
    if not url.endswith("/v1"):
        console.print("  [dim]Appending /v1 to base URL[/dim]")
        url = f"{url}/v1"
    return url


def _prompt_api_key(*, allow_dummy: bool = False) -> str:
    """Prompt until a non-empty API key is entered (or dummy for local vLLM)."""
    while True:
        api_key = console.input("  API Key: ").strip()
        if api_key:
            return api_key
        if allow_dummy:
            console.print("  [dim]Using 'dummy' for vLLM[/dim]")
            return "dummy"
        console.print("  [red]API Key is required. Please enter your API key.[/red]")


def _prompt_remote_proxy(
    provider: str,
    *,
    allow_dummy_key: bool = False,
    shared_base_url: str = "",
) -> Tuple[str, str, str]:
    """Prompt for model, base URL, and API key for remote/local proxy providers."""
    if provider == "litellm":
        if shared_base_url:
            base_url = shared_base_url
        else:
            raw_url = console.input(
                "  Proxy Base URL (e.g. https://litellm.example.com/v1): "
            ).strip()
            base_url = _normalize_proxy_url(raw_url)
        model = console.input(
            "  LLM Model (e.g. gpt-4o-mini): "
        ).strip()
    elif provider == "vllm":
        model = console.input("  LLM Model: ").strip()
        base_url = console.input(
            "  LLM Base URL (e.g. http://localhost:8000/v1): "
        ).strip()
    else:
        model = ""
        base_url = shared_base_url

    api_key = _prompt_api_key(allow_dummy=allow_dummy_key)
    return model, base_url, api_key


def _print_config_summary(
    *,
    provider: str,
    llm_model: str,
    emb_model: str,
    base_url: str,
    api_key: str,
) -> None:
    """Print a Rich panel summarizing saved configuration."""
    lines = [
        f"[cyan]Provider:[/cyan]       {provider}",
        f"[cyan]Proxy URL:[/cyan]      {base_url or '(default)'}",
        f"[cyan]LLM Model:[/cyan]      {llm_model}",
        f"[cyan]Embedder Model:[/cyan] {emb_model}",
        f"[cyan]API Key:[/cyan]        {api_key[:10]}..." if api_key else "[cyan]API Key:[/cyan]        (not set)",
    ]
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold green]Configuration Saved[/bold green]",
            border_style="green",
        )
    )
    console.print("[dim]Run [bold cyan]he config show[/bold cyan] to verify settings.[/dim]")


def _print_provider_table() -> list[tuple[str, str, str, str]]:
    """Render provider selection table and return provider options."""
    providers = [
        ("openai", "OpenAI", "Cloud", "api.openai.com/v1"),
        ("bailian", "Bailian", "Cloud", "dashscope compatible-mode/v1"),
        ("vllm", "vLLM", "Local", "localhost:8000/v1"),
        ("litellm", "LiteLLM Proxy", "Remote proxy", "your-host:4000/v1"),
        ("custom", "Custom", "OpenAI-compatible", "custom URL"),
    ]

    table = Table(
        title="Step 1: Choose Provider",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Provider", style="cyan", width=18)
    table.add_column("Type", style="blue", width=16)
    table.add_column("Endpoint hint", style="dim")

    for i, (_key, name, ptype, hint) in enumerate(providers, 1):
        table.add_row(str(i), name, ptype, hint)

    console.print(table)
    return providers


@app.callback()
def config_callback(
    ctx: typer.Context,
):
    """Show configuration help when running 'he config' without subcommand."""
    if ctx.invoked_subcommand is not None:
        return

    from ..utils import LOGO

    console.print()
    console.print(Text(LOGO, style="bold cyan"))

    from rich.rule import Rule

    console.print(Rule(style="cyan dim"))
    console.print()

    title_text = Text("CONFIGURATION", style="bold cyan")
    desc_text = Text("Manage LLM and Embedder settings", style="dim")

    header = Table(box=None, show_header=False, pad_edge=False)
    header.add_column(no_wrap=True)
    header.add_column(style="dim white", no_wrap=True)
    header.add_row(title_text, desc_text)

    console.print(header)
    console.print()
    console.print(Rule(style="cyan dim"))
    console.print()

    console.print("[bold cyan]Available Commands:[/bold cyan]")
    console.print()

    commands_info = [
        (
            "he config init",
            "Interactive configuration setup (recommended for first-time users)",
        ),
        ("he config show", "Display current configuration"),
        ("he config llm", "Configure LLM settings"),
        ("he config embedder", "Configure Embedder settings"),
    ]

    for cmd, desc in commands_info:
        console.print(f"  [green]{cmd:<30}[/green] {desc}")

    console.print()
    console.print(Rule(style="cyan dim"))
    console.print()

    console.print("[bold cyan]Quick Start:[/bold cyan]")
    console.print()
    console.print(
        "  [yellow]1.[/yellow] Run [green]he config init[/green] for interactive setup"
    )
    console.print("  [yellow]2.[/yellow] Or configure individually:")
    console.print("     [green]he config llm --api-key YOUR_KEY[/green]")
    console.print("     [green]he config embedder --api-key YOUR_KEY[/green]")
    console.print()

    console.print("[bold cyan]Environment Variables (alternative):[/bold cyan]")
    console.print()
    console.print(
        "  [green]OPENAI_API_KEY[/green] - OpenAI API key (used if not set in config)"
    )
    console.print(
        "  [green]ANTHROPIC_API_KEY[/green] - Anthropic/Claude API key (or CLAUDE_API_KEY)"
    )
    console.print("  [green]OPENAI_BASE_URL[/green] - Custom API base URL (optional)")
    console.print(
        "  [green]LITELLM_BASE_URL[/green] - LiteLLM proxy URL (when provider is litellm)"
    )
    console.print(
        "  [green]LITELLM_API_KEY[/green] - LiteLLM master key (or LITELLM_MASTER_KEY)"
    )
    console.print()

    console.print(Rule(style="cyan dim"))
    console.print()

    hint_text = Text("💡 Tip: Run ", style="dim")
    hint_text.append("he config <command> --help", style="bold cyan")
    hint_text.append(" for detailed command usage", style="dim")
    console.print(hint_text)
    console.print()

    raise typer.Exit()


def _show_config():
    """Show current configuration."""
    config = ConfigManager()
    cfg = config.show()

    table = Table(title="Hyper-Extract Configuration")
    table.add_column("Service", style="cyan", width=12)
    table.add_column("Provider", style="blue", width=12)
    table.add_column("Model", style="yellow", width=28)
    table.add_column("API Key", style="magenta", width=20)
    table.add_column("Base URL", style="green", width=30)

    llm_cfg = cfg["llm"]
    emb_cfg = cfg["embedder"]

    table.add_row(
        "LLM",
        llm_cfg.get("provider", "-") or "-",
        llm_cfg["model"],
        llm_cfg["api_key"][:10] + "..." if llm_cfg["api_key"] else "(not set)",
        llm_cfg["base_url"] or "(default)",
    )
    table.add_row(
        "Embedder",
        emb_cfg.get("provider", "-") or "-",
        emb_cfg["model"],
        emb_cfg["api_key"][:10] + "..." if emb_cfg["api_key"] else "(not set)",
        emb_cfg["base_url"] or "(default)",
    )

    console.print(table)


@app.command(name="show")
def show(
    show_all: bool = typer.Option(False, "--show", help="Show all configuration"),
):
    """Show current configuration."""
    logger.info("command=config-show")
    _show_config()


@app.command(name="llm")
def llm(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help=_PROVIDER_HELP,
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="LLM API key",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="LLM model name",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-u",
        help="Custom API base URL",
    ),
    show: bool = typer.Option(False, "--show", help="Show current LLM configuration"),
    unset: bool = typer.Option(False, "--unset", help="Unset LLM configuration"),
):
    """Configure LLM settings."""
    logger.info("command=config-llm show=%s unset=%s", show, unset)
    config = ConfigManager()

    if show:
        cfg = config.get_llm_config()
        table = Table(title="LLM Configuration", show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Provider", cfg.provider or "(not set)")
        table.add_row("Model", cfg.model)
        table.add_row(
            "API Key", cfg.api_key[:10] + "..." if cfg.api_key else "(not set)"
        )
        table.add_row("Base URL", cfg.base_url or "(default)")
        console.print(table)
        return

    if unset:
        config.unset_llm()
        console.print("[green]LLM configuration cleared[/green]")
        return

    config.set_llm(
        provider=provider,
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    console.print("[green]LLM configuration updated[/green]")


@app.command(name="embedder")
def embedder(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help=_PROVIDER_HELP,
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Embedder API key",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Embedder model name",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-u",
        help="Custom API base URL",
    ),
    show: bool = typer.Option(
        False, "--show", help="Show current Embedder configuration"
    ),
    unset: bool = typer.Option(False, "--unset", help="Unset Embedder configuration"),
):
    """Configure Embedder settings."""
    logger.info("command=config-embedder show=%s unset=%s", show, unset)
    config = ConfigManager()

    if show:
        cfg = config.get_embedder_config()
        table = Table(title="Embedder Configuration", show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Provider", cfg.provider or "(not set)")
        table.add_row("Model", cfg.model)
        table.add_row(
            "API Key", cfg.api_key[:10] + "..." if cfg.api_key else "(not set)"
        )
        table.add_row("Base URL", cfg.base_url or "(default)")
        console.print(table)
        return

    if unset:
        config.unset_embedder()
        console.print("[green]Embedder configuration cleared[/green]")
        return

    config.set_embedder(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
    )
    console.print("[green]Embedder configuration updated[/green]")


@app.command(name="init")
def init(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help=_PROVIDER_HELP,
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key for both LLM and Embedder",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        "-u",
        help="Custom API base URL",
    ),
):
    """Initialize configuration interactively."""
    logger.info(
        "command=config-init provider=%s api_key_provided=%s",
        provider,
        api_key is not None,
    )
    config = ConfigManager()

    # Quick mode: provider + api_key provided
    if provider and api_key:
        from hyperextract.utils.client import PROVIDER_PRESETS, REMOTE_PROXY_PROVIDERS

        preset = PROVIDER_PRESETS.get(provider, {})
        preset_url = preset.get("base_url") or ""
        resolved_base = base_url or preset_url

        if provider in REMOTE_PROXY_PROVIDERS and not resolved_base:
            console.print(
                f"[red]Error:[/red] Provider '{provider}' requires --base-url.\n"
                f"  Example: he config init -p {provider} -k YOUR_KEY "
                f"-u https://your-proxy/v1"
            )
            raise typer.Exit(1)

        llm_model = preset.get("default_llm") or "gpt-4o-mini"
        emb_model = preset.get("default_embedder") or "text-embedding-3-small"

        config.set_llm(
            provider=provider,
            model=llm_model,
            api_key=api_key,
            base_url=resolved_base,
        )
        if emb_model:
            config.set_embedder(
                provider=provider,
                model=emb_model,
                api_key=api_key,
                base_url=resolved_base,
            )
        else:
            console.print(
                "[yellow]Warning: Provider '{}' has no default embedder. "
                "Please configure embedder separately.[/yellow]".format(provider)
            )

        _print_config_summary(
            provider=provider,
            llm_model=llm_model,
            emb_model=emb_model or "(configure separately)",
            base_url=resolved_base,
            api_key=api_key,
        )
        return

    # Legacy quick mode: only api_key provided (OpenAI defaults)
    if api_key and not provider:
        config.set_llm(
            provider="openai",
            model="gpt-4o-mini",
            api_key=api_key,
            base_url=base_url,
        )
        config.set_embedder(
            provider="openai",
            model="text-embedding-3-small",
            api_key=api_key,
            base_url=base_url,
        )
        _print_config_summary(
            provider="openai",
            llm_model="gpt-4o-mini",
            emb_model="text-embedding-3-small",
            base_url=base_url or "",
            api_key=api_key,
        )
        return

    # Interactive mode
    console.print("[bold cyan]Hyper-Extract Configuration Setup[/bold cyan]")
    console.print()

    from hyperextract.utils.client import PROVIDER_PRESETS

    providers = _print_provider_table()
    console.print()
    choice = console.input("Select provider [1-5]: ").strip()
    try:
        selected = providers[int(choice) - 1][0] if choice.isdigit() else "openai"
    except (IndexError, ValueError):
        selected = "openai"

    preset = PROVIDER_PRESETS.get(selected, {})
    preset_url = preset.get("base_url") or ""
    default_llm = preset.get("default_llm") or "gpt-4o-mini"
    default_emb = preset.get("default_embedder") or "text-embedding-3-small"

    console.print()
    console.print(f"[bold]Step 2: LLM Configuration (Provider: {selected})[/bold]")

    if selected == "litellm":
        raw_url = console.input(
            "  Proxy Base URL (e.g. https://litellm.example.com/v1): "
        ).strip()
        proxy_url = _normalize_proxy_url(raw_url)
        llm_model = console.input(
            f"  LLM Model (default: {default_llm}): "
        ).strip() or default_llm
        llm_api_key = _prompt_api_key(allow_dummy=False)
        llm_base_url = proxy_url

        config.set_llm(
            provider=selected,
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url or None,
        )

        console.print()
        console.print("[bold]Step 3: Embedder Configuration[/bold]")
        emb_model = console.input(
            f"  Embedder Model (default: {default_emb}): "
        ).strip() or default_emb
        emb_api_key = llm_api_key
        emb_base_url = proxy_url

        config.set_embedder(
            provider=selected,
            model=emb_model,
            api_key=emb_api_key,
            base_url=emb_base_url or None,
        )

        console.print()
        _print_config_summary(
            provider=selected,
            llm_model=llm_model,
            emb_model=emb_model,
            base_url=proxy_url,
            api_key=llm_api_key,
        )
        return

    if selected == "vllm":
        llm_model, llm_base_url, llm_api_key = _prompt_remote_proxy(
            selected, allow_dummy_key=True
        )
    else:
        llm_model = (
            console.input(f"  Model (default: {default_llm}): ").strip() or default_llm
        )
        llm_base_url = (
            console.input(
                f"  Base URL (default: {preset_url}, press Enter to skip): "
            ).strip()
            or preset_url
        )
        llm_api_key = _prompt_api_key(allow_dummy=False)

    config.set_llm(
        provider=selected,
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url or None,
    )

    console.print()
    console.print("[bold]Step 3: Embedder Configuration[/bold]")

    if selected == "vllm":
        emb_model = console.input("  Embedder Model (e.g. bge-m3): ").strip()
        emb_base_url = console.input(
            "  Embedder Base URL (e.g. http://localhost:8001/v1): "
        ).strip()
        emb_api_key = _prompt_api_key(allow_dummy=True)
    else:
        emb_model = (
            console.input(f"  Model (default: {default_emb}): ").strip() or default_emb
        )
        emb_base_url = (
            console.input(
                f"  Base URL (default: {preset_url}, press Enter to skip): "
            ).strip()
            or preset_url
        )
        emb_api_key = _prompt_api_key(allow_dummy=False)

    config.set_embedder(
        provider=selected,
        model=emb_model,
        api_key=emb_api_key,
        base_url=emb_base_url or None,
    )

    console.print()
    _print_config_summary(
        provider=selected,
        llm_model=llm_model,
        emb_model=emb_model,
        base_url=llm_base_url or emb_base_url,
        api_key=llm_api_key,
    )
