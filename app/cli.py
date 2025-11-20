"""Command-line entry point."""

from __future__ import annotations

import typer
from rich import print as rprint

from .config import IngestRequest, resolve_settings
from .pipeline import PipelineRunner

cli = typer.Typer(add_completion=False, help="Video Lectures to Searchable PDFs")


@cli.command()
def run(
    source_type: str = typer.Option(..., "--type", "-t", help="local|youtube|gdrive"),
    source: str = typer.Option(..., "--source", "-s", help="Path or URL"),
) -> None:
    """Execute the end-to-end pipeline."""

    settings = resolve_settings()
    runner = PipelineRunner(settings)
    req = IngestRequest(source_type=source_type, source=source)
    result = runner.run(req)
    rprint(
        f"[bold green]Pipeline complete[/]\n"
        f"Slide PDF: {result.slide_pdf}\n"
        f"Transcript PDF: {result.transcript_pdf}\n"
        f"Combined PDF: {result.combined_pdf}"
    )


@cli.command()
def paths() -> None:
    """Show configured directories."""

    settings = resolve_settings()
    rprint(settings.paths)


if __name__ == "__main__":
    cli()

