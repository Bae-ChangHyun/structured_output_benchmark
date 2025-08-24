import os
import json
from typing import Any
from langfuse import observe
from ollama._client import Client
from structured_output_kit.extraction.base import BaseFramework, experiment


class OllamaFramework(BaseFramework):
    """_summary_
    https://ollama.com/blog/structured-outputs
    """
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.client = Client(self.base_url,
                             api_key=self.api_key or os.getenv("OLLAMA_API_KEY", "dummy"))

    @observe(name='Ollama Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            
            response = self.client.chat(
                model=self.model,
                format=self.response_model.model_json_schema(),
                messages=[
                    {"role": "user", "content": self.prompt.format(**inputs)}
                ],
            )
            content = json.loads(response.message.content)
            
            return content

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
