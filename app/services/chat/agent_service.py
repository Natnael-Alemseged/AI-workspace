

#agent_service

import os
from dotenv import load_dotenv
from composio import Composio
from composio_llamaindex import LlamaIndexProvider
from groq import Groq
from llama_index.llms.openai_like import OpenAILike

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.groq import Groq

from app.core.config import GROQ_API_KEY, GROK_API_KEY, COMPOSIO_API_KEY
from app.services.memory_service import get_relevant_memories, add_memory
from app.utils.ai_agent_parser import AgentType

load_dotenv()

# Initialize LLM (Grok in this case, could be OpenAI if you swap)
llm = Groq(
    # model="grok-4-0709",
    model="openai/gpt-oss-120b",

    # api_base="https://api.x.ai/v1",
    api_key=GROQ_API_KEY,
    # context_window=128000,
    # is_chat_model=True,
    # is_function_calling_model=True,
)
# Initialize Composio with LlamaIndex provider
composio = Composio(api_key=COMPOSIO_API_KEY, provider=LlamaIndexProvider())

# Cache tools globally by agent type
email_tools = None
search_tools = None

async def get_tools(user_id: str, agent_type: str = None):
    """
    Get tools for a specific agent type.
    
    Args:
        user_id: User ID for Composio authentication
        agent_type: Type of agent (emailAi, searchAi, or None for all)
        
    Returns:
        List of tools for the specified agent type
    """
    global email_tools, search_tools
    
    if agent_type == AgentType.EMAIL_AI.value or agent_type == "emailAi":
        # Email agent - only Gmail tools
        if email_tools is None:
            email_tools = composio.tools.get(
                user_id=user_id,
                toolkits=["gmail"],
                limit=50
            )
            email_tools = [
                t for t in email_tools
                if t.metadata.name.startswith("GMAIL")
            ]
            print(f"✅ Email tools initialized: {len(email_tools)} tools")
        return email_tools
    
    elif agent_type == AgentType.SEARCH_AI.value or agent_type == "searchAi":
        # Search agent - only search tools
        if search_tools is None:
            search_tools = composio.tools.get(
                user_id=user_id,
                toolkits=["composio_search"],
                limit=50
            )
            # search_tools = [
            #     t for t in search_tools
            #     if t.metadata.name in ["COMPOSIO_SEARCH_WEB"]
            # ]
            print(f"✅ Search tools initialized: {len(search_tools)} tools")
        return search_tools
    
    else:
        # Default: all tools (backward compatibility)
        all_tools = composio.tools.get(
            user_id=user_id,
            toolkits=["gmail", "composio_search"],
            limit=50
        )
        all_tools = [
            t for t in all_tools
            if t.metadata.name in ["COMPOSIO_SEARCH_WEB"]
               or t.metadata.name.startswith("GMAIL")
        ]
        print(f"✅ All tools initialized: {len(all_tools)} tools")
        return all_tools


async def run_agent_stream(prompt: str, user_id: str, agent_type: str = None):
    """
    Run the AI agent with the specified prompt.
    
    Args:
        prompt: The user's prompt/request
        user_id: User ID for authentication and memory
        agent_type: Type of agent to use (emailAi, searchAi, or None for general)
        
    Returns:
        Agent response as string
    """
    tools_list = await get_tools(user_id, agent_type)

    # FETCH RELEVANT MEMORIES
    memories = get_relevant_memories(user_id, prompt, limit=2)
    memory_context = "\n".join(memories) if memories else "No prior context."

    # Customize agent based on type
    if agent_type == AgentType.EMAIL_AI.value or agent_type == "emailAi":
        agent_name = "Email Assistant"
        agent_description = "A specialized agent for managing Gmail and email tasks."
        system_prompt = (
            f"""You are a helpful email assistant specialized in managing Gmail. """
            f"""You can send emails, read emails, search emails, and manage email tasks. """
            f"""Here are relevant contexts: {memory_context}"""
        )
    elif agent_type == AgentType.SEARCH_AI.value or agent_type == "searchAi":
        agent_name = "Search Assistant"
        agent_description = "A specialized agent for web search and information retrieval."
        system_prompt = (
            f"""You are a helpful search assistant specialized in finding information on the web. """
            f"""You can search for information, answer questions, and provide relevant results. """
            f"""Here are relevant contexts: {memory_context}"""
        )
    else:
        agent_name = "Personal Assistant"
        agent_description = "A smart agent that manages Gmail and search Composio tools."
        system_prompt = (
            f"""You are a helpful personal assistant that can manage emails and search the web. """
            f"""Here are relevant contexts: {memory_context}"""
        )

    agent = FunctionAgent(
        name=agent_name,
        description=agent_description,
        tools=tools_list,
        llm=llm,
        system_prompt=system_prompt,
    )

    agent_output = await agent.run(prompt)

    # Extract the actual text safely
    message = agent_output.response

    # ← THIS IS THE ONLY LINE THAT MATTERS
    final_text = message.content if hasattr(message, 'content') else str(message)


    add_memory(
        user_id=user_id,
        prompt=prompt,
        response=final_text
    )


    print(f"Agent response ({agent_type or 'general'}):", final_text)
    return final_text  # ← Always a string → JSON works 100%

