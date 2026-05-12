"""
scripts/leadiq_tui.py — LeadIQ v3 Terminal Dashboard (Python + Rich)
Power-user terminal interface for lead intelligence.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()


def build_dashboard(leads: list, stats: dict, anomalies: list, fusions: list, trends: list) -> Layout:
    """Build the TUI dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="hot_leads", ratio=2),
        Layout(name="side", ratio=1),
    )
    layout["side"].split_column(
        Layout(name="anomalies"),
        Layout(name="trends"),
    )

    # Header
    header_text = Text("🔥 LeadIQ v3 — WORLDCLASS LEAD INTELLIGENCE", style="bold cyan")
    layout["header"].update(Panel(header_text, border_style="cyan"))

    # Stats bar
    stats_table = Table.grid(padding=(0, 2))
    stats_table.add_row(
        f"[bold red]🔥 HOT: {stats['hot']}[/]",
        f"[bold yellow]🌡 WARM: {stats['warm']}[/]",
        f"[bold blue]🟢 COOL: {stats['cool']}[/]",
        f"[dim]❄️ COLD: {stats['cold']}[/]",
        f"[dim]📊 ANOM: {len(anomalies)}[/]",
        f"[dim]🔗 FUSIONS: {len(fusions)}[/]",
    )
    layout["stats"].update(Panel(stats_table, border_style="green"))

    # HOT leads table
    hot_table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold red")
    hot_table.add_column("#", width=3)
    hot_table.add_column("Score", width=6)
    hot_table.add_column("Title", max_width=40)
    hot_table.add_column("Source", width=10)
    hot_table.add_column("Signals", width=20)

    scored = sorted(leads, key=lambda x: x["score"].overall, reverse=True)
    for i, lead in enumerate(scored[:15], 1):
        s = lead["score"]
        p = lead["post"]
        style = "bold red" if s.confidence == "HOT" else "yellow" if s.confidence == "WARM" else "cyan" if s.confidence == "COOL" else "dim"
        hot_table.add_row(
            str(i),
            f"[{style}]{s.overall}[/]",
            p.title[:37] + "..." if len(p.title) > 40 else p.title,
            p.source,
            ", ".join(k for k, v in s.dimensions.items() if v > 50)[:20],
            style=style,
        )
    layout["hot_leads"].update(Panel(hot_table, title="🔎 LEADS (sorted by score)", border_style="bright_green"))

    # Anomalies
    anomaly_text = Text()
    for a in anomalies[:5]:
        sev = a.get("severity", "low")
        color = "red" if sev in ("high",) else "yellow" if sev in ("medium",) else "dim"
        anomaly_text.append(f"[{color}]🚨 {a.get('signal_type')} z={a.get('z_score')}\n[/]")
    layout["anomalies"].update(Panel(anomaly_text, title="🚨 ANOMALIES", border_style="yellow"))

    # Trends
    trends_text = Text()
    for t in trends[:5]:
        tid = t.get("topic_id") or t.get("keyword")
        ms = t.get("momentum_score", 0)
        color = "red" if ms > 60 else "yellow" if ms > 30 else "dim"
        trends_text.append(f"[{color}]{ms}: {tid}\n[/]")
    layout["trends"].update(Panel(trends_text, title="📈 TRENDS", border_style="cyan"))

    # Footer
    layout["footer"].update(Panel(
        Text("[q]uit  [n]ext  [p]rev  [s]core  [f]ilter  [e]xport  [t]rends", style="dim"),
        border_style="grey",
    ))

    return layout


async def main():
    """Entry point for TUI dashboard."""
    from backend.pipeline_v3 import run_full_pipeline

    console.print("[bold cyan]⏳ Collecting leads from 4 sources...[/]")
    result = await run_full_pipeline()

    leads = result["leads"]
    stats = result["stats"]
    anomalies = result.get("anomalies", [])
    fusions = result.get("fusions", [])
    trends_list = result.get("trends", [])

    layout = build_dashboard(leads, stats, anomalies, fusions, trends_list)

    with Live(layout, refresh_per_second=2, screen=True) as live:
        console.print("[bold cyan]✅ Pipeline complete. Press Ctrl+C to exit.[/]")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[dim]🛑 LeadIQ TUI closed.[/]")


if __name__ == "__main__":
    asyncio.run(main())