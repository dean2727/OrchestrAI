# agents/base_agent.py
from abc import ABC, abstractmethod
from typing import List, Dict
from schemas.orchestrator_schema import AgentTemplateVarInstruction

class BaseAgent(ABC):
    """
    Base class for metadata and LangGraph-specific implementation for the AI agents 
    in the recurring OrchestrAI AI jobs. Each job (Kubernetes cronjob) has a 
    dynamic agent flow, depending on user query. The LangGraph code defined by 
    each agent is to be inserted into a workflow template that the cronjob will 
    then run off of.
    """

    # These are template variables that inform prompt templates for the agent,
    # mapping the variable to a set of instructions to the LLM on how to determine 
    # the given template variable, for a give AI job/user query (it's prompting for prompts)
    # (May be empty for some agents, like simple text notifications)
    template_var_instructions = {}
    # These are the LangGraph State attributes (mappings of strings to its respective 
    # data type) this agent is responsible for setting after its node's execution in the graph
    # (May be empty for some agents, like simple text notifications)
    state_vars_set = {}

    def __init__(self):
        self.ai_generated_template_vars: List[AgentTemplateVarInstruction] = []

    @property
    def description(self) -> str:
        """Return a short description of what this agent does."""
        pass

    @property
    def node_name(self) -> str:
        """Return the node variable name - to be used in certain parts of the AI 
        job template, such as graph.add_node() or graph.add_edge()"""
        return self.__class__.__name__.lower()  # Automatically generate based on class name
    
    @property
    def graph_state_attributes(self) -> List[str]:
        """Return the LangGraph State attributes this agent would add to the graph, if it were used"""
        return list(self.ai_generated_template_vars.keys())

    @abstractmethod
    def get_graph_node_code(self) -> str:
        """
        Defines the LangGraph code (prompt, tool, agent, and node definition) 
        pertaining to this agent, to be injected into AI job (jinja) template
        """
        pass