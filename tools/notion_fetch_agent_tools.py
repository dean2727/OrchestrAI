import os
from langchain.tools import tool
from notion_client import Client

# Notion fetch function
# TODO: figure out auth for this, if app will go into prod eventually
@tool
def fetch_latest_notion_journaling_entry(dummy_input: str = "") -> str:
    """Fetch the latest journaling entry (page) from a Notion database (pass in a random string)."""

    # TODO: Extract this out later
    # This is my hardcoded database ID for 
    notion_db_id = "9dd35093a917436f9de6aa56b28c6182"
    # notion_db_id = os.environ["NOTION_DB_ID"]
    notion = Client(auth=os.environ["NOTION_BEARER_TOKEN"])
    response = notion.databases.query(
        database_id=notion_db_id,
        sorts=[
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ],
        page_size=1  # Limit to the most recent entry
    )

    def get_page_content(page_id):
        blocks = notion.blocks.children.list(block_id=page_id)
        content = []
        for block in blocks["results"]:
            block_type = block["type"]
            if block_type == "paragraph" and block["paragraph"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
                content.append(f"Paragraph: {text}")
            elif block_type == "heading_1" and block["heading_1"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["heading_1"]["rich_text"]])
                content.append(f"Heading 1: {text}")
            elif block_type == "heading_2" and block["heading_2"]["rich_text"]:
                text = "".join([t["plain_text"] for t in block["heading_2"]["rich_text"]])
                content.append(f"Heading 2: {text}")
            # Add more block types as needed (e.g., "image", "to_do", etc.)
        return content

    # Process and display the results
    results = response["results"]
    output_string = ""
    for i, page in enumerate(results, 1):
        # Get the title (adjust based on your database's property name)
        title = page["properties"].get("Name", {}).get("title", [{}])[0].get("plain_text", "No title")
        created_time = page["created_time"]
        page_id = page["id"]
        
        # Fetch the page content
        content = get_page_content(page_id)
        
        # Add the page details and content to the output string
        output_string += f"{i}. Title: {title}, Created: {created_time}\n"
        if content:
            output_string += "   Content:\n"
            for line in content:
                output_string += f"      {line}\n"
        else:
            output_string += "   No content blocks found.\n"
        output_string += "\n"

    return output_string