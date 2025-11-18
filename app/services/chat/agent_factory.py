# """Agent factory module for creating specialized agents"""
# from agno.agent import Agent
# from agno.models.groq import Groq
# from composio_agno import ComposioToolSet
# from loguru import logger
# from typing import Optional
#
# from app.core.agent_config import (
#     AGENT_CONFIG,
#     gmail_tools_actions,
#     calendar_tools_actions,
#     weather_tools_actions,
#     websearch_tools_actions,
#     googledrive_tools_actions,
# )
# from app.core.config import COMPOSIO_API_KEY, GROQ_API_KEY
#
#
# class AgentFactory:
#     """Factory class for creating specialized agents"""
#
#     def __init__(self, entity_id: str):
#         """
#         Initialize agent factory with entity ID.
#
#         Args:
#             entity_id: User entity ID for Composio
#         """
#         self.entity_id = entity_id
#         self.toolset: Optional[ComposioToolSet] = None
#         self._initialize_toolset()
#
#     def _initialize_toolset(self):
#         """Initialize Composio toolset"""
#         try:
#             if not COMPOSIO_API_KEY:
#                 raise ValueError("COMPOSIO_API_KEY is not set")
#
#             self.toolset = ComposioToolSet(
#                 api_key=COMPOSIO_API_KEY,
#                 entity_id=self.entity_id
#             )
#             logger.info(f"Initialized ComposioToolSet for entity {self.entity_id}")
#         except Exception as e:
#             logger.error(f"Error initializing toolset: {e}")
#             raise
#
#     def _get_groq_model(self):
#         """Get configured Groq model"""
#         if not GROQ_API_KEY:
#             raise ValueError("GROQ_API_KEY is not set")
#
#         return Groq(
#             id=AGENT_CONFIG["model"],
#             api_key=GROQ_API_KEY
#         )
#
#     def create_gmail_agent(self) -> Agent:
#         """Create Gmail agent"""
#         try:
#             # Get Gmail tools
#             gmail_tools = self.toolset.get_tools(
#                 actions=gmail_tools_actions,
#             )
#
#             logger.info(f"Created Gmail agent with {len(gmail_tools)} tools")
#
#             return Agent(
#                 name="Gmail Agent",
#                 role="Manage email communications",
#                 model=self._get_groq_model(),
#                 instructions=[
#                     "Use tools to manage Gmail operations",
#                     "Use HTML instead of markdown formatting for better readability while writing emails or drafts",
#                     "Always confirm the action was completed successfully",
#                     "Be concise and helpful in your responses",
#                     "Extract email addresses, subjects, and body content from user requests",
#                 ],
#                 add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
#                 timezone_identifier=AGENT_CONFIG["timezone"],
#                 tools=gmail_tools,
#                 add_location_to_instructions=AGENT_CONFIG["add_location"],
#                 markdown=True,
#                 show_tool_calls=True,
#             )
#         except Exception as e:
#             logger.error(f"Error creating Gmail agent: {e}")
#             raise
#
#     def create_calendar_agent(self) -> Agent:
#         """Create Google Calendar agent"""
#         try:
#             calendar_tools = self.toolset.get_tools(
#                 actions=calendar_tools_actions,
#             )
#
#             logger.info(f"Created Calendar agent with {len(calendar_tools)} tools")
#
#             return Agent(
#                 name="Google Calendar Agent",
#                 role="Manage calendar events and schedules",
#                 model=self._get_groq_model(),
#                 instructions=[
#                     "Use tools to create and find calendar events",
#                     "Use currency and other metrics/units as per the location of the user",
#                     "Always confirm the action was completed successfully",
#                 ],
#                 add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
#                 timezone_identifier=AGENT_CONFIG["timezone"],
#                 tools=calendar_tools,
#                 add_location_to_instructions=AGENT_CONFIG["add_location"],
#                 markdown=True,
#                 show_tool_calls=True,
#             )
#         except Exception as e:
#             logger.error(f"Error creating Calendar agent: {e}")
#             raise
#
#     def create_weather_agent(self) -> Agent:
#         """Create Weather agent"""
#         try:
#             weather_tools = self.toolset.get_tools(
#                 actions=weather_tools_actions,
#             )
#
#             logger.info(f"Created Weather agent with {len(weather_tools)} tools")
#
#             return Agent(
#                 name="Weather Agent",
#                 role="Provide weather information",
#                 model=self._get_groq_model(),
#                 instructions=[
#                     "Use tools to fetch current weather data",
#                     "Use currency and other metrics/units as per the location of the user",
#                 ],
#                 add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
#                 timezone_identifier=AGENT_CONFIG["timezone"],
#                 tools=weather_tools,
#                 add_location_to_instructions=AGENT_CONFIG["add_location"],
#                 markdown=True,
#                 show_tool_calls=True,
#             )
#         except Exception as e:
#             logger.error(f"Error creating Weather agent: {e}")
#             raise
#
#     def create_search_agent(self) -> Agent:
#         """Create Web Search agent"""
#         try:
#             search_tools = self.toolset.get_tools(
#                 actions=websearch_tools_actions,
#             )
#
#             logger.info(f"Created Search agent with {len(search_tools)} tools")
#
#             return Agent(
#                 name="Web Search Agent",
#                 role="Handle web search requests and general research",
#                 model=self._get_groq_model(),
#                 instructions=[
#                     "Use tools to perform web searches and gather information",
#                     "Use currency and other metrics/units as per the location of the user",
#                     "Provide comprehensive and accurate information",
#                 ],
#                 add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
#                 timezone_identifier=AGENT_CONFIG["timezone"],
#                 tools=search_tools,
#                 add_location_to_instructions=AGENT_CONFIG["add_location"],
#                 markdown=True,
#                 show_tool_calls=True,
#             )
#         except Exception as e:
#             logger.error(f"Error creating Search agent: {e}")
#             raise
#
#     def create_googledrive_agent(self) -> Agent:
#         """Create Google Drive agent"""
#         try:
#             googledrive_tools = self.toolset.get_tools(
#                 actions=googledrive_tools_actions,
#             )
#
#             logger.info(f"Created Google Drive agent with {len(googledrive_tools)} tools")
#
#             return Agent(
#                 name="Google Drive Agent",
#                 role="Manage files and documents in Google Drive",
#                 model=self._get_groq_model(),
#                 instructions=[
#                     "Use tools to manage files in Google Drive",
#                     "Use currency and other metrics/units as per the location of the user",
#                     "Always confirm file operations were successful",
#                 ],
#                 add_datetime_to_instructions=AGENT_CONFIG["add_datetime"],
#                 timezone_identifier=AGENT_CONFIG["timezone"],
#                 tools=googledrive_tools,
#                 markdown=True,
#                 show_tool_calls=True,
#             )
#         except Exception as e:
#             logger.error(f"Error creating Google Drive agent: {e}")
#             raise