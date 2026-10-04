import json
import ollama
import streamlit as st
from tools import available_tools, tools_schema

# 1. Page Configuration
st.set_page_config(page_title="Local AI Agent", page_icon="🤖", layout="centered")

st.title("🤖 Unlimited Local AI Agent")
st.caption("Running 100% locally via Ollama (Llama 3.2 3B) - Zero API Cost")

MODEL = "llama3.2:3b"

# 2. Chat History Initialize
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are an intelligent AI Agent running locally on Ollama. "
                "STRICT RULE: Respond ONLY in Roman Urdu or English. "
                "NEVER use Devanagari Hindi script. "
                "Always use tools when needed to answer user queries accurately."
            ),
        }
    ]

# 3. Previous Chat Render Karein
for msg in st.session_state.messages:
    if msg["role"] != "system" and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 4. Main Chat Logic
if user_input := st.chat_input("Pooch kar dekhein: 'Latest AI news search karo'"):
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Local Llama Model Soch Raha Hai..."):
            try:
                # First Ollama Chat Call
                response = ollama.chat(
                    model=MODEL,
                    messages=st.session_state.messages,
                    tools=tools_schema,
                )

                response_message = response["message"]
                tool_calls = response_message.get("tool_calls")

                if tool_calls:
                    st.session_state.messages.append(response_message)

                    for tool_call in tool_calls:
                        func_name = tool_call["function"]["name"]
                        func_args = tool_call["function"]["arguments"]

                        if isinstance(func_args, str):
                            func_args = json.loads(func_args)

                        st.status(f"⚙ Executing Tool: `{func_name}`...", state="running")

                        if func_name in available_tools:
                            func_res = available_tools[func_name](**func_args)
                        else:
                            func_res = json.dumps({"error": "Tool not found"})

                        st.session_state.messages.append({
                            "role": "tool",
                            "content": str(func_res),
                        })

                    # Second Ollama Call (Tool execution ke baad final answer)
                    second_response = ollama.chat(
                        model=MODEL,
                        messages=st.session_state.messages,
                    )
                    final_reply = second_response["message"]["content"]
                else:
                    final_reply = response_message["content"]

                st.markdown(final_reply)
                st.session_state.messages.append({"role": "assistant", "content": final_reply})

            except Exception as e:
                st.error(f"❌ Error: {e}")