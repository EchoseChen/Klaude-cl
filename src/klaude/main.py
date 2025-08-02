import click
from klaude.agent import Agent


@click.command()
@click.option('-p', '--prompt', required=True, help='User prompt for the agent')
def main(prompt: str):
    agent = Agent()
    agent.run(prompt)


if __name__ == '__main__':
    main()