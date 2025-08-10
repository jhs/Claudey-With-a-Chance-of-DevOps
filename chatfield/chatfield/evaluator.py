"""LangGraph-based evaluator for Chatfield conversations."""

import uuid

from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import InMemorySaver

from .base import Dialogue


class State(TypedDict):
    messages: list[Dict[str, Any]]
    dialogue_data: Dict[str, Any]  # Serialized dialogue data (msgpack-compatible)


class Evaluator:
    """
    Evaluator that manages conversation flow.
    """
    
    def __init__(self, dialogue: Dialogue):
        self.dialogue = dialogue
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()
        self.thread_id = str(uuid.uuid4())

        self.state = State(
            messages=[], 
            dialogue_data=dialogue.to_msgpack_dict(),
        )
        
    def _build_graph(self):
        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')

        graph = builder.compile(checkpointer=self.checkpointer)
        return graph
        
    def initialize(self, state:State) -> State:
        print(f'Node> Initialize')
        # print(f'State: {state!r}')
        print(f'  Data model: {self.dialogue!r}')
        # Update state with current dialogue data
        state["dialogue_data"] = self.dialogue.to_msgpack_dict()
        return state
        
    def think(self, state: State) -> State:
        print(f'Node> Think')
        return state
    
    def route_think(self, state: State) -> str:
        print(f'Edge> Route think')
        print(f'    > State: {state!r}')
        return 'listen'
        
    def listen(self, state: State) -> State:
        print(f'Node> Listen')
        print(f'    > Interrupt')
        find_me = {'foo': 'What is the value of Foo?'}
        res = interrupt(find_me)
        print(f'    > Interrupt result is type {type(res)}: {res!r}')
        return state
        
    def go(self):
        config = {"configurable": {"thread_id": self.thread_id}}

        # Unclear if this is the correct thing to do here.
        graph_input = self.state

        for event in self.graph.stream(graph_input, config=config):
            print(f'ev>')
            for value in event.values():
                # print("Assistant:", value["messages"][-1].content)
                # print(f'  >> {type(value)} {value!r}')
                pass