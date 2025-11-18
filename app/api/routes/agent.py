# # app/api/routes/agent.py
# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from loguru import logger
# from typing import Any, Dict, List, Optional
#
#
#
# from app.api.routes.users_complete import get_current_active_user as current_active_user
# from app.services.agent_factory import AgentFactory
#
# router = APIRouter(prefix="/agent", tags=["agent"])
#
#
# # -------------------- Request & Response Models --------------------
# class AgentRequest(BaseModel):
#     """
#     Model for the incoming request, containing the user's prompt.
#     """
#     prompt: str
#
#
# class AgentResponse(BaseModel):
#     """
#     Model for the outgoing response.
#     """
#     status: str
#     result: Dict[str, Any]
#
#
# # -------------------------------------------------------------------
#
#
# @router.post("/gmail", response_model=AgentResponse)
# async def agent_gmail_chat(request: AgentRequest, user=Depends(current_active_user)):
#     """
#     AI agent endpoint for interacting with Gmail via Composio tools and Groq LLM.
#     Uses Agno framework with specialized Gmail agent.
#     """
#     entity_id = str(user.id)
#
#     try:
#         # Create agent factory for this user
#
#         toolset = ComposioToolSet()
#         factory = AgentFactory(entity_id=entity_id)
#
#         # Create Gmail agent
#         gmail_agent = factory.create_gmail_agent()
#
#         logger.info(f"Processing Gmail request for user {entity_id}: {request.prompt}")
#
#         # Run the agent with the user's prompt
#         response = gmail_agent.run(request.prompt)
#
#         # Extract response content
#         if hasattr(response, 'content'):
#             final_text = response.content
#         elif isinstance(response, dict):
#             final_text = response.get('content', str(response))
#         else:
#             final_text = str(response)
#
#         # Extract tool calls if available
#         tool_calls_executed = []
#         if hasattr(response, 'messages'):
#             for msg in response.messages:
#                 if hasattr(msg, 'role') and msg.role == 'tool':
#                     tool_calls_executed.append({
#                         "name": getattr(msg, 'name', 'unknown'),
#                         "content": getattr(msg, 'content', '')
#                     })
#
#         logger.info(f"Gmail agent completed successfully for user {entity_id}")
#
#         return AgentResponse(
#             status="success",
#             result={
#                 "text": final_text,
#                 "tool_calls_executed": tool_calls_executed,
#                 "agent": "Gmail Agent"
#             }
#         )
#
#     except Exception as e:
#         logger.error(f"Agent Gmail chat error for user {entity_id}: {e}", exc_info=True)
#         error_detail = str(e)
#         raise HTTPException(status_code=500, detail=f"Agent failed: {error_detail}")
#
#
# @router.post("/calendar", response_model=AgentResponse)
# async def agent_calendar_chat(request: AgentRequest, user=Depends(current_active_user)):
#     """
#     AI agent endpoint for interacting with Google Calendar.
#     Uses Agno framework with specialized Calendar agent.
#     """
#     entity_id = str(user.id)
#
#     try:
#         factory = AgentFactory(entity_id=entity_id)
#         calendar_agent = factory.create_calendar_agent()
#
#         logger.info(f"Processing Calendar request for user {entity_id}: {request.prompt}")
#
#         response = calendar_agent.run(request.prompt)
#
#         if hasattr(response, 'content'):
#             final_text = response.content
#         elif isinstance(response, dict):
#             final_text = response.get('content', str(response))
#         else:
#             final_text = str(response)
#
#         tool_calls_executed = []
#         if hasattr(response, 'messages'):
#             for msg in response.messages:
#                 if hasattr(msg, 'role') and msg.role == 'tool':
#                     tool_calls_executed.append({
#                         "name": getattr(msg, 'name', 'unknown'),
#                         "content": getattr(msg, 'content', '')
#                     })
#
#         logger.info(f"Calendar agent completed successfully for user {entity_id}")
#
#         return AgentResponse(
#             status="success",
#             result={
#                 "text": final_text,
#                 "tool_calls_executed": tool_calls_executed,
#                 "agent": "Calendar Agent"
#             }
#         )
#
#     except Exception as e:
#         logger.error(f"Agent Calendar chat error for user {entity_id}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
#
#
# @router.post("/search", response_model=AgentResponse)
# async def agent_search_chat(request: AgentRequest, user=Depends(current_active_user)):
#     """
#     AI agent endpoint for web search operations.
#     Uses Agno framework with specialized Search agent.
#     """
#     entity_id = str(user.id)
#
#     try:
#         factory = AgentFactory(entity_id=entity_id)
#         search_agent = factory.create_search_agent()
#
#         logger.info(f"Processing Search request for user {entity_id}: {request.prompt}")
#
#         response = search_agent.run(request.prompt)
#
#         if hasattr(response, 'content'):
#             final_text = response.content
#         elif isinstance(response, dict):
#             final_text = response.get('content', str(response))
#         else:
#             final_text = str(response)
#
#         tool_calls_executed = []
#         if hasattr(response, 'messages'):
#             for msg in response.messages:
#                 if hasattr(msg, 'role') and msg.role == 'tool':
#                     tool_calls_executed.append({
#                         "name": getattr(msg, 'name', 'unknown'),
#                         "content": getattr(msg, 'content', '')
#                     })
#
#         logger.info(f"Search agent completed successfully for user {entity_id}")
#
#         return AgentResponse(
#             status="success",
#             result={
#                 "text": final_text,
#                 "tool_calls_executed": tool_calls_executed,
#                 "agent": "Search Agent"
#             }
#         )
#
#     except Exception as e:
#         logger.error(f"Agent Search chat error for user {entity_id}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
#
#
# @router.post("/weather", response_model=AgentResponse)
# async def agent_weather_chat(request: AgentRequest, user=Depends(current_active_user)):
#     """
#     AI agent endpoint for weather information.
#     Uses Agno framework with specialized Weather agent.
#     """
#     entity_id = str(user.id)
#
#     try:
#         factory = AgentFactory(entity_id=entity_id)
#         weather_agent = factory.create_weather_agent()
#
#         logger.info(f"Processing Weather request for user {entity_id}: {request.prompt}")
#
#         response = weather_agent.run(request.prompt)
#
#         if hasattr(response, 'content'):
#             final_text = response.content
#         elif isinstance(response, dict):
#             final_text = response.get('content', str(response))
#         else:
#             final_text = str(response)
#
#         tool_calls_executed = []
#         if hasattr(response, 'messages'):
#             for msg in response.messages:
#                 if hasattr(msg, 'role') and msg.role == 'tool':
#                     tool_calls_executed.append({
#                         "name": getattr(msg, 'name', 'unknown'),
#                         "content": getattr(msg, 'content', '')
#                     })
#
#         logger.info(f"Weather agent completed successfully for user {entity_id}")
#
#         return AgentResponse(
#             status="success",
#             result={
#                 "text": final_text,
#                 "tool_calls_executed": tool_calls_executed,
#                 "agent": "Weather Agent"
#             }
#         )
#
#     except Exception as e:
#         logger.error(f"Agent Weather chat error for user {entity_id}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")
#
#
# @router.post("/drive", response_model=AgentResponse)
# async def agent_drive_chat(request: AgentRequest, user=Depends(current_active_user)):
#     """
#     AI agent endpoint for Google Drive operations.
#     Uses Agno framework with specialized Drive agent.
#     """
#     entity_id = str(user.id)
#
#     try:
#         factory = AgentFactory(entity_id=entity_id)
#         drive_agent = factory.create_googledrive_agent()
#
#         logger.info(f"Processing Drive request for user {entity_id}: {request.prompt}")
#
#         response = drive_agent.run(request.prompt)
#
#         if hasattr(response, 'content'):
#             final_text = response.content
#         elif isinstance(response, dict):
#             final_text = response.get('content', str(response))
#         else:
#             final_text = str(response)
#
#         tool_calls_executed = []
#         if hasattr(response, 'messages'):
#             for msg in response.messages:
#                 if hasattr(msg, 'role') and msg.role == 'tool':
#                     tool_calls_executed.append({
#                         "name": getattr(msg, 'name', 'unknown'),
#                         "content": getattr(msg, 'content', '')
#                     })
#
#         logger.info(f"Drive agent completed successfully for user {entity_id}")
#
#         return AgentResponse(
#             status="success",
#             result={
#                 "text": final_text,
#                 "tool_calls_executed": tool_calls_executed,
#                 "agent": "Google Drive Agent"
#             }
#         )
#
#     except Exception as e:
#         logger.error(f"Agent Drive chat error for user {entity_id}: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")