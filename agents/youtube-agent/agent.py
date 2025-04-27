from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
#from google.adk.models.lite_llm import LiteLlm
from google.genai import types # For creating message Content/Parts
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
import os
import dotenv

dotenv.load_dotenv()

async def search_youtube_videos(search_query: str, max_results: int):
    """
    Search for YouTube videos based on a search query.
        
    Args:
        search_query: The search terms to look for on YouTube (e.g., 'Google Cloud Next 25')
        max_results: Optional. Maximum number of results to return (default: 10)

    Returns:
        List of YouTube videos with details including title, channel, link, published date, 
        duration, views, thumbnail URL, and description.
    """
    try:
        # MCPToolset.from_server() returns a coroutine that needs to be awaited
        # It doesn't support the async context manager protocol directly
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command="mcp-youtube-search",
                args=[],
                env={"SERP_API_KEY": os.getenv("SERP_API_KEY")},
            )
        )
        
        try:
            # Get the first tool (should be the YouTube search tool)
            if not tools:
                return "No YouTube search tool available"
            
            youtube_tool = tools[0]
            
            # Execute the tool with properly formatted arguments
            result = await youtube_tool.run_async(
                args={"search_query": search_query}, 
                tool_context=None
            )
            return result
        finally:
            # Make sure to close the exit_stack when done
            await exit_stack.aclose()
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"

youtube_agent = Agent(
    name="youtube_assistant",
    model="gemini-2.0-flash",
    description=(
        "Agent to retrieve information from various data sources, including Notion and Youtube"
    ),
    instruction="""You are a helpful YouTube video search assistant.
Your goal is to use the search_youtube tool and present the results clearly.

1.  When asked to find videos, call the search_youtube tool.
2.  The tool will return a JSON object. Find the list of videos in the 'results' field of this JSON.
3.  For each video in the list, create a bullet point (*).
4.  Format each bullet point like this: **Title** (Link) by Channel: Description. (Published Date, Views, Duration)
    - Use the 'title', 'link', 'channel', 'description', 'published_date', 'views', and 'duration' fields from the JSON for each video.
    - Make the title bold.
    - Put the link in parentheses right after the title.
5.  Your final response should ONLY be the formatted bullet list of videos. Do not include the raw JSON.
6.  If the 'results' list in the JSON is empty, simply respond: "I couldn't find any videos for that search."
""",
    tools=[search_youtube_videos],
)

import asyncio
if __name__ == "__main__":
    session_service = InMemorySessionService()

    # Define constants for identifying the interaction context
    APP_NAME = "sample_app"
    USER_ID = "user_1"
    SESSION_ID = "session_001" # Using a fixed ID for simplicity

    # Create the specific session where the conversation will happen
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print(f"Session created: App='{APP_NAME}', User='{USER_ID}', Session='{SESSION_ID}'")

    # --- Runner ---
    # Key Concept: Runner orchestrates the agent execution loop.
    runner = Runner(
        agent=youtube_agent, # The agent we want to run
        app_name=APP_NAME,   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    print(f"Runner created for agent '{runner.agent.name}'.")

    async def call_agent_async(query: str, runner, user_id, session_id):
        """Sends a query to the agent and prints the final response."""
        print(f"\n>>> User Query: {query}")

        # Prepare the user's message in ADK format
        content = types.Content(role='user', parts=[types.Part(text=query)])

        final_response_text = "Agent did not produce a final response." # Default

        # Key Concept: run_async executes the agent logic and yields Events.
        # We iterate through events to find the final answer.
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
            # You can uncomment the line below to see *all* events during execution
            print(f"  [Event] Author: {event.author}, Type: {type(event).__name__}, Final: {event.is_final_response()}, Content: {event.content}")
            
            #print("DEBUG:", (event.content if event.content else ''), "~~~~", (event.actions if event.actions else ''))

            # Key Concept: is_final_response() marks the concluding message for the turn.
            if event.is_final_response():
                if event.content and event.content.parts:
                    # Assuming text response in the first part
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate: # Handle potential errors/escalations
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                # Add more checks here if needed (e.g., specific error codes)
                break # Stop processing events once the final response is found

        print(f"<<< Agent Response: {final_response_text}")

    async def run_conversation():
        await call_agent_async("show me videos on google vertex AI",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID)
    try:
        asyncio.run(run_conversation())
    except Exception as e:
        print(f"An error occurred: {e}")