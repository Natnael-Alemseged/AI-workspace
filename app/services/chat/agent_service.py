

#agent_service

import os
from dotenv import load_dotenv
from composio import Composio
from composio_llamaindex import LlamaIndexProvider
# Use OpenAILike for better compatibility with Groq's specialized models
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.agent.workflow import FunctionAgent

from app.core.config import GROQ_API_KEY, GROK_API_KEY, COMPOSIO_API_KEY
from app.services.memory_service import get_relevant_memories, add_memory
from app.services.redis_client import redis_client
from app.utils.ai_agent_parser import AgentType

load_dotenv()

# Initialize LLM (using OpenAILike for Groq's newer models to bypass specialized class validation)
llm = OpenAILike(
    model="openai/gpt-oss-120b",
    api_base="https://api.groq.com/openai/v1",

    api_key=GROQ_API_KEY,
    is_chat_model=True,
    is_function_calling_model=True,
    # context_window=131072, # Optional: set according to model specs
)
# Initialize Composio with LlamaIndex provider
composio = Composio(api_key=COMPOSIO_API_KEY, provider=LlamaIndexProvider())

# Cache tools globally by agent type
email_tools = None
search_tools = None

async def get_tools(user_id: str, agent_type: str = None, topic_id:str = None):
    """
    Get tools for a specific agent type.
    
    Args:
        user_id: User ID for Composio authentication
        agent_type: Type of agent (emailAi, searchAi, or None for all)
        
    Returns:
        Tuple of (List of tools, system_prompt_addition)
    """
    global email_tools, search_tools
    
    system_prompt_addition = ""

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
        return email_tools, system_prompt_addition
    
    elif agent_type == AgentType.SEARCH_AI.value or agent_type == "searchAi":
        # Search agent - only search tools
        if search_tools is None:
            search_tools = composio.tools.get(
                user_id=user_id,
                toolkits=["composio_search"],
                limit=50
            )
            print(f"✅ Search tools initialized: {len(search_tools)} tools")
        return search_tools, system_prompt_addition
    
    else:
        # Default: all tools (backward compatibility)
        # Dynamic connection check
        requested_toolkits = ["gmail", "composio_search", "googledocs", "googledrive"]
        active_toolkits = ["googledocs"]
        missing_toolkits = []
        
        try:
            # 1. Fetch user connections
            # Note: list() returns all connections for the app, we must filter by user_id if needed.
            # Assuming composio.client gives access to global connections.
            connections = composio.client.connected_accounts.list()
            
            # 2. Identify active toolkits for THIS user
            # Filter connections belonging to this user
            user_connections = [
                c for c in connections 
                if hasattr(c, 'user_id') and c.user_id == user_id and c.status == 'ACTIVE'
            ]
            
            # Get slugs of connected apps
            connected_slugs = {c.toolkit.slug for c in user_connections if hasattr(c, 'toolkit')}
            
            # 3. Classify requested toolkits
            for tk in requested_toolkits:
                # search might not need connection in the same way, but let's check.
                # 'composio_search' usually doesn't require user auth like gmail/docs.
                if tk == "composio_search":
                    active_toolkits.append(tk)
                    continue

                if tk in connected_slugs:
                    active_toolkits.append(tk)
                else:
                    missing_toolkits.append(tk)
            
            print(f"✅ Active Toolkits: {active_toolkits}")
            print(f"❌ Missing Toolkits: {missing_toolkits}")

        except Exception as e:
            print(f"⚠️ Error checking connections: {e}")
            # Fallback: try to fetch all, and let them fail if not connected
            active_toolkits = requested_toolkits
            missing_toolkits = []

        # 4. Fetch tools for active toolkits
        all_tools = []
        if active_toolkits:
             all_tools = composio.tools.get(
                user_id=user_id,
                # toolkits=active_toolkits,
                toolkits=requested_toolkits,
                limit=500
            )

        # 5. Handle missing connections
        if missing_toolkits:
            # Fetch generic Composio tools (includes MANAGE_CONNECTIONS)
            # We specifically want the connection manager
            try:
                composio_tools = composio.tools.get(toolkits=["composio"], user_id=user_id)
                conn_tools = [
                    t for t in composio_tools 
                    if "MANAGE_CONNECTIONS" in t.metadata.name
                ]
                all_tools.extend(conn_tools)
                
                # Update Prompt
                missing_str = ", ".join(missing_toolkits)
                system_prompt_addition = (
                    f"\nNOTE: The user is NOT connected to the following services: {missing_str}. "
                    f"If the user asks to perform tasks involving these services, "
                    f"you MUST use the `COMPOSIO_MANAGE_CONNECTIONS` tool to initiate the connection."
                )
            except Exception as e:
                print(f"Error fetching connection tools: {e}")

        # Filter specific tools as before
        all_tools = [
            t for t in all_tools
            if t.metadata.name in ["COMPOSIO_SEARCH_WEB", "COMPOSIO_MANAGE_CONNECTIONS"]
               or t.metadata.name.startswith("GMAIL")
               or t.metadata.name.startswith("GOOGLEDOCS")
               or t.metadata.name.startswith("GOOGLEDRIVE")
        ]
        print('all active tools from api are',active_toolkits)
        print(f"✅ All tools initialized count: {len(all_tools)} tools")
        print(f"✅ All tools initialized: {all_tools}")
        return all_tools, system_prompt_addition


async def run_agent_stream(prompt: str, user_id: str, agent_type: str = None,topic_id: str = None):
    """
    Run the AI agent with the specified prompt.
    
    Args:
        prompt: The user's prompt/request
        user_id: User ID for authentication and memory
        agent_type: Type of agent to use (emailAi, searchAi, or None for general)
        
    Returns:
        Agent response as string
    """
    tools_list, prompt_addition = await get_tools(user_id, agent_type,topic_id)

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
        # === GENERAL AGENT WITH PERSONA + REDIS + TOPIC SUPPORT ===
        import logging
        logger = logging.getLogger("demo")

        # Normalize topic_id
        topic_id = (topic_id or "general").strip().lower().replace(" ", "_")
        persona_key = f"persona:{user_id}:{topic_id}"

        # === STEP 1: Check if user is trying to change persona ===
        lower = prompt.lower().strip()
        if any(trigger in lower for trigger in [
            "act as", "be a ", "from now on", "change persona",
            "set persona", "talk like", "respond as", "pretend to be"
        ]) or lower.startswith("persona:"):
            # Extract the persona description
            if lower.startswith("persona:"):
                new_persona = prompt.split(":", 1)[1].strip()
            else:
                # Grab everything after common triggers
                for trigger in ["act as", "be a ", "talk like", "respond as", "pretend to be"]:
                    if trigger in lower:
                        new_persona = prompt.lower().split(trigger, 1)[1].strip()
                        break
                else:
                    new_persona = prompt  # fallback

            # Capitalize nicely for display
            display_persona = new_persona.title()
            if not display_persona.endswith((".", "!", "?")):
                display_persona += "!"

            # Save to Redis
            redis_client.set(persona_key, new_persona)
            logger.info(f"PERSONA CHANGED → {persona_key} = '{new_persona}'")

            return f"Got it!\n\n**{display_persona}**"

        # === STEP 2: Load current persona from Redis ===
        raw_persona = redis_client.get(persona_key)
        if raw_persona:
            if isinstance(raw_persona, bytes):
                raw_persona = raw_persona.decode("utf-8")
            current_persona = raw_persona
            logger.info(f"PERSONA LOADED from Redis → '{current_persona}'")
        else:
            current_persona = "A helpful, witty, and direct assistant."
            logger.info("No persona found → using default")

        # === STEP 3: Build dynamic system prompt with persona injected ===
        # === STEP 3: Build dynamic system prompt with persona injected ===
        system_prompt = f"""You are an AI assistant with a specific personality.
        
        CURRENT PERSONA (YOU MUST OBEY THIS EXACTLY):
        {current_persona}

        RULES:
        - Stay 100% in character. Never break role.
        - Use the persona's tone, vocabulary, and style in every reply.
        - You can use Gmail and web search tools when needed.
        - Past conversation context:
        {memory_context}

        Now respond to the user naturally."""

        # Inject connection prompt if exists
        if prompt_addition:
            system_prompt += f"\n\n{prompt_addition}"

        agent_name = f"{current_persona.split('.')[0][:30]}"
        agent_description = f"Assistant embodying: {current_persona[:100]}"

        logger.info(f"Launching agent with persona: {current_persona[:60]}...")

    # === REST OF YOUR CODE (unchanged) ===
    # Safeguard: Groq has a limit on the number of tools (usually 128). 
    # Capping at 100 to be safe and avoid the 'maximum number of items is 128' error.
    if len(tools_list) > 100:
        print(f"⚠️ Warning: Truncating tools from {len(tools_list)} to 100 for Groq compatibility")
        tools_list = tools_list[:100]

    agent = FunctionAgent(
        name=agent_name,
        description=agent_description,
        tools=tools_list,
        llm=llm,
        system_prompt=system_prompt,
    )

    agent_output = await agent.run(prompt)
    message = agent_output.response
    final_text = message.content if hasattr(message, 'content') else str(message)

    add_memory(user_id=user_id, prompt=prompt, response=final_text)
    print(f"Agent ({topic_id}):", final_text)
    return final_text