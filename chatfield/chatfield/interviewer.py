"""LangGraph-based evaluator for Chatfield conversations."""

import re
import uuid
import traceback

from pydantic import BaseModel, Field, conset, create_model
from deepdiff import DeepDiff, extract

from typing import Annotated, Any, Dict, Optional, TypedDict, List, Literal, Set
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
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
        return a
    if b_subclass:
        # print(f'Reduce to subclass: {b!r}')
        return b
    if a_type is not b_type:
        # TODO: I think this logic will change if/when changing the model in-flight works.
        raise NotImplementedError(f'Cannot reduce {a_type!r} and {b_type!r}')

    # a and b are the same type. Diff them to see what changed.
    left, right = a, b
    diff = DeepDiff(left._chatfield, right._chatfield, ignore_order=True)
    if not diff:
        # print(f'Identical instances: {a_type} and {b_type}')
        return a

    # Accumulate everything into the result in order to return it.
    # print(f'Reduce:')
    # print(f'  a: {type(a)} {a!r}')
    # print(f'  b: {type(b)} {b!r}')

    # TODO: Assume B has all the latest information. If LangGraph does not guarantee
    # any ordering, then this a bug which would trigger if they arrive differently from my testing.
    result = b

    type_changes = diff.pop('type_changes') if 'type_changes' in diff else {}
    for key_path, delta in type_changes.items():
        if delta['old_value'] is None and delta['new_value'] is not None:
            # print(f'  Field changing to non-None {key_path}: {extract(result._chatfield, key_path)}')
            pass
        else:
            raise NotImplementedError(f'Cannot reduce {a_type!r} with type changes: {diff}')

    values_changed = diff.pop('values_changed') if 'values_changed' in diff else {}
    for key_path, delta in values_changed.items():
        if delta['old_value'] is None and delta['new_value'] is not None:
            # print(f'  Field changing to non-None {key_path}: {extract(result._chatfield, key_path)}')
            pass
        elif (not delta['old_value']) and delta['new_value']:
            # print(f'  Field changing falsy to truthy {key_path}: {extract(result._chatfield, key_path)}')
            pass
        elif key_path == "root['roles']['alice']['type']" and delta['old_value'] == 'Agent':
            # print(f'  Field changing from default value {key_path}: {extract(result._chatfield, key_path)}')
            pass
        elif key_path == "root['roles']['bob']['type']" and delta['old_value'] == 'User':
            # print(f'  Field changing from default value {key_path}: {extract(result._chatfield, key_path)}')
            pass
        else:
            raise NotImplementedError(f'Cannot reduce {a_type!r} with value changes: {diff}')

    dict_added = diff.pop('dictionary_item_added') if 'dictionary_item_added' in diff else set()
    if dict_added:
        pass # All adds are fine.

    iterable_added = diff.pop('iterable_item_added') if 'iterable_item_added' in diff else set()
    if iterable_added:
        pass # All adds are fine.
    
    if diff:
        raise NotImplementedError(f'Cannot reduce {a_type!r} with non-type changes: {diff}')

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
        # tool_id = 'openai:gpt-5'
        tool_id = 'openai:gpt-4.1'
        temperature = 0.0
        self.llm = init_chat_model(tool_id, temperature=temperature)

        # Define the tools used in the graph.
        # The schema maps field names to its input type, in this case a dict with all the casts, etc.
        tool_call_args_schema = {}
        conclude_args_schema = {}

        interview_field_names = self.interview._fields()
        for field_name in interview_field_names:
            # print(f'Define field formal parameters: {field_name}')

            # Get field metadata directly from _chatfield for builder-created interviews
            field_metadata = self.interview._chatfield['fields'][field_name]
            is_conclude = field_metadata['specs']['conclude']

            casts = field_metadata['casts']
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

            field_definition = create_model(
                field_name,
                # title = field_docstring,
                __doc__= field_metadata.get('desc', field_name),

                # These are always defined and returned by the LLM.
                # TODO: I think only value should be here. The others should move to the other casts.
                value    = (str, Field(title=f'Natural Value', description=f'The most typical valid representation of a {interview._name()} {field_name}')),
                # context  = (str, Field(title=f'Context about {interview._name()} {field_name}', description=conv_desc)),
                # as_quote = (str, Field(title=f'Directly quote {theBob}', description=quote_desc)),

                # These come in via decorators to cast the value in fun ways.
                **casts_definitions,
            )

            if is_conclude:
                conclude_args_schema[field_name] = field_definition # Mandatory
            else:
                tool_call_args_schema[field_name] = Optional[field_definition] # Optional

        # TODO: Probably need more tools:
        # - updates worth saving but it's not yet valid.
        # - Something to re-zero the field (if the above cannot do it)

        #
        # Update Tool
        #

        tool_name = f'update_{self.interview._id()}'
        tool_desc = (
            f'Record valid information shared by the {theBob}'
            f' about the {self.interview._name()}'
            # f'. Always call this tool with at most one field at a time, and the others all null.'
            # f' To record multiple fields, call this tool multiple times.'
        )

        UpdateToolArgs = create_model('UpdateToolArgs',
            state        = Annotated[dict, InjectedState     ],
            tool_call_id = Annotated[str , InjectedToolCallId],
            **tool_call_args_schema,
        )

        @tool(tool_name, description=tool_desc, args_schema=UpdateToolArgs)
        def update_wrapper(state, tool_call_id, **kwargs):
            return self.run_tool(state, tool_call_id, **kwargs)

        #
        # Conclude Tool
        #

        tool_name = f'conclude_{self.interview._id()}'
        tool_desc = (
            f'Record key required information'
            f' about the {self.interview._name()}'
            f' by summarizing, synthesizing, or recalling'
            f' the conversation so far with the {theBob}'
        )
        ConcludeToolArgs = create_model('ConcludeToolArgs',
            state        = Annotated[dict, InjectedState     ],
            tool_call_id = Annotated[str , InjectedToolCallId],
            **conclude_args_schema,
        )

        @tool(tool_name, description=tool_desc, args_schema=ConcludeToolArgs)
        def conclude_wrappr(state, tool_call_id, **kwargs):
            return self.run_tool(state, tool_call_id, **kwargs)

        self.llm_with_update = self.llm.bind_tools([update_wrapper])
        self.llm_with_conclude = self.llm.bind_tools([conclude_wrappr])
        self.llm_with_both = self.llm.bind_tools([update_wrapper, conclude_wrappr])

        tool_node = ToolNode(tools=[update_wrapper, conclude_wrappr])

        builder = StateGraph(State)

        builder.add_node('initialize', self.initialize)
        builder.add_node('think'     , self.think)
        builder.add_node('listen'    , self.listen)
        builder.add_node('tools'     , tool_node)
        builder.add_node('digest'    , self.digest)
        builder.add_node('teardown'  , self.teardown)

        builder.add_edge             (START       , 'initialize')
        builder.add_edge             ('initialize', 'think')
        builder.add_conditional_edges('think'     , self.route_from_think)
        builder.add_edge             ('listen'    , 'think')
        builder.add_conditional_edges('tools'     , self.route_from_tools, ['think', 'digest'])
        builder.add_conditional_edges('digest'    , self.route_from_digest, ['tools', 'think'])
        builder.add_edge             ('teardown'  , END    )

        self.graph = builder.compile(checkpointer=self.checkpointer)
        
    # This exists to fail faster in case of serialization bugs with the LangGraph checkpointer.
    # Hopefully it can go away.
    def _get_state_interview(self, state: State) -> Interview:
        interview = state.get('interview')
        if not isinstance(interview, Interview):
            raise ValueError(f'Expected state["interview"] to be an Interview instance, got {type(interview)}: {interview!r}')
        
        if not interview._chatfield['fields']:
            # No fields defined is okay only for a totally-null, uninitialized interview object.
            # This happens normally in early state, before the initialize node.
            # TODO: For now, instead of exhaustively checking for "not-initialized-ness", I will do some quick duck typing.
            if interview._chatfield['type'] is None and interview._chatfield['desc'] is None:
                # print(f'Interview is uninitialized, which is okay: {interview!r}')
                pass
            else:
                raise Exception(f'Expected state["interview"] to have fields, got empty: {interview!r}')
        return interview

    # Node
    def initialize(self, state:State):
        print(f'Initialize> {self._get_state_interview(state).__class__.__name__}')
        
        # Currently there is an empty/null Interview object in the state. Populate that with the real one.
        return {'interview': self.interview}
    
    # Node
    def run_tool(self, state: State, tool_call_id: str, **kwargs) -> Command:
        print(f'Tool> {tool_call_id}> {kwargs!r}')

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
            state_update["interview"] = interview

        return Command(update=state_update)

    # Node
    def digest(self, state: State):
        interview = self._get_state_interview(state)
        print(f'Digest> {interview._name()}')

        # First digest undefined confidential fields. Then digest the conclude fields.
        for field_name, chatfield in interview._chatfield['fields'].items():
            if not chatfield['specs']['conclude']:
                if chatfield['specs']['confidential']:
                    if not chatfield['value']:
                        return self.digest_confidential(state)
        return self.digest_conclude(state)
    
    def digest_confidential(self, state: State):
        interview = self._get_state_interview(state)
        print(f'Digest Confidential> {interview._name()}')

        fields_prompt = []
        field_definitions = {}
        for field_name, chatfield in interview._chatfield['fields'].items():
            if chatfield['specs']['conclude']:
                continue

            if chatfield['specs']['confidential'] and not chatfield['value']:
                # This confidential field must be marked "N/A".
                fields_prompt.append(f'- {field_name}: {chatfield["desc"]}')
                field_definition = self.mk_field_definition(interview, field_name, chatfield)
            else:
                # Force the LLM to pass null for values we don't need.
                field_definition = (Literal[None], Field(title=f'Must be null', description=f'must be null'))

            field_definitions[field_name] = field_definition

        fields_prompt = '\n'.join(fields_prompt)

        # Build a special llm object bound to a speicial tool which explicitly requires the proper arguments.
        # Make it call the a compatible tool name.
        tool_name = f'update_{interview._id()}'
        tool_desc = (
            f'Record those confidential fields about the {interview._name()}'
            f' from the {interview._bob_role_name()}'
            f' which have no relevent information so far.'
        )

        ConfidentialToolArgs = create_model('ConfidentialToolArgs',
            state        = Annotated[dict, InjectedState     ],
            tool_call_id = Annotated[str , InjectedToolCallId],
            **field_definitions,
        )

        @tool(tool_name, description=tool_desc, args_schema=ConfidentialToolArgs)
        def confidential_wrapper(state, tool_call_id, **kwargs):
            # Note, I think this wrapper never actually runs. The real update wrapper runs.
            # But, the LLM does use the correct arguments defined in this code.
            return self.run_tool(state, tool_call_id, **kwargs)

        llm = self.llm.bind_tools([confidential_wrapper])

        sys_msg = SystemMessage(content=(
            # f'You have successfully gathered enough information to'
            f'You must now'
            f' update and populate the not-yet-defined confidential fields, listed below to remind you.'
            f' Use the update tool call to indicate there is no relevant information'
            f' for the fields.'
            f'\n\n'
            f'## Confidential Fields needed for {interview._name()}\n'
            f'\n'
            f'{fields_prompt}'
        ))

        all_messages = state['messages'] + [sys_msg]
        llm_response_message = llm.invoke(all_messages)
        # print(f'New LLM response message: {llm_response_message!r}')

        # LangGraph wants only net-new messages. Its reducer will merge them.
        new_messages = [sys_msg] + [llm_response_message]
        return {'messages':new_messages}
    
    def mk_field_definition(self, interview:Interview, field_name: str, chatfield: Dict[str, Any]):
        casts_definitions = self.mk_casts_definitions(chatfield)
        field_definition = create_model(
            field_name,
            __doc__= chatfield['desc'],
            value  = (str, Field(title=f'Natural Value', description=f'The most typical valid representation of a {interview._name()} {field_name}')),
            **casts_definitions,
        )
        return field_definition
    
    def mk_casts_definitions(self, chatfield): # field_name:str, chatfield:Dict[str, Any]):
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

        casts = chatfield['casts']
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

        return casts_definitions

    def digest_conclude(self, state: State):
        interview = self._get_state_interview(state)
        print(f'Digest Conclude> {interview._name()}')

        llm = self.llm_with_conclude
        fields_prompt = self.mk_fields_prompt(interview, mode='conclude')
        sys_msg = SystemMessage(content=(
            f'You have successfully gathered enough information'
            f' to draw conclusions and record key information from this conversation.'
            f' You must now record all conclusion fields, defined below.'
            f'\n\n'
            f'## Conclusion Fields needed for {interview._name()}\n'
            f'\n'
            f'{fields_prompt}'
        ))

        all_messages = state['messages'] + [sys_msg]
        llm_response_message = llm.invoke(all_messages)
        # print(f'New LLM response message: {llm_response_message!r}')

        # LangGraph wants only net-new messages. Its reducer will merge them.
        new_messages = [sys_msg] + [llm_response_message]
        return {'messages':new_messages}

    # Node
    def think(self, state: State):
        print(f'Think> {self._get_state_interview(state).__class__.__name__}')

        # Track any system messages that need to be added.
        new_system_message = None

        #
        # System Messages
        #

        prior_system_messages = [msg for msg in state['messages'] if isinstance(msg, SystemMessage)]
        if len(prior_system_messages) == 0:
            print(f'Start conversation in thread: {self.config["configurable"]["thread_id"]}')
            system_prompt = self.mk_system_prompt(state)
            new_system_message = SystemMessage(content=system_prompt)

        #
        # LLM Tool Optimizations
        #

        # `llm` controls which tools are available/bound to the LLM.
        # The LLMs are previously bound, so this references whichever is needed.
        #
        # By default, the tools are available. But they are omitted following a
        # system message, or following a "Success" tool response. This
        # encourages the LLM to respond with an AIMessage.
        llm = None
        latest_message = state['messages'][-1] if state['messages'] else None

        if isinstance(latest_message, SystemMessage):
            # print(f'No tools: Latest message is a system message.')
            llm = self.llm
        elif isinstance(latest_message, ToolMessage):
            if latest_message.content == 'Success':
                # print(f'No tools: Latest message is a tool response')
                llm = self.llm
        
        llm = llm or self.llm_with_update

        #
        # Call the LLM
        #

        if new_system_message:
            if prior_system_messages:
                raise NotImplementedError(f'Cannot handle multiple system messages yet: {prior_system_messages!r}')

        # Although the reducer only wants net-new messages, the LLM wants the full conversation.
        new_system_messages = [new_system_message] if new_system_message else []
        all_messages = new_system_messages + state['messages']
        llm_response_message = llm.invoke(all_messages)
        # print(f'New LLM response message: {llm_response_message!r}')

        #
        # Return to LangGraph
        #
        
        # LangGraph wants only net-new messages. Its reducer will merge them.
        # TODO: I do not know if anything else needs to be done to place the system message before the others.
        new_messages = new_system_messages + [llm_response_message]
        new_messages.append(llm_response_message)
        return {'messages':new_messages}
    
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
        interview = self._get_state_interview(state)
        collection_name = interview._name()
        fields_prompt = self.mk_fields_prompt(interview)

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
            # f' into a collection called {collection_name},'
            f' detailed below.'
            f'{with_traits}'
            # f' You begin the conversation in the most suitable way.'
            f'{use_tools}'
            f' Although the {interview._bob_role_name()} may take the conversation anywhere, your response must fit the conversation and your respective roles'
            f' while refocusing the discussion so that you can gather clear key {collection_name} information from the {interview._bob_role_name()}.'
            f'{alice_and_bob}'
            f'\n\n----\n\n'
            f'# Collection: {collection_name}\n'
            f'\n'
            f'## Description\n'
            f'{interview._chatfield["desc"]}'
            f'\n\n'
            f'## Fields to Collect\n'
            f'\n'
            f'{fields_prompt}\n'
        )
        return res

    def mk_fields_prompt(self, interview: Interview, mode='normal', field_names=None) -> str:
        if mode not in ('normal', 'conclude'):
            raise ValueError(f'Bad mode: {mode!r}; must be "normal" or "conclude"')

        fields = [] # Note, this should always be in source-code order.

        field_keys = field_names or interview._chatfield['fields'].keys()
        for field_name in field_keys:
            chatfield = interview._chatfield['fields'][field_name]

            if mode == 'normal' and chatfield['specs']['conclude']:
                # print(f'Skip conclude field for normal prompt: {field_name!r}')
                continue
        
            if mode == 'conclude' and not chatfield['specs']['conclude']:
                # print(f'Skip normal field for conclude prompt: {field_name!r}')
                continue

            desc = chatfield.get('desc')
            field_label = f'{field_name}'
            if desc:
                field_label += f': {desc}'

            # TODO: I think confidential and conclude should be their own thing, not specs.
            specs = chatfield['specs']
            specs_prompts = []

            if specs['confidential']:
                specs_prompts.append(
                    f'**Confidential**:'
                    f' Do not inquire about this explicitly nor bring it up yourself. Continue your normal behavior.'
                    f' However, if the {interview._bob_role_name()} ever volunteers or implies it, you must record this information.'
                )

            for spec_name, predicates in specs.items():
                if spec_name not in ('confidential', 'conclude'):
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
        return fields
    
    def route_from_think(self, state: State) -> str:
        print(f'Route from think: {self._get_state_interview(state).__class__.__name__}')

        result = tools_condition(dict(state))
        if result == 'tools':
            # print(f'Route: to tools')
            return 'tools'

        interview = self._get_state_interview(state)
        if interview._done:
            # print(f'Route: to teardown')
            return 'teardown'
        
        # Either digest once, the first time _enough becomes true.
        # Or, digest after every subsequent user message. For now, do the former
        # because then _done would evaluate true, so the above return would trigger.
        if interview._enough:
            # TODO: I wonder if this is needed anymore? Does digest happen differently in the graph now?
            print(f'Route: think -> digest')
            return 'digest'

        return 'listen'
    
    def route_from_tools(self, state: State) -> str:
        interview = self._get_state_interview(state)
        print(f'Route from tools: {interview._name()}')

        if interview._enough and not interview._done:
            print(f'Route: tools -> digest')
            return 'digest'

        return 'think'
    
    def route_from_digest(self, state: State) -> str:
        interview = self._get_state_interview(state)
        print(f'Route from digest: {interview._name()}')

        result = tools_condition(dict(state))
        if result == 'tools':
            print(f'Route: digest -> tools')
            return 'tools'

        return 'think'
    
    # Node
    def teardown(self, state: State):
        # Ending will cause a return back to .go() caller.
        # That caller will expect the original interview object to reflect the conversation.
        interview = self._get_state_interview(state)
        print(f'Teardown> {interview._name()}')
        self.interview._copy_from(interview)
        
    # Node
    def listen(self, state: State):
        interview = self._get_state_interview(state)
        print(f'Listen> {interview.__class__.__name__}')

        # The interrupt will cause a return back to .go() caller.
        # That caller will expect the original interview object to reflect the conversation.
        # So, for now just copy over the _chatfield dict.
        self.interview._copy_from(interview)

        msg = state['messages'][-1] if state['messages'] else None
        if not isinstance(msg, AIMessage):
            raise ValueError(f'Expected last message to be an AIMessage, got {type(msg)}: {msg!r}')

        # TODO: Make the LLM possibly set a prompt to the user.
        feedback = msg.content.strip()
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
            graph_input = State(messages=user_messages)

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
            print(f'WARN: Return None, probably should generate a message anyway')
            return None
        
        if len(interrupts) > 1:
            # TODO: I think this can happen? Because of parallel execution?
            raise Exception(f'Unexpected scenario multiple interrupts: {interrupts!r}')

        return interrupts[0]