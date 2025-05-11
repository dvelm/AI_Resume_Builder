"""
This module contains utility functions for the Resume and Cover Letter Builder service.
"""

# app/libs/resume_and_cover_builder/utils.py
import json
# import openai # Remove direct openai import
import time
from datetime import datetime
from typing import Dict, List
from langchain_core.messages.ai import AIMessage, BaseMessage # Import BaseMessage for broader type hinting
from langchain_core.prompt_values import StringPromptValue
# from langchain_openai import ChatOpenAI # Remove ChatOpenAI import
from .config import global_config
from loguru import logger
from requests.exceptions import HTTPError as HTTPStatusError


class LLMLogger:

    # Use a more generic type hint if possible, or remove it if relying on duck typing
    def __init__(self, llm): # Removed ChatOpenAI type hint
        self.llm = llm

    @staticmethod
    def log_request(prompts, parsed_reply: Dict[str, Dict]):
        calls_log = global_config.LOG_OUTPUT_FILE_PATH / "open_ai_calls.json"
        # Process prompts safely
        if isinstance(prompts, StringPromptValue):
            prompts_log = prompts.text
        elif isinstance(prompts, dict) and 'messages' in prompts: # Handle Langchain Dict format
             prompts_log = {
                 f"prompt_{i+1}": msg.content
                 for i, msg in enumerate(prompts['messages']) if hasattr(msg, 'content')
             }
        elif hasattr(prompts, 'messages'): # Handle object with messages attribute
             prompts_log = {
                 f"prompt_{i+1}": msg.content
                 for i, msg in enumerate(prompts.messages) if hasattr(msg, 'content')
             }
        else:
             prompts_log = str(prompts) # Fallback to string representation

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Safely extract token usage details
        token_usage = parsed_reply.get("usage_metadata", {}) # Default to empty dict
        output_tokens = token_usage.get("output_tokens", 0)
        input_tokens = token_usage.get("input_tokens", 0)
        total_tokens = token_usage.get("total_tokens", 0)

        # Safely extract model details
        response_metadata = parsed_reply.get("response_metadata", {}) # Default to empty dict
        model_name = response_metadata.get("model_name", "unknown") # Default model name

        # Calculate cost only if tokens are available and it seems like an OpenAI model
        # (This cost calculation is specific to OpenAI pricing)
        total_cost = 0
        # Check if model_name is a non-empty string before lowercasing
        if total_tokens > 0 and isinstance(model_name, str) and "gpt" in model_name.lower():
             prompt_price_per_token = 0.00000015
             completion_price_per_token = 0.0000006
             total_cost = (input_tokens * prompt_price_per_token) + (
                 output_tokens * completion_price_per_token
             )

        # Create a log entry with all relevant information
        log_entry = {
            "model": model_name,
            "time": current_time,
            "prompts": prompts_log,
            "replies": parsed_reply.get("content", ""),  # Safely get content
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": total_cost, # Will be 0 if not calculated
        }

        # Write the log entry to the log file in JSON format
        try:
            with open(calls_log, "a", encoding="utf-8") as f:
                json_string = json.dumps(log_entry, ensure_ascii=False, indent=4)
                f.write(json_string + "\n")
        except Exception as e:
            logger.error(f"Failed to write to log file {calls_log}: {e}")


class LoggerChatModel:

    # Consider using a more generic type hint like BaseChatModel if importing from langchain_core.language_models
    def __init__(self, llm_adapter): # Accept the adapter or the specific model instance
        self.llm = llm_adapter # Store the adapter/model

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        max_retries = 15
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                reply = self.llm.invoke(messages)
                # Logging might need adjustment depending on how different models structure metadata
                # For now, assume parse_llmresult can handle the structure or skip logging if needed
                # parsed_reply = self.parse_llmresult(reply)
                # LLMLogger.log_request(prompts=messages, parsed_reply=parsed_reply)
                return reply
            except HTTPStatusError as err: # Remove openai.RateLimitError
                if hasattr(err, 'response') and err.response.status_code == 429:
                    logger.warning(f"HTTP 429 Rate Limit Exceeded: Waiting for {retry_delay} seconds before retrying (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    # Consider more specific error handling or re-raising
                    logger.error(f"HTTP error occurred: {err}. Waiting {retry_delay}s.")
                    time.sleep(retry_delay)
                    retry_delay *= 2 # Exponential backoff
            except Exception as e:
                logger.error(f"Unexpected error occurred: {str(e)}, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2

        logger.critical("Failed to get a response from the model after multiple attempts.")
        raise Exception("Failed to get a response from the model after multiple attempts.")

    # Adjust type hint to BaseMessage if needed
    def parse_llmresult(self, llmresult: BaseMessage) -> Dict[str, Dict]:
        # Parse the LLM result into a structured format, handling potential missing attributes.
        content = getattr(llmresult, 'content', "") # Safely get content
        response_metadata = getattr(llmresult, 'response_metadata', {}) # Default to empty dict if missing
        id_ = getattr(llmresult, 'id', None) # Default to None if missing
        usage_metadata = getattr(llmresult, 'usage_metadata', {}) # Default to empty dict if missing

        # Ensure metadata are dictionaries before using .get()
        if not isinstance(response_metadata, dict):
            response_metadata = {}
        if not isinstance(usage_metadata, dict):
            usage_metadata = {}

        parsed_result = {
            "content": content,
            "response_metadata": {
                "model_name": response_metadata.get("model_name", ""), # Use .get() safely
                "system_fingerprint": response_metadata.get("system_fingerprint", ""),
                "finish_reason": response_metadata.get("finish_reason", ""),
                "logprobs": response_metadata.get("logprobs", None),
            },
            "id": id_,
            "usage_metadata": {
                "input_tokens": usage_metadata.get("input_tokens", 0), # Use .get() safely
                "output_tokens": usage_metadata.get("output_tokens", 0),
                "total_tokens": usage_metadata.get("total_tokens", 0),
            },
        }
        return parsed_result
