"""LangGraph-based evaluator for Chatfield conversations."""

import re
import uuid
import traceback

from pydantic import BaseModel, Field, conset, create_model
from deepdiff import DeepDiff, extract

from typing import Annotated, Any, Dict, Optional, TypedDict, List, Literal, Set
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt, Interrupt
from langgraph.prebuilt import ToolNode, tools_condition, InjectedState
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

# from mcp import Tool


from .interview import Interview

def merge_interviews(a:Interview, b:Interview) -> Interview:
    """
    LangGraph reducer for Interview objects. It merges any defined values.
    """
    result = None

    a_type = type(a)
    b_type = type(b)
    a_subclass = isinstance(a, b_type) and a_type is not b_type
    b_subclass = isinstance(b, a_type) and a_type is not b_type

    if a_subclass:
        # print(f'Reduce to subclass: {a!r}')
        result = a
    elif b_subclass:
        # print(f'Reduce to subclass: {b!r}')
        result = b
    elif a_type is not b_type:
        # TODO: I think this logic will change if/when changing the model in-flight works.
        raise NotImplementedError(f'Cannot reduce {a_type!r} and {b_type!r}')
    else:
        # a and b are the same type.
        # For some reason I see them coming in reversed.
        # left, right = a, b
        left, right = b, a

        diff = DeepDiff(left._chatfield, right._chatfield, ignore_order=True)
        if not diff:
            # print(f'Identical instances: {a_type} and {b_type}')
            result = a    
        else:
            type_changes = diff.get('type_changes')
            if not type_changes:
                raise NotImplementedError(f'Cannot reduce {a_type!r} with non-type changes: {diff}')
            
            # Accumulate everything into a in order to return it.
            result = a    

            print(f'===========')
            print(f'Reduce:')
            print(f'  a: {type(a)} {a!r}')
            print(f'  b: {type(b)} {b!r}')
            for key_path, delta in type_changes.items():
                if delta['old_value'] is None and delta['new_value'] is not None:
                    # print(f'  Field already present {key_path}: {extract(a._chatfield, key_path)}')
                    pass
                else:
                    raise NotImplementedError(f'Cannot reduce {a_type!r} with type changes: {diff}')
            
            if len(diff) != 1:
                raise NotImplementedError(f'Cannot reduce {a_type!r} with non-type changes: {diff}')

    if result is None:
        raise Exception(f'XXX')
    return result

class State(TypedDict):
    messages: Annotated[List[Any] , add_messages    ]
    interview: Annotated[Interview, merge_interviews]


class Interviewer:
    """
    Interviewer that manages conversation flow.
    """
    
    def __init__(self, interview: Interview, thread_id: Optional[str] = None):
        self.checkpointer = InMemorySaver()

        self.config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        self.interview = interview
        theAlice = self.interview._alice_role_name()
        theBob   = self.interview._bob_role_name()

        # tool_id = 'openai:o3-mini'
        # temperature = None
        tool_id = 'openai:gpt-5'
        temperature = 0.0
        self.llm = init_chat_model(tool_id, temperature=temperature)

        # Define the tools used in the graph.
        tool_name = f'update_{self.interview._name()}'
        tool_desc = (
            f'Record valid information stated by the {theBob}'
            f' about the {self.interview._name()}'
            # f'. Always call this tool with at most one field at a time, and the others all null.'
            # f' To record multiple fields, call this tool multiple times.'
        )

        # Each field will take a dict argument pertaining to it.
        tool_call_args_schema = {}

        interview_field_names = self.interview._fields()
        for field_name in interview_field_names:
            print(f'Define field formal parameters: {field_name}')

            method = object.__getattribute__(self.interview, field_name)
            chatfield = getattr(method, '_chatfield', {})
            # specs = chatfield.get('specs', {})
            casts = chatfield.get('casts', {})

            casts_definitions = {}
            ok_primitive_types = {
                'int': int,
                'float': float,
                'str': str,
                'bool': bool,
                'list': List[Any],
                'set': set,
                'dict': Dict[str, Any],
                'choice': 'choice',
            }

            for cast_name, cast_info in casts.items():
                cast_type = cast_info['type']
                cast_type = ok_primitive_types.get(cast_type)
                if not cast_type:
                    raise ValueError(f'Cast {cast_name!r} bad type: {cast_info!r}; must be one of {ok_primitive_types.keys()}')

                cast_title = None # cast_info.get('title', f'{cast_name} value')
                cast_prompt = cast_info['prompt']

                if cast_type == 'choice':
                    # TODO: Unclear if this name shortening helps:
                    cast_short_name = re.sub(r'^choose_.*_', '', cast_name)
                    cast_prompt = cast_prompt.format(name=cast_short_name)

                    # First start with all the choices.
                    choices = tuple(cast_info['choices'])
                    min_results = 1
                    max_results = 1

                    if cast_info['null']:
                        min_results = 0

                    cast_type = Literal[choices]  # type: ignore

                    if cast_info['multi']:
                        # cast_type = Set[cast_type]
                        max_results = len(choices)
                        cast_type = conset(item_type=cast_type, min_length=min_results, max_length=max_results)

                    if cast_info['null']:
                        cast_type = Optional[cast_type]

                cast_definition = (cast_type, Field(description=cast_prompt, title=cast_title))
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
                value    = (str, Field(title=f'Natural Value', description=f'The most typical valid representation of a {interview._name()} {field_name}')),
                context  = (str, Field(title=f'Context about {interview._name()} {field_name}', description=conv_desc)),
                as_quote = (str, Field(title=f'Directly quote {theBob}', description=quote_desc)),

                # These come in via decorators to cast the value in fun ways.
                **casts_definitions,
            )

            tool_call_args_schema[field_name] = Optional[field_definition]

        
        ToolArgs = create_model('ToolArgs',
            state        = Annotated[dict, InjectedState     ],
            tool_call_id = Annotated[str , InjectedToolCallId],
            **tool_call_args_schema,
        )

        # TODO: Probably need more tools:
        # - updates worth saving but it's not yet valid.
        # - Something to re-zero the field (if the above cannot do it)

        @tool(tool_name, description=tool_desc, args_schema=ToolArgs)
        def tool_wrapper(state, tool_call_id, **kwargs):
            # print(f'tool_wrapper for id {tool_call_id}: {kwargs!r}')
            interview = self._get_state_interview(state)

            pre_interview_model = interview.model_dump()

            try:
                self.process_tool_input(interview, **kwargs)
            except Exception as er:
                tool_msg = f'Error: {er!r}'
                tool_msg += f'\n\n' + ''.join(traceback.format_exception(er))
            else:
                tool_msg = f'Success'

            post_interview_model = interview.model_dump()

            # Prepare the return value, including needed state updates.
            state_update = {}

            # Append a ToolMessage indicating a completed run by tool_call_id.
            tool_msg = ToolMessage(tool_msg, tool_call_id=tool_call_id)
            state_update["messages"] = [tool_msg]

            # Specify an interview object if anything changed.
            data_diff = DeepDiff(pre_interview_model, post_interview_model, ignore_order=True)
            if data_diff:
                # type_diff = data_diff.get('type_changes')
                # vals_diff = data_diff.get('values_changed')
                # if type_diff:
                #     print(f'Keys with changed type: {len(type_diff.keys())}: {", ".join(type_diff.keys())}')
                # if vals_diff:
                #     print(f'Keys with changed values: {len(vals_diff.keys())}: {", ".join(vals_diff.keys())}')
                state_update["interview"] = interview

            return Command(update=state_update)

        tools_avilable = [tool_wrapper]
        self.llm_with_tools = self.llm.bind_tools(tools_avilable)
        tool_node = ToolNode(tools=tools_avilable)

        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)
        builder.add_node('tools'     , tool_node)
        builder.add_node('teardown'  , self.teardown)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_think)
        builder.add_edge             ('listen'    , 'think')
        builder.add_edge             ('tools'     , 'think')
        builder.add_edge             ('teardown'  , END    )

        self.graph = builder.compile(checkpointer=self.checkpointer)
        
    # This exists to fail faster in case if serialization bugs with the LangGraph checkpointer.
    # Hopefully it can go away.
    def _get_state_interview(self, state: State) -> Interview:
        interview = state.get('interview')
        if not isinstance(interview, Interview):
            raise ValueError(f'Expected state["interview"] to be an Interview instance, got {type(interview)}: {interview!r}')
        return interview

    # Node
    def initialize(self, state:State):
        # print(f'Initialize> {self._get_state_interview(state).__class__.__name__}')
        print(f'Initialize> {self._get_state_interview(state)!r}')
        return None
        
    # Node
    def think(self, state: State):
        print(f'Think: {self._get_state_interview(state).__class__.__name__}')
        
        # Track net-new messages. Its reducer will merge them.
        new_messages = []

        # `llm` controls which tools are available/bound to the LLM.
        # The LLMs are previously bound, so this references whichever is needed.
        #
        # By default, the tools are available. But they are omitted following a
        # system message, or following a "Success" tool response. This
        # encourages the LLM to respond with an AIMessage.
        llm = None

        if not state['messages']:
            print(f'Start conversation in thread: {self.config["configurable"]["thread_id"]}')
            system_prompt = self.mk_system_prompt(state)
            system_msg = SystemMessage(content=system_prompt)
            new_messages.append(system_msg)

        latest_message = new_messages[-1] if new_messages else None
        if isinstance(latest_message, SystemMessage):
            # print(f'No tools: Latest message is a system message.')
            llm = self.llm
        elif isinstance(latest_message, ToolMessage):
            if latest_message.content == 'Success':
                # print(f'No tools: Latest message is a tool response')
                llm = self.llm
        
        llm = llm or self.llm_with_tools

        # Note, the reducer will merge these properly in the state. For now, append them for presentation to the LLM.
        all_messages = state['messages'] + new_messages

        llm_response_message = llm.invoke(all_messages)
        # print(f'New message: {llm_response_message!r}')
        new_messages.append(llm_response_message)

        return {'messages':new_messages}
    
    # def process_tool_input(self, state: State, **kwargs):
    def process_tool_input(self, interview: Interview, **kwargs):
        """
        Move any LLM-provided field values into the interview state.
        """
        defined_args = [X for X in kwargs if kwargs[X] is not None]
        print(f'Tool input for {len(defined_args)} fields: {", ".join(defined_args)}')
        for field_name, llm_field_value in kwargs.items():
            if llm_field_value is None:
                continue

            llm_values = llm_field_value.model_dump()
            print(f'LLM found a valid field: {field_name!r} = {llm_values!r}')
            chatfield = interview._get_chat_field(field_name)
            if chatfield.get('value'):
                # print(f'{self.__class__.__name__}: Overwrite old field {field_name!r} value: {chatfield["value"]!r}')
                # TODO: This could do something sophisticated.
                pass

            all_values = {}
            for key, val in llm_values.items():
                key = re.sub(r'^choose_exactly_one_' , 'as_one_'  , key)
                key = re.sub(r'^choose_zero_or_one_' , 'as_maybe_', key)
                key = re.sub(r'^choose_one_or_more_' , 'as_multi_', key)
                key = re.sub(r'^choose_zero_or_more_', 'as_any_'  , key)
                all_values[key] = val
            chatfield['value'] = all_values

    def mk_system_prompt(self, state: State) -> str:
        # XXX TODO: There is a bug pulling the roles, probably because of the new ._chatfield dict.
        interview = self._get_state_interview(state)
        # interview = self.interview._fromdict(interview)  # Reconstruct the interview object from the state

        collection_name = interview._name()

        field_keys = interview._chatfield['fields'].keys()
        field_keys = reversed(field_keys)  # Reverse the order to maintain source-code order.

        fields = []
        for field_name in field_keys:
            chatfield = interview._chatfield['fields'][field_name]

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
        use_tools = (
            f' Use tools to record information fields'
            f' and their related "casts",'
            f' which are cusom conversions you provide for each field.'
        #     f' When you identify valid information to collect,'
        #     f' Use the {tool_name} tool, followed by a response to the {interview._bob_role_name()}.'
        )
        # use_tools = ''

        res = (
            f'You are the conversational {interview._alice_role_name()} focused on gathering key information in conversation with the {interview._bob_role_name()},'
            f' into a collection called {collection_name}, detailed below.'
            f'{with_traits}'
            # f' You begin the conversation in the most suitable way.'
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
            # print(f'Route: to tools')
            return 'tools'

        interview = self._get_state_interview(state)
        if interview._done:
            print(f'Route: to teardown')
            return 'teardown'

        return 'listen'
    
    # Node
    def teardown(self, state: State):
        # Ending will cause a return back to .go() caller.
        # That caller will expect the original interview object to reflect the conversation.
        interview = self._get_state_interview(state)
        print(f'Teardown: {interview._name()}')
        self.interview._copy_from(interview)
        
    def listen(self, state: State):
        interview = self._get_state_interview(state)
        print(f'Listen: {interview.__class__.__name__}')

        # The interrupt will cause a return back to .go() caller.
        # That caller will expect the original interview object to reflect the conversation.
        # So, for now just copy over the _chatfield dict.
        self.interview._copy_from(interview)

        feedback = {'messages': state['messages']}
        # TODO: Make the LLM possibly set a prompt to the user.
        update = interrupt(feedback)

        print(f'Interrupt result: {update!r}')
        user_input = update["user_input"]
        user_msg = HumanMessage(content=user_input)
        return {'messages': [user_msg]}
        
    def go(self, user_input: Optional[str] = None) -> Optional[str]:
        """
        Process one conversation turn.
        
        Args:
            user_input: The user's input message (or None to start/continue)
            
        Returns:
            The content of the latest AI message as a string, or None if conversation is complete
        """
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
            # The event is a dict mapping node name to node output.
            # print(f'ev> {event!r}')
            for node_name, state_delta in event.items():
                # print(f'Node {node_name!r} emitted: {state_delta!r}')
                if isinstance(state_delta, tuple):
                    if isinstance(state_delta[0], Interrupt):
                        interrupts.append(state_delta[0].value)

        if not interrupts:
            # TODO: What is the logic? I think never return None right?
            return None
        
        if len(interrupts) > 1:
            # TODO: I think this can happen? Because of parallel execution?
            print(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')
            raise Exception(f'XXX Hey there, I got multiple interrupts: {interrupts!r}')

        return interrupts[0]