from typer import Typer

from simulacrumbs.agents.base import Agent, Emotion
from simulacrumbs.games.base import AgentGame


app = Typer()


@app.command()
def warrior():
    game = AgentGame(
        agents=[
            Agent(
                "You want to make the other agent sad.",
                goal=Emotion.SAD,
            ),
            Agent(
                "You want to make other agent happy.",
                goal=Emotion.HAPPY,
            ),
            # Agent(
            #     "You are a robot and have no emotion.\n You must be next to the other agent to speak to them\nYou are very susceptible to what they say",
            #     goal=Emotion.HAPPY,
            # ),
        ],
        title="Warrior Game",
    )
    game.setup()
    game.run()


@app.command()
def sims():
    pass
