import click

from proofer.agent import build_graph
from proofer.state import AgentState


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--yes", is_flag=True, help="Automatically approve and apply suggested changes."
)
def main(file_path, yes):
    graph = build_graph()
    initial_state: AgentState = {"path": str(file_path), "auto_approve": yes}
    graph.invoke(initial_state)
