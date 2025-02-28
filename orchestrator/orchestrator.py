from agents import *
from jinja2 import Template
from openai import OpenAI
import os
from agents import AGENT_DESCRIPTIONS, AGENT_REGISTRY
from schemas.orchestrator_schema import *
from kubernetes import client
from typing import List, Any, Dict

# String template (langgraph python script) which each AI cronjob will be based off of
workflow_template = """
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import TypedDict
import os
from langgraph.graph import START, END, StateGraph
from langchain.agents import initialize_agent

{{ STATE }}

graph = StateGraph(State)

{% for code_block in NODE_CODE_BLOCKS %}
{{ code_block }}
{% endfor %}

{% for node in NODES %}
{{ node }}
{% endfor %}

{% for edge in EDGES %}
{{ edge }}
{% endfor %}

compiled_graph = graph.compile()

if __name__ == "__main__":
    initial_state = {{ INITIAL_STATE }}
    try:
        result = compiled_graph.invoke(initial_state)
        print("Graph execution successful! Response: ", result)
    except Exception as e:
        print(f"Graph-level error: {e}") 
"""

class Orchestrator:
    instructions_to_get_job_agents = """
    You are a helpful assistant working in an application that will help the user 
    automate recurring tasks in their life, by setting up a cronjob for them, which 
    will execute a sequence of AI agents that each have different purposes. You have 
    access to the following agent pool:

    {agent_descriptions}

    Your job is to first think through what steps/stages need to go into properly 
    fulfilling this request. Then, map these steps to the agents in the agent pool,
    and determine if the pool can provide you with all the necessary agents. If you 
    find that the pool does include all necessary agents, return back the list of 
    agents in the order they should be executed in the cronjob. Otherwise, if the 
    pool does not have all necessary agents, then return a string message saying so.

    User query:
    {query}
    """

    instructions_to_format_job_agents = """
    Your goal is to simply parse out the agent names into a list in the order that 
    you see them, from this message:

    {message}

    If you see no ordered list and instead some message that the agent pool does 
    not have all necessary agents, just return back this same message.
    """

    reasoning_model = "o1-mini-2024-09-12"
    non_reasoning_model = "gpt-4o"

    orchestrator = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
    )

    def determine_agents(self, msg: str):
        """
        Given the first message from the user on the UI, use the LLM (base and 
        reasoning models) to determie if there are sufficient agents available 
        in the pool to fulfill the (recurring) AI job request that underlies the 
        user's request
        """
        agent_descriptions = "\n".join(
            [f"{name}: {agent.description}" for name, agent in AGENT_DESCRIPTIONS.items()]
        )
        try:
            chat_completion = self.orchestrator.beta.chat.completions.parse(
                model=self.reasoning_model,
                messages=[
                    {
                        "role": "user",
                        "content": self.orchestrator_instructions_get_job_agents.format(
                            agent_descriptions=agent_descriptions, query=msg
                        ),
                    }
                ],
            )

            chat_completion = chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error determining agents for user query (call 1): {e}")

        try:
            chat_completion2 = self.orchestrator.beta.chat.completions.parse(
                model=self.non_reasoning_model,
                messages=[
                    {
                        "role": "user",
                        "content": self.orchestrator_instructions_format_job_agents \
                        .format(message=chat_completion),
                    }
                ],
                response_format=OrchestratorOutputFormat
            )

            response = chat_completion2.choices[0].message.parsed
        except Exception as e:
            print(f"Error formatting agents (call 2): {e}")

        return response
    
    def _determine_agent_template_values(
            self, orig_user_query: str, 
            agent_description: str, 
            template_var_instructions: Dict[str, str]
        ) -> List[AgentTemplateVarInstruction]:
        template_var_instructions_str = "".join([f"{var_name}: \n{var_instructions}\n\n" for var_name, var_instructions in template_var_instructions.items()])

        prompt = f"""
Your job is to give me back what each of the following variables would be, 
given the agent description and user query. Make sure to back a response 
that is in JSON/dictionary format, where keys are variables and values are 
the values you determine for them.

Agent description: {agent_description}

User query: {orig_user_query}

Variables:
{template_var_instructions_str}
        """

        # Send all var_instructions into single prompt, call AI
        # Have the output conform to pydantic structure with {<key from var_instructions>: <prompt>}
        # This will be sent when initializing the agent
        try:
            chat_completion = self.orchestrator.beta.chat.completions.parse(
                model=self.non_reasoning_model,
                messages=[{"role": "user", "content": prompt}],
                response_format=AgentTemplateVarInstructionsOutputFormat
            )

            response = chat_completion.choices[0].message.parsed
            template_vars = response.ai_generated_template_vars
            return template_vars
        except Exception as e:
            print(f"Error determining agent template variables: {e}")

    def initialize_agents(self, orig_user_query: str, agent_names: List[str]) -> List[BaseAgent]:
        """
        Instantiate the actual agent classes, in the order they will be executed in 
        AI job, given the list of agent names determined from the agent-determination 
        piece of the orchestrator
        """

        agents = []
        prev_agent = None
        for i in range(len(agent_names)):
            # First, need to get the values for the LangGraph attributes/template 
            # variables, for this agent, using AI
            name = agent_names[i]
            agent_template_var_instructions = AGENT_REGISTRY[name].template_var_instructions

            # If we need to get the prompt instructions for this agent
            if agent_template_var_instructions:
                # If its a generation agent, then, instructions are supplied
                # Otherwise, the instructions depend on the node that came before it,
                # ie the state attributes that were set by this node
                # (prompt is set by this, via build_prompt_py_code template variable)
                # TODO: do we want to set some attribute on the class indicating whether
                # this agent is in the "vanilla generation" category? Or, do we 
                # want to just have some high level 4o agent?
                if "build_prompt_py_code" in agent_template_var_instructions:
                    if name == "scripturegenerationagent" and i == 0: # TODO: need to see if i == 0 is the only case for this
                        agent_template_values = self._determine_agent_template_values(
                            orig_user_query, AGENT_DESCRIPTIONS[name], agent_template_var_instructions)
                        agent_template_values = {
                            "build_prompt_py_code": f"prompt = generation_agent_prompt_template.format(instructions={agent_template_values['instructions']})"
                        }
                    else:
                        agent_template_values = [AgentTemplateVarInstruction(
                            template_var_name="build_prompt_py_code",
                            template_var_instruction=prev_agent.get_post_generation_agent_code()
                        )]
                else:
                    agent_template_values = self._determine_agent_template_values(
                        orig_user_query, AGENT_DESCRIPTIONS[name], agent_template_var_instructions)
            else:
                agent_template_values = []
            
            agent = AGENT_REGISTRY[name](agent_template_values, i)
            agents.append(agent)

            prev_agent = agent

        return agents

    def build_and_render_ai_job_workflow(self, agents: List[BaseAgent], output_file_path: str):
        """
        Builds the AI job workflow for the cronjob, referencing the instantiated list 
        of agents (in the order they will be executed). Reference things like the 
        LangGraph node code, step attribute, and agent name
        """
        template = Template(workflow_template)

        graph_state = "class State(TypedDict):\n" + "\n".join(
            f"    {key}: {value_type.__name__}"
            for agent in agents
            for key, value_type in agent.state_vars_set.items()
        )

        node_code_blocks = []
        nodes = []
        for agent in agents:
            code_block = agent.get_graph_node_code()

            # Inject template variables (AI-generated prompt instructions) for this code block
            for tvar in agent.ai_generated_template_vars:
                tvar_name, tvar_instruction = tvar.template_var_name, tvar.template_var_instruction

                # Cant do string .format() because { } are part of python's official syntax
                code_block = code_block.replace("{"+tvar_name+"}", tvar_instruction)

            node_code_blocks.append(code_block)
            nodes.append(f"graph.add_node(\"{agent.node_name}\", {agent.node_name})")

        edges = []
        # First edge, connects START to node
        edges.append(f"graph.add_edge(START, \"{agents[0].node_name}\")")
        for i in range(len(agents) - 1):
            agent, agent_after = agents[i], agents[i+1]
            edges.append(f"graph.add_edge(\"{agent.node_name}\", \"{agent_after.node_name}\")")
        # Last edge, connects to END
        edges.append(f"graph.add_edge(\"{agents[-1].node_name}\", END)")

        # Everything should be injected in or is set post-graph-node execution,
        # so initial graph state can be {}
        initial_state = {}

        rendered_script = template.render(
            STATE=graph_state,
            NODE_CODE_BLOCKS=node_code_blocks,
            NODES=nodes,
            EDGES=edges,
            INITIAL_STATE=initial_state
        )
        with open(output_file_path, "w") as f:
            f.write(rendered_script)

    def submit_cronjob(self, namespace: str, cronjob_manifest: Dict[str, Any]):
        batch_v1 = client.BatchV1Api()
        response = batch_v1.create_namespaced_cron_job(
            namespace=namespace,
            body=cronjob_manifest
        )