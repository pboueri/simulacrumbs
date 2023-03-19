from typer import Typer

from simulacrumbs.agents.base import Agent
from simulacrumbs.games.base import AgentGame


app = Typer()


@app.command()
def warrior():
    game = AgentGame(agents=[Agent("You are a warrior"), Agent("You are a ballerina")], title="Warrior Game")
    game.setup()
    game.run()


@app.command()
def sims():
    pass
