import os
from typing import Any
from mirascope import llm
from mirascope.core import openai
from openai import OpenAI
from langfuse import observe
from structured_output_kit.extraction.base import BaseFramework, experiment


class MirascopeFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def response(self, prompt, call_params=None):
        if self.provider == 'openai' or self.provider == 'google':
            @llm.call(provider=self.provider, model=self.model, response_model=self.response_model)
            def extract_info(query: str, call_params=None):
                return {
                    "messages": [{"role": "user", "content": query}],
                    "call_params": call_params,
                }
        else:
            if self.provider == 'ollama':
                client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key or os.getenv("OLLAMA_API_KEY", "dummy"),
                    max_retries=0,
                    timeout=self.timeout)
            else:
                client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                    max_retries=0,
                    timeout=self.timeout)
            @openai.call(self.model, response_model=self.response_model, client=client)
            def extract_info(query: str, call_params=None):
                return {
                    "messages": [{"role": "user", "content": query}],
                    "call_params": call_params,
                }
        return extract_info(prompt, call_params=call_params)

    @observe(name='Mirascope Framework')
    def run(
        self, retries: int, inputs: dict = {}, kwargs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            response = self.response(self.prompt.format(**inputs), call_params=self.extra_kwargs)
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
