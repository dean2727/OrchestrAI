from jinja2 import Template

# String template (langgraph python script) which each AI cronjob will be based off of
workflow_template = """
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import TypedDict
import os
from langgraph.graph import END, StateGraph
from langchain.agents import initialize_agent

{{ STATE }}

{% for code_block in NODE_CODE_BLOCKS %}
{{ code_block }}
{% endfor %}

{% for node in NODES %}
{{ node }}
{% endfor %}

{% for edge in EDGES %}
{{ edge }}
{% endfor %}

graph = StateGraph(State)

...

compiled_graph = graph.compile()

if __name__ == "__main__":
    initial_state = {
        {{ INITIAL_STATE }}
    }
    try:
        result = compiled_graph.invoke(initial_state)
        print("Graph execution successful! Response: ", result)
    except Exception as e:
        print(f"Graph-level error: {e}") 
"""

x = Template(workflow_template)

rendered_script = x.render(
    STATE="hello1!",
    NODE_CODE_BLOCKS=["x", "y", "z"],
    NODES=["hello2!", "hello3!"],
    EDGES=["hello4!", "hello5!"],
    INITIAL_STATE="hello6!"
)

with open("test_jinja.py", "w") as f:
    f.write(rendered_script)