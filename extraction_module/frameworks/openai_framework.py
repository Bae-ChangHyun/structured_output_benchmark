import os
from typing import Any
from pydantic import create_model
from typing import get_args, get_origin

#from openai import OpenAI
from langfuse.openai import OpenAI
from loguru import logger
from langfuse import observe
from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class OpenAIFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.llm_host == "openai":
            self.client = OpenAI(max_retries=0)
            
        elif self.llm_host == "ollama" or self.llm_host == "vllm":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key="empty",
                max_retries=0,
            )
        elif self.llm_host == "google":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=os.getenv("GOOGLE_API_KEY"),
                max_retries=0,
            )
            self.response_model = self.remove_optional()

    def remove_optional(self):
        """
        gemini 모델을 openai api를 이용하여 structured output으로 변환할 때,
        pydantic BaseModel 객체의 Optional 필드가 있으면 아래와 같은 오류 발생
        openai.BadRequestError: Error code: 400 - [{'error': {'code': 400, 'message': "Unable to submit request because one or more response schemas didn't specify the schema type field. Learn more: https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output", 'status': 'INVALID_ARGUMENT'}}]
        """
        
        schema= self.response_model
        
        fields = {}
        for name, field in schema.model_fields.items():
            typ = field.annotation
            if get_origin(typ) is not None and get_origin(typ).__name__ == "Union":
                args = [a for a in get_args(typ) if a is not type(None)]
                if args:
                    typ = args[0]
            fields[name] = (typ, ...)
        NewModel = create_model(
            schema.__name__ + "Required",
            **fields,
            __base__=schema.__base__
        )
        return NewModel
            
    @observe(name='OpenAI Framework')
    def run(self, retries: int, inputs: dict = {}) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            response = self.client.chat.completions.parse(
                model=self.llm_model,
                messages=[
                    {"role": "user", "content": self.prompt.format(**inputs)}
                ],
                response_format=self.response_model,
                **self.extra_kwargs
            )
            return response.choices[0].message.parsed

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
