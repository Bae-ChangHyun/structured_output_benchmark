import os
from typing import Any, Dict
import json

from ollama._client import Client
from langfuse import observe
from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class OllamaFramework(BaseFramework):
    """_summary_
    https://ollama.com/blog/structured-outputs
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = Client(self.base_url)

    @observe(name='Ollama Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            
            response = self.client.chat(
                model=self.llm_model,
                format=self.response_model.model_json_schema(),
                messages=[
                    {"role": "user", "content": self.prompt.format(**inputs)}
                ],
            )
            content = json.loads(response.message.content)
            
            return content

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies