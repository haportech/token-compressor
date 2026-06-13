"""Live token savings dashboard — watches stats JSONL in real-time."""
import json
import os
import time
from pathlib import Path

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

STATS_PATH = Path.home() / ".hermes" / "token-compressor-stats.jsonl"
COST_PER_TOKEN = 0.43 / 1_000_000  # DeepSeek v4 input cost


def load_stats():
    """Load all stats from JSONL file."""
    if not STATS_PATH.exists():
        return []
    entries = []
    with open(STATS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def render(entries):
    """Render the full dashboard layout."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
    )

    now = time.strftime("%H:%M:%S")
    header = Panel(
        Text(f"Token Compressor Dashboard — {now}", style="bold cyan"),
        style="bright_black",
    )
    layout["header"].update(header)

    body = Layout()
    body.split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1),
    )
    layout["body"].update(body)

    # Summary panel
    total_saved = sum(e["saved_tokens"] for e in entries)
    total_compressions = len(entries)
    dollars_saved = total_saved * COST_PER_TOKEN

    if entries:
        avg_pct = sum(e["savings_pct"] for e in entries) / len(entries)
    else:
        avg_pct = 0

    summary_text = Text()
    summary_text.append("Compressions: ", style="dim")
    summary_text.append(f"{total_compressions}\n", style="bold yellow")
    summary_text.append("Tokens saved: ", style="dim")
    summary_text.append(f"{total_saved:,}\n", style="bold green")
    summary_text.append("Dollars saved: ", style="dim")
    code = f"${dollars_saved:.4f}"
    if dollars_saved > 0.01:
        summary_text.append(code, style="bold green")
    else:
        summary_text.append(code, style="yellow")
    summary_text.append("\nAvg savings:    ", style="dim")
    summary_text.append(f"{avg_pct:.0f}%", style="bold cyan")

    summary = Panel(summary_text, title="Session Totals", border_style="cyan")
    body["right"].update(summary)

    # Recent compressions table
    table = Table(title="Recent Compressions", border_style="bright_black")
    table.add_column("#", style="dim", width=4)
    table.add_column("Time", style="cyan", width=10)
    table.add_column("Strategy", style="magenta", width=12)
    table.add_column("In", justify="right", style="yellow")
    table.add_column("Out", justify="right", style="green")
    table.add_column("Saved", justify="right", style="bold green")
    table.add_column("Pct", justify="right", style="cyan")
    table.add_column("Source", style="dim", max_width=40, no_wrap=True)

    for i, e in enumerate(entries[-10:], 1):
        ts = e["timestamp"][11:19] if "T" in e["timestamp"] else e["timestamp"][:8]
        table.add_row(
            str(i),
            ts,
            e["strategy"],
            f"{e['input_tokens']:,}",
            f"{e['output_tokens']:,}",
            f"{e['saved_tokens']:,}",
            f"{e['savings_pct']:.0f}%",
            e["source"],
        )

    body["left"].update(Panel(table, border_style="bright_black"))

    return layout


def main():
    """Run the live dashboard."""
    console = Console()
    console.clear()

    with Live(console=console, refresh_per_second=1, screen=True) as live:
        last_size = 0
        while True:
            entries = load_stats()
            if not entries:
                live.update(
                    Panel(
                        Text("Waiting for compression events...\n\nRun Hermes in another terminal.",
                             style="dim yellow", justify="center"),
                        border_style="yellow",
                    )
                )
            else:
                live.update(render(entries))
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
