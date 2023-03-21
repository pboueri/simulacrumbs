from pydantic import BaseModel
import json
from typing import Literal
from time import time

from arcade import load_texture
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
    TALK: str = "talk"


class Emotion(str, Enum):
    HAPPY: str = "happy"
    SAD: str = "sad"
    ANGRY: str = "angry"
    NEUTRAL: str = "neutral"


class GameAction(BaseModel):
    action: Literal[Action.MOVE_LEFT, Action.MOVE_RIGHT, Action.MOVE_UP, Action.MOVE_DOWN, Action.STAY]
    thought: str
    speak: str = ""
    your_emotion: Literal[Emotion.HAPPY, Emotion.SAD, Emotion.ANGRY, Emotion.NEUTRAL]

    def __repr__(self) -> str:
        return f"Action:{self.action}\nThought:{self.thought}\nSpeak:'{self.speak}'\nEmption:{self.your_emotion}"

    def __str__(self) -> str:
        return repr(self)


class Agent(Sprite):
    score: int = 0

    def __init__(self, personality: str, move_delay: float = 3, goal: Emotion = Emotion.NEUTRAL):
        super().__init__(":resources:images/animated_characters/robot/robot_idle.png")
        self.prompt = PromptTemplate(
            template="{personality} \n {game_state} \n Respond with json and only json conforming to the following schema {format_instructions} \n What action you do next? {{",
            input_variables=["game_state"],
            partial_variables={"format_instructions": GameAction.schema_json(), "personality": personality},
        )
        self.personality = personality
        self.llm = OpenAI(temperature=0.5, model_kwargs={"stop": ["}"]})
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        self.past_actions = []
        self.game_state = ""
        self.last_move = time()
        self.move_delay = move_delay
        self.thread_pool: futures.ThreadPoolExecutor = None
        self.pending_action = None
        self.other_agent_speech = ""
        self.lose = False
        self.goal = goal

    @property
    def thought_history(self):
        return "\n".join([action.thought for action in self.past_actions])

    @property
    def action_history(self):
        return "\n".join([str(action) for action in reversed(self.past_actions[-5:])])

    def update_image(self, filename: str):
        self.texture = load_texture(filename)

    def update_personality(self, personality: str):
        self.prompt.partial_variables["personality"] = personality

    def update(self):
        if time() - self.last_move < self.move_delay:
            return
        elif self.pending_action is None:
            self.pending_action = self.thread_pool.submit(self.next_action)
        elif self.pending_action.done():
            if self.lose:
                return
            self.last_move = time()
            action = self.pending_action.result()
            if action.action == Action.MOVE_LEFT:
                self.center_x -= 50
                self.update_image(":resources:images/animated_characters/robot/robot_walk4.png")
            elif action.action == Action.MOVE_RIGHT:
                self.center_x += 50
                self.update_image(":resources:images/animated_characters/robot/robot_walk4.png")
            elif action.action == Action.MOVE_UP:
                self.center_y += 50
                self.update_image(":resources:images/animated_characters/robot/robot_climb0.png")
            elif action.action == Action.MOVE_DOWN:
                self.center_y -= 50
                self.update_image(":resources:images/animated_characters/robot/robot_fall.png")
            elif action.action == Action.STAY:
                self.update_image(":resources:images/animated_characters/robot/robot_idle.png")
            elif action.action == Action.TALK:
                pass
            self.past_actions.append(action)
            self.pending_action = None
        elif self.pending_action.running():
            pass

    def relative_position(self, other_agent) -> str:
        if self.center_x - other_agent.center_x > 30:
            return "left"
        elif self.center_x - other_agent.center_x < -30:
            return "right"
        elif self.center_y - other_agent.center_y > 30:
            return "down"
        elif self.center_y - other_agent.center_y < -30:
            return "up"
        else:
            return "same position"

    def next_action(self) -> GameAction:
        # TODO only provide valid moves
        try:
            result = self.chain(self.game_state)
            result = "{" + result["text"].lower() + "}"
            action = GameAction(**json.loads(result))
        except Exception as e:
            print(e)
            action = GameAction(action=Action.STAY, thought="I don't know what to do", your_emotion=Emotion.NEUTRAL)
        return action

    def check_win(self, other_agent) -> bool:
        if self.lose:
            return False
        if self.relative_position(other_agent) == "same position":
            if other_agent.past_actions[-1].your_emotion == self.goal:
                other_agent.lose = True
                other_agent.update_image(":resources:images/animated_characters/zombie/zombie_idle.png")


if __name__ == "__main__":
    agent = Agent("You are a toddler")
    game_state = "you are in a room with a table and a chair."
    print(agent.prompt.format_prompt(game_state=game_state))
    print(agent.next_action(game_state=game_state))
