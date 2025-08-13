from typing import Any
from mirascope import llm
from mirascope.core import openai
from openai import OpenAI
from langfuse import observe
from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class MirascopeFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def response(self, prompt):

        if self.llm_host == 'openai' or self.llm_host == 'google':
            @llm.call(provider=self.llm_host, model=self.llm_model, response_model=self.response_model)
            def extract_info(query: str):
                return f"{query}"
        else:
            client =  OpenAI(
                base_url=self.base_url,
                api_key="dummy",
                max_retries=0,
                timeout=self.timeout)
            
            @openai.call(self.llm_model, response_model=self.response_model, client=client)
            def extract_info(query: str):
                return f"{query}"

        return extract_info(prompt)

    @observe(name='Mirascope Framework')
    def run(
        self, retries: int, inputs: dict = {}, kwargs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
 
            response = self.response(self.prompt.format(**inputs))
            
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
