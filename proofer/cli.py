import click

from proofer.agent import build_graph
from proofer.state import AgentState


@click.command()
@click.argument("file_path", type=click.Path(exists=True), required=False)
@click.option("--text", "-t", help="Direct text input instead of file")
@click.option(
    "--yes", is_flag=True, help="Automatically approve and apply suggested changes."
)
def cli(file_path, text, yes):
    if not file_path and not text:
        raise click.ClickException("Either provide a file path or use --text option")

    if file_path and text:
        raise click.ClickException("Cannot use both file path and --text option")

    graph = build_graph()

    if text:
        initial_state: AgentState = {"input_text": text, "auto_approve": yes}
    else:
        initial_state: AgentState = {"path": str(file_path), "auto_approve": yes}

    graph.invoke(initial_state)
