from mcpomni_connect.types import ContextInclusion
import asyncio
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    ErrorData,
    TextContent,
)
from mcp.shared.context import RequestContext
from typing import Optional, List, Any, Dict
from mcpomni_connect.utils import logger
import os
from openai import OpenAI
from pathlib import Path
import json


from typing import Any

from groq import Groq
from openai import OpenAI
from mcpomni_connect.utils import logger
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("LLM_API_KEY")


class LLMConnection:
    def __init__(self):
        self.openai = OpenAI(api_key=api_key)
        self.groq = Groq(api_key=api_key)
        self.openrouter = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.gemini = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=api_key,
        )
        self.deepseek = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=api_key,
        )

    async def llm_call(
        self,
        messages: list[dict[str, Any]],
        provider,
        model,
        temperature,
        max_tokens,
        stop,
    ):
        try:
            provider = provider.lower()

            if provider == "openai":
                response = await asyncio.to_thread(
                    self.openai.chat.completions.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stop=stop,
                )
                return response

            elif provider == "groq":
                response = await asyncio.to_thread(
                    self.groq.chat.completions.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stop=stop,
                )
                return response

            elif provider == "openrouter":
                response = await asyncio.to_thread(
                    self.openrouter.chat.completions.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stop=stop,
                )
                return response

            elif provider == "gemini":
                response = await asyncio.to_thread(
                    self.gemini.chat.completions.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stop=stop,
                )
                return response

            elif provider == "deepseek":
                response = await asyncio.to_thread(
                    self.deepseek.chat.completions.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages,
                    stop=stop,
                )
                return response
            else:
                return ErrorData(
                    code="INVALID_REQUEST",
                    message=f"Unsupported LLM provider: {provider}",
                )
        except Exception as e:
            logger.error(f"Error calling LLM for provider '{provider}': {e}")
            return ErrorData(
                code="INTERNAL_ERROR", message=f"An error occurred: {str(e)}"
            )


class samplingCallback:
    llm_connection = LLMConnection()

    async def load_model(self):
        config_path = Path("servers_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            llm_config = config.get("LLM", {})
            # Get available models for the provider
            available_models = []
            models = llm_config.get("model", [])
            if not isinstance(models, list):
                models = [models]
            available_models.extend(models)
            provider = llm_config.get("provider").lower()
        return available_models, provider

    async def _select_model(
        self, preferences, available_models: List[str]
    ) -> str:
        """Select the best model based on preferences and available models."""

        if not preferences or not preferences.hints:
            return available_models[0]  # Default to first available model

        # Try to match hints with available models
        for hint in preferences.hints:
            if not hint.name:
                continue
            for model in available_models:
                if hint.name.lower() in model.lower():
                    return model

        # If no match found, use priorities to select model
        if (
            preferences.intelligencePriority
            and preferences.intelligencePriority > 0.7
        ):
            # Prefer more capable models
            return max(
                available_models, key=lambda x: len(x)
            )  # Simple heuristic
        elif preferences.speedPriority and preferences.speedPriority > 0.7:
            # Prefer faster models
            return min(
                available_models, key=lambda x: len(x)
            )  # Simple heuristic
        elif preferences.costPriority and preferences.cosPriority > 0.7:
            # Prefer cheaper models
            return min(
                available_models, key=lambda x: len(x)
            )  # Simple heuristic

        return available_models[0]  # Default fallback

    async def _get_context(
        self,
        include_context: Optional[ContextInclusion],
        server_name: str = None,
    ) -> str:
        """Get relevant context based on inclusion type."""
        if not include_context or include_context == ContextInclusion.NONE:
            return ""

        context_parts = []

        if include_context == ContextInclusion.THIS_SERVER:
            # Get context from specific server
            if server_name in self.sessions:
                session_data = self.sessions[server_name]
                if "message_history" in session_data:
                    context_parts.extend(session_data["message_history"])

        elif include_context == ContextInclusion.ALL_SERVERS:
            # Get context from all servers
            for session_data in self.sessions.values():
                if "message_history" in session_data:
                    context_parts.extend(session_data["message_history"])

        return "\n".join(context_parts)

    async def _sampling(
        self,
        context: RequestContext["ClientSession", Any],
        params: CreateMessageRequestParams,
    ) -> CreateMessageResult | ErrorData:
        """Enhanced sampling callback with support for advanced features."""
        try:

            # Validate required parameters
            if not params.messages or not isinstance(params.maxTokens, int):
                return ErrorData(
                    code="INVALID_REQUEST",
                    message="Missing required fields: messages or max_tokens",
                )

            # Get the LLM configuration from the client instance

            available_models, provider = await self.load_model()

            # Select model based on preferences
            model = await self._select_model(
                params.modelPreferences, available_models
            )

            additional_context = await self._get_context(params.includeContext)

            # Prepare messages with context and system prompt
            messages = []
            if params.systemPrompt:
                messages.append(
                    {"role": "system", "content": params.systemPrompt}
                )
            if additional_context:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Context: {additional_context}",
                    }
                )
            messages.extend(
                [
                    {"role": msg.role, "content": msg.content.text}
                    for msg in params.messages
                ]
            )

            # Initialize the appropriate client based on provider
            response = await self.llm_connection.llm_call(
                provider=provider,
                messages=messages,
                model=model,
                temperature=params.temperature,
                max_tokens=params.maxTokens,
                stop=params.stopSequences,
            )
            completion = response.choices[0].message.content
            stop_reason = response.choices[0].finish_reason

            # Create the result
            result = CreateMessageResult(
                model=model,
                stop_reason=stop_reason,
                role="assistant",
                content=TextContent(type="text", text=completion),
            )

            logger.debug(f"Sampling callback completed successfully: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in sampling callback: {str(e)}")
            return ErrorData(
                code="INTERNAL_ERROR", message=f"An error occurred: {str(e)}"
            )
