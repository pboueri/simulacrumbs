from typing import List

from pydantic import BaseModel

from simulacrumbs.agents.base import Agent


class GameState(BaseModel):
    agents: List[Agent]

    def generate_prompt(self, agent: Agent, valid_actions: List[Action]) -> str:
        pass
