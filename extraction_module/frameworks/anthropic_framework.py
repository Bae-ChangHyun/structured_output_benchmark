import os
from typing import Any

import anthropic
from loguru import logger
from langfuse import observe

from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class AnthropicFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.client = anthropic.Anthropic(
            api_key=kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY"),
            timeout=self.timeout,
        )
        
        # tool schema 변환
        self.tool_schema = self._convert_schema_to_tool()

    def _convert_schema_to_tool(self) -> dict:
        """Pydantic BaseModel을 Anthropic tool schema로 변환"""
        if not self.response_model:
            raise ValueError("response_model이 설정되지 않았습니다.")
            
        # Pydantic 모델의 JSON schema 추출
        if hasattr(self.response_model, 'model_json_schema'):
            schema = self.response_model.model_json_schema()
        else:
            # 기존 스키마인 경우
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
            # 프롬프트 포맷팅
            formatted_prompt = self.prompt.format(**inputs)
            
            # Anthropic API 호출
            response = self.client.messages.create(
                model=self.llm_model,
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
            
            # 응답에서 tool_use 결과 추출
            if response.content and len(response.content) > 0:
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        return content_block.input
                        
            # tool_use가 없는 경우 예외 발생
            raise ValueError("응답에서 structured output을 찾을 수 없습니다.")

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
