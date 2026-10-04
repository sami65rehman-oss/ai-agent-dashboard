import os
import json
from dotenv import load_dotenv
from groq import Groq
from tools import available_tools, tools_schema

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def run_agent(messages):
    """Function Calling agent loop using Groq API."""
    if not GROQ_API_KEY:
        return "❌ Error: GROQ_API_KEY missing in .env file."

    client = Groq(api_key=GROQ_API_KEY)

    try:
        # First call to LLM with tool definitions
        response = client.chat.completions.create(
            messages=messages,
            model="openai/gpt-oss-120b",
            tools=tools_schema,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Check if the LLM requested a tool execution
        if tool_calls:
            # Append LLM's response message to conversation context
            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Execute the corresponding tool
                if function_name in available_tools:
                    tool_function = available_tools[function_name]
                    tool_result = tool_function(**function_args)

                    # Append tool response back to messages
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(tool_result)
                    })

            # Second call to LLM to parse tool results into natural language
            second_response = client.chat.completions.create(
                messages=messages,
                model="openai/gpt-oss-120b"
            )
            return second_response.choices[0].message.content

        # Standard conversation response if no tool was called
        return response_message.content

    except Exception as e:
        return f"❌ Groq Error: {str(e)}"