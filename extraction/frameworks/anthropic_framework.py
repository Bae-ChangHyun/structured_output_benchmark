import os
from typing import Any

import anthropic
from loguru import logger
from langfuse import observe

from structured_output_kit.extraction.base import BaseFramework, experiment


class AnthropicFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout=self.timeout,
        )
        
        self.tool_schema = self._convert_schema_to_tool()

    def _convert_schema_to_tool(self) -> dict:
        if not self.response_model:
            raise ValueError("response_model이 설정되지 않았습니다.")
        if hasattr(self.response_model, 'model_json_schema'):
            schema = self.response_model.model_json_schema()
        else:
            schema = self.response_model
        return {
            "name": "extract_info",
            "description": "Extract structured information from the given text using well-defined JSON schema.",
            "input_schema": schema
        }

    @observe(name='Anthropic Framework')
    def run(self, retries: int, inputs: dict = {}) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            formatted_prompt = self.prompt.format(**inputs)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=32768,
                tools=[self.tool_schema],
                tool_choice={"type": "tool", "name": self.tool_schema["name"]},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": formatted_prompt},
                        ],
                    }
                ],
                **self.extra_kwargs
            )
            if response.content and len(response.content) > 0:
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        return content_block.input
            raise ValueError("응답에서 structured output을 찾을 수 없습니다.")

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
