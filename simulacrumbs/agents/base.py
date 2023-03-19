from pydantic import BaseModel
import json
from time import time

from arcade import Sprite
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser

from enum import Enum


class Action(str, Enum):
    MOVE_LEFT: str = "left"
    MOVE_RIGHT: str = "right"
    MOVE_UP: str = "up"
    MOVE_DOWN: str = "down"
    STAY: str = "stay"


class GameAction(BaseModel):
    action: Action
    thought: str


class Agent(Sprite):
    score: int = 0

    def __init__(self, personality: str, move_delay: float = 5):
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png")
        self.prompt = PromptTemplate(
            template="{personality} \n {game_state} \n Respond with json and only json conforming to the following schema {format_instructions} \n What action you do next? {{",
            input_variables=["game_state"],
            partial_variables={"format_instructions": GameAction.schema_json(), "personality": personality},
        )
        self.personality = personality
        self.llm = OpenAI(model_name="curie", temperature=0.5, model_kwargs={"stop": ["}"]})
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        self.thought_history = ""
        self.move_history = ""
        self.game_state = ""
        self.last_move = time()
        self.move_delay = move_delay

    
    def update_personality(self, personality: str):
        self.prompt.partial_variables["personality"] = personality

    def update(self):
        if time() - self.last_move < self.move_delay:
            return
        else:
            self.last_move = time()
            action = self.next_action(self.game_state)
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
            self.thought_history +=  "\n" + action.thought
            self.move_history += "\n" + action.action

    def next_action(self, game_state: str) -> GameAction:
        # TODO only provide valid moves
        try:
            result = self.chain(game_state)
            result = "{" + result["text"] + "}"
            action = GameAction(**json.loads(result))
        except Exception as e:
            action = GameAction(action=Action.STAY, thought="I don't know what to do")
        return action


if __name__ == "__main__":
    agent = Agent("You are a toddler")
    game_state = "you are in a room with a table and a chair."
    print(agent.prompt.format_prompt(game_state=game_state))
    print(agent.next_action(game_state=game_state))
