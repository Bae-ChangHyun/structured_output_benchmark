import os
from typing import Any
from pydantic import create_model
from typing import get_args, get_origin

from langfuse.openai import OpenAI
from loguru import logger
from langfuse import observe
from structured_output_kit.extraction.base import BaseFramework, experiment


class OpenAIFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.provider == "openai":
            self.client = OpenAI(max_retries=0)

        elif self.provider == "ollama":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or os.getenv("OLLAMA_API_KEY", "dummy"),
                max_retries=0,
            )
        elif self.provider == "openai_compatible":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                max_retries=0,
            )
        elif self.provider == "google":
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=os.getenv("GOOGLE_API_KEY"),
                max_retries=0,
            )
            self.response_model = self.remove_optional()

    def remove_optional(self):
        schema = self.response_model
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
                model=self.model,
                messages=[
                    {"role": "user", "content": self.prompt.format(**inputs)}
                ],
                response_format=self.response_model,
                **self.extra_kwargs
            )
            return response.choices[0].message.parsed

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
