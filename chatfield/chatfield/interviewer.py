"""LangGraph-based evaluator for Chatfield conversations."""

import uuid
import traceback

from pydantic import BaseModel, Field, create_model

from typing import Annotated, Any, Dict, Optional, TypedDict, List
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

# from mcp import Tool


from .base import Interview


class State(TypedDict):
    messages: List[Any]
    interview: Interview


class Interviewer:
    """
    Interviewer that manages conversation flow.
    """
    
    def __init__(self, interview: Interview, thread_id: Optional[str] = None):
        self.checkpointer = InMemorySaver()

        self.config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        self.interview = interview

        # tool_id = 'openai:gpt-5'
        tool_id = 'openai:gpt-4.1'
        self.llm = init_chat_model(tool_id)

        # Define the tools used in the graph.
        tool_name = f'update_{self.interview._name()}'
        tool_desc = f'Record valid information stated by the {self.interview._bob_role_name()} about the {self.interview._name()}'

        # Each field will take a dict argument pertaining to it.
        tool_call_args_schema = {}

        # theAlice = self.interview._alice_role_name()
        theBob   = self.interview._bob_role_name()

        interview_field_names = self.interview._fields()
        for field_name in interview_field_names:
            print(f'Define field formal parameters: {field_name}')

            method = object.__getattribute__(self.interview, field_name)
            chatfield = getattr(method, '_chatfield', {})
            # specs = chatfield.get('specs', {})
            casts = chatfield.get('casts', {})

            casts_definitions = {}
            ok_primitive_types = dict(int=int, float=float, str=str, bool=bool)

            for cast_name, cast_info in casts.items():
                cast_type = cast_info['type']
                cast_type = ok_primitive_types.get(cast_type)
                if not cast_type:
                    raise ValueError(f'Cast {cast_name!r} bad type: {cast_info!r}; must be one of {ok_primitive_types.keys()}')

                cast_prompt = cast_info['prompt']
                cast_definition = (cast_type, Field(description=cast_prompt))
                casts_definitions[cast_name] = cast_definition

            conv_desc = (
                f'The conversational context leading up to the {theBob} providing the {field_name},'
                f' either as a brief summary prose, or else "N/A" if no context is relevant or helpful'
            )

            quote_desc = (
                f"A direct quote of the {theBob}'s exact words"
                # f' "within quotes like this",'
                f' and if necessary:'
                f' multiple paragraphs, elipses,'
                f' [clarifying square brackets], or [sic]'
            )

            field_docstring = method.__doc__ or method.__name__

            field_definition = create_model(
                field_name,
                # title = field_docstring,
                __doc__= field_docstring,

                # These are always defined and returned by the LLM.
                value                = (str, Field(title=f'Natural Value', description=f'The most typical valid representation of a {interview._name()} {field_name}')),
                conversation_context = (str, Field(title=f'Context about {interview._name()} {field_name}', description=conv_desc)),
                as_quote             = (str, Field(title=f'Direct {theBob} Quotation', description=quote_desc)),

                # These come in via decorators to cast the value in fun ways.
                **casts_definitions,
            )

            tool_call_args_schema[field_name] = Optional[field_definition]

        
        ToolArgs = create_model('ToolArgs',
            state        = Annotated[dict, InjectedState     ],
            tool_call_id = Annotated[str , InjectedToolCallId],
            **tool_call_args_schema,
        )

        # XXX
        # Maybe 1 tool for storing validated fields and a second tool for updates but it's not yet valid.

        @tool(tool_name, description=tool_desc, args_schema=ToolArgs)
        def tool_wrapper(state, tool_call_id, **kwargs):
            # print(f'tool_wrapper for id {tool_call_id}: {kwargs!r}')
            try:
                self.process_tool_input(state, **kwargs)
            except Exception as er:
                tool_msg = f'Error: {er!r}'
                # Also include the entire traceback in tool_msg.
                # tb.format_exception(None, e, e.__traceback__)
                # tool_msg += f'\n\n' + ''.join(traceback.format_exception(None, er, er.__traceback__))
                tool_msg += f'\n\n' + ''.join(traceback.format_exception(er))
            else:
                tool_msg = f'Success'

            tool_msg = ToolMessage(tool_msg, tool_call_id=tool_call_id)
            new_messages = state['messages'] + [tool_msg]
            new_interview = self._get_state_interview(state)
            state_update = { "messages": new_messages, "interview": new_interview }
            return Command(update=state_update)

        tools_avilable = [tool_wrapper]
        self.llm_with_tools = self.llm.bind_tools(tools_avilable)
        tool_node = ToolNode(tools=tools_avilable)

        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)
        builder.add_node('tools'     , tool_node)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')
        builder.add_edge             ('tools'     , 'think')

        self.graph = builder.compile(checkpointer=self.checkpointer)
        
    # This exists to fail faster in case if serialization bugs with the LangGraph checkpointer.
    # Hopefully it can go away.
    def _get_state_interview(self, state: State) -> Interview:
        interview = state.get('interview')
        if not isinstance(interview, Interview):
            raise ValueError(f'Expected state["interview"] to be an Interview instance, got {type(interview)}: {interview!r}')
        return interview

    def initialize(self, state:State) -> State:
        print(f'Initialize: {self._get_state_interview(state).__class__.__name__}')
        return state
        
    def think(self, state: State) -> State:
        print(f'Think: {self._get_state_interview(state).__class__.__name__}')
        
        if state['messages']:
            # I think ultimately the tools will be defined and the llm bound at this time.
            print(f'Messages already exist; continue conversation.')
            llm = self.llm_with_tools
        else:
            print(f'Start conversation in thread: {self.config["configurable"]["thread_id"]}')
            llm = self.llm

            system_prompt = self.mk_system_prompt(state)
            # print(f'----\n{system_msg.content}\n----')

            system_msg = SystemMessage(content=system_prompt)
            state['messages'].append(system_msg)

        # Tools are available by default, but they are omitted following a
        # system message, or following a "Success" tool response.
        llm = None
        latest_message = state['messages'][-1] if state['messages'] else None
        if isinstance(latest_message, SystemMessage):
            # print(f'No tools: Latest message is a system message.')
            llm = self.llm
        elif isinstance(latest_message, ToolMessage):
            if latest_message.content == 'Success':
                # print(f'No tools: Latest message is a tool response')
                llm = self.llm
        
        llm = llm or self.llm_with_tools

        llm_response_message = llm.invoke(state['messages'])
        # print(f'New message: {llm_response_message!r}')
        state['messages'].append(llm_response_message)

        return state
    
    def process_tool_input(self, state: State, **kwargs):
        """
        Process the tool input and update the interview state.
        """
        # print(f'Process tool input: {kwargs!r}')
        interview = self._get_state_interview(state)
        for field_name, llm_field_value in kwargs.items():
            if llm_field_value is None:
                continue

            all_values = llm_field_value.model_dump()
            print(f'LLM found a valid field: {field_name!r} = {all_values!r}')
            chatfield = interview._get_chat_field(field_name)
            if chatfield.get('value'):
                # print(f'{self.__class__.__name__}: Overwrite old field {field_name!r} value: {chatfield["value"]!r}')
                # TODO: This could do something sophisticated.
                pass
            chatfield['value'] = all_values

    def mk_system_prompt(self, state: State) -> str:
        interview = self._get_state_interview(state)
        # interview = self.interview._fromdict(interview)  # Reconstruct the interview object from the state

        collection_name = interview._name()

        fields = []
        for field_name in interview._fields():
            chatfield = interview._get_chat_field(field_name)
            desc = chatfield.get('desc')
            field_label = f'{field_name}'
            if desc:
                field_label += f': {desc}'

            specs = chatfield.get('specs', {})
            specs_prompts = []
            for spec_name, predicates in specs.items():
                for predicate in predicates:
                    specs_prompts.append(f'{spec_name.capitalize()}: {predicate}')
            
            casts = chatfield.get('casts', {})
            casts_prompts = []
            for cast_name, cast_info in casts.items():
                cast_prompt = cast_info.get('prompt')
                if cast_prompt:
                    casts_prompts.append(f'{cast_name.capitalize()}: {cast_prompt}')
            
            # Disable casts for the system prompt becauase they are required parameters for the tool call.
            casts_prompts = []

            field_specs = '\n'.join(f'    - {spec}' for spec in specs_prompts) + '\n' if specs_prompts else ''
            field_casts = '\n'.join(f'    - {cast}' for cast in casts_prompts) + '\n' if casts_prompts else ''

            field_prompt = (
                f'- {field_label}\n'
                f'{field_specs}'
                f'{field_casts}'
            )
            fields.append(field_prompt)
        fields = '\n'.join(fields)

        alice_traits = ''
        bob_traits = ''

        traits = interview._alice_role().get('traits', [])
        if traits:
            alice_traits = f'# Traits and Characteristics about the {interview._alice_role_name()}\n\n'
            # Maintain source-code order, since decorators apply bottom-up.
            alice_traits += '\n'.join(f'- {trait}' for trait in reversed(traits))

        traits = interview._bob_role().get('traits', [])
        if traits:
            bob_traits = f'# Traits and Characteristics about the {interview._bob_role_name()}\n\n'
            # Maintain source-code order, since decorators apply bottom-up.
            bob_traits += '\n'.join(f'- {trait}' for trait in reversed(traits))

        with_traits = f''
        if alice_traits or bob_traits:
            with_traits = f" Participants' characteristics and traits will be described below."
            
        alice_and_bob = ''
        if alice_traits or bob_traits:
            alice_and_bob = f'\n\n'
            alice_and_bob += alice_traits
            if alice_traits and bob_traits:
                alice_and_bob += '\n\n'
            alice_and_bob += bob_traits

        # TODO: Is it helpful at all to mention the tools in the system prompt?
        # tool_name = 'update_interview'
        # use_tools = (
        #     f' When you identify valid information to collect,'
        #     f' Use the {tool_name} tool, followed by a response to the {interview._bob_role_name()}.'
        # )
        use_tools = ''

        res = (
            f'You are a the conversational {interview._alice_role_name()} focused on gathering key information in conversation with the {interview._bob_role_name()},'
            f' into a collection called {collection_name}, detailed below.'
            f'{with_traits}'
            f' You begin the conversation in the most suitable way.'
            f'{use_tools}'
            f' Although the {interview._bob_role_name()} may take the conversation anywhere, your response must fit the conversation and your respective roles'
            f' while refocusing the discussion so that you can gather clear key {collection_name} information from the {interview._bob_role_name()}.'
            f'{alice_and_bob}'
            f'\n\n----\n\n'
            f'# Collection: {collection_name}\n'
            f'\n'
            f'{fields}\n'
        )
        return res
    
    def route_think(self, state: State) -> str:
        print(f'Route think edge: {self._get_state_interview(state).__class__.__name__}')

        result = tools_condition(dict(state))
        if result == 'tools':
            print(f'Route: to tools')
            return 'tools'

        interview = self._get_state_interview(state)
        if interview._done:
            print(f'Route: to end')
            return END

        return 'listen'
        
    def listen(self, state: State) -> State:
        print(f'Listen: {self._get_state_interview(state).__class__.__name__}')

        feedback = {'messages': state['messages']}
        # TODO: Make the LLM possibly set a prompt to the user.
        update = interrupt(feedback)

        print(f'Interrupt result: {update!r}')
        user_input = update["user_input"]
        user_msg = HumanMessage(content=user_input)
        state['messages'].append(user_msg)
        return state
        
    def go(self, user_input: Optional[str] = None):
        print(f'Go: User input: {user_input!r}')
        state = self.graph.get_state(config=self.config)

        if state.values and state.values['messages']:
            print(f'Continue conversation: {self.config["configurable"]["thread_id"]}')
            graph_input = Command(update={}, resume={'user_input': user_input})
        else:
            print(f'New conversation: {self.config["configurable"]["thread_id"]}')
            user_message = HumanMessage(content=user_input) if user_input else None
            user_messages = [user_message] if user_message else []
            graph_input = State(messages=user_messages, interview=self.interview)

        interrupts = []
        for event in self.graph.stream(graph_input, config=self.config):
            # print(f'ev> {event!r}')
            for value in event.values():
                # print("Assistant:", value["messages"][-1].content)
                # print(f'  >> {type(value)} {value!r}')
                for obj in value:
                    # print(f'    >> {type(obj)} {obj!r}')
                    if isinstance(obj, Interrupt):
                        # Do I need to keep a reference to this Interrupt or its ID?
                        interrupts.append(obj.value)
        
        if not interrupts:
            return None
        
        if len(interrupts) > 1:
            # TODO: I think this can happen? Because of parallel execution?
            print(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')
            raise Exception(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')

        return interrupts[0]