from typing import List

import arcade
from arcade import load_texture
from arcade import gui
import random

from simulacrumbs.agents.base import Agent
from concurrent import futures

TEXT_WIDTH = 200
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
THOUGHT_HISTORY = "These are agent thoughts:\n"
MOVE_HISTORY = "These are the agents moves:\n"

# A pydantic BaseModel that keeps track of Game state including agents and actions
class AgentGame(arcade.Window):
    def __init__(self, title, agents: List[Agent]) -> None:
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, title)
        self.agents = agents
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=3)
        for agent in self.agents:
            agent.thread_pool = self.thread_pool
        self.manager = gui.UIManager()
        self.manager.enable()
        # Create a chat area on the left side of the window that records agent thoughts
        self.agent_thoughts = []
        self.agent_prompts = []
        self.agent_moves = []
        for ix,agent in enumerate(agents):
            agent_thought = gui.UITextArea(
                x=TEXT_WIDTH*ix, y=0, width=TEXT_WIDTH*(ix+1), height=300, text=THOUGHT_HISTORY, multiline=True, text_color=arcade.color.BLACK
            )
            agent_moves = gui.UITextArea(
                x=TEXT_WIDTH*ix, y=300, width=TEXT_WIDTH*(ix+1), height=300, text=MOVE_HISTORY, multiline=True, text_color=arcade.color.BLACK
            )
            agent_prompt = gui.UIInputText(
                x=TEXT_WIDTH*ix, y=600, width=TEXT_WIDTH*(ix+1), height=200, text=agent.personality
            )
            self.manager.add(agent_thought)
            self.manager.add(agent_prompt)
            self.manager.add(agent_moves)
            self.agent_thoughts.append(agent_thought)
            self.agent_prompts.append(agent_prompt)
            self.agent_moves.append(agent_moves)
            
        self.start_width = TEXT_WIDTH*len(agents)
        arcade.set_background_color(arcade.color.WHITE)

    def setup(self):
        self.agent_list = arcade.SpriteList()
        for agent in self.agents:
            agent.center_x = random.randrange(self.start_width, SCREEN_WIDTH)
            agent.center_y = random.randrange(SCREEN_HEIGHT)
        self.agent_list.extend(self.agents)

    def update(self, delta_time: float):
        self.agent_list.update()
        for ix, agent in enumerate(self.agents):
            agent.game_state = f"""
You are in a room at position ({agent.center_x},{agent.center_y}).
There are {len(self.agents)-1} other Agents in the room
Your most recent action was {agent.past_actions[-1].action if len(agent.past_actions) > 0 else ''}
Your most recent thought was "{agent.past_actions[-1].thought if len(agent.past_actions) > 0 else ''}"
             """
            agent.update_personality(self.agent_prompts[ix].text)
            self.agent_thoughts[ix].text = THOUGHT_HISTORY + "\n" + agent.thought_history
            self.agent_moves[ix].text = MOVE_HISTORY + "\n" + agent.action_history
        # Correct for any agents that have moved outside of the boundary
        for agent in self.agents:
            if agent.center_x < self.start_width:
                agent.center_x = self.start_width
            if agent.center_x > SCREEN_WIDTH:
                agent.center_x = SCREEN_WIDTH
            if agent.center_y < 0:
                agent.center_y = 0
            if agent.center_y > SCREEN_HEIGHT:
                agent.center_y = SCREEN_HEIGHT

    def on_draw(self):
        self.clear()
        self.manager.draw()
        self.agent_list.draw()
