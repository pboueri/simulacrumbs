from pydantic import BaseModel
import json
from typing import Literal
from time import time

from arcade import Sprite
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from concurrent import futures

from enum import Enum


class Action(str, Enum):
    MOVE_LEFT: str = "left"
    MOVE_RIGHT: str = "right"
    MOVE_UP: str = "up"
    MOVE_DOWN: str = "down"
    STAY: str = "stay"


class GameAction(BaseModel):
    action: Literal[Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN, Action.STAY]
    thought: str


class Agent(Sprite):
    score: int = 0

    def __init__(self, personality: str, move_delay: float = 3):
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png")
        self.prompt = PromptTemplate(
            template="{personality} \n {game_state} \n Respond with json and only json conforming to the following schema {format_instructions} \n What action you do next? {{",
            input_variables=["game_state"],
            partial_variables={"format_instructions": GameAction.schema_json(), "personality": personality},
        )
        self.personality = personality
        self.llm = OpenAI( temperature=0.5, model_kwargs={"stop": ["}"]})
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        self.past_actions = []
        self.game_state = ""
        self.last_move = time()
        self.move_delay = move_delay
        self.thread_pool: futures.ThreadPoolExecutor = None
        self.pending_action = None

    @property
    def thought_history(self):
        return "\n".join([action.thought for action in self.past_actions])

    @property
    def action_history(self):
        return "\n".join([action.action for action in self.past_actions])
    
    def update_personality(self, personality: str):
        self.prompt.partial_variables["personality"] = personality

    def update(self):
        if time() - self.last_move < self.move_delay:
            return
        elif self.pending_action is None:
            self.pending_action = self.thread_pool.submit(self.next_action)
        elif self.pending_action.done():
            self.last_move = time()
            action = self.pending_action.result()
            if action.action == Action.MOVE_LEFT:
                self.center_x -= 10
            elif action.action == Action.MOVE_RIGHT:
                self.center_x += 10
            elif action.action == Action.MOVE_UP:
                self.center_y += 10
            elif action.action == Action.MOVE_DOWN:
                self.center_y -= 10
            elif action.action == Action.STAY:
                pass
            self.past_actions.append(action)
            self.pending_action = None
        elif self.pending_action.running():
            pass

    def next_action(self) -> GameAction:
        # TODO only provide valid moves
        try:
            result = self.chain(self.game_state)
            result = "{" + result["text"] + "}"
            action = GameAction(**json.loads(result))
        except Exception as e:
            print(result)
            action = GameAction(action=Action.STAY, thought="I don't know what to do")
        return action


if __name__ == "__main__":
    agent = Agent("You are a toddler")
    game_state = "you are in a room with a table and a chair."
    print(agent.prompt.format_prompt(game_state=game_state))
    print(agent.next_action(game_state=game_state))
