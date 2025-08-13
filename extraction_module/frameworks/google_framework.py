import json
from typing import Any
from google import genai
from google.genai import types

from langfuse import observe
from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class GoogleFramework(BaseFramework):
    '''
    # https://ai.google.dev/gemini-api/docs/structured-output?hl=ko&lang=python
    # https://ai.google.dev/gemini-api/docs/structured-output?hl=ko&lang=rest
    '''
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        self.client = genai.Client()
        
    @observe(name='Google Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            response = self.client.models.generate_content(
                model = self.llm_model,
                contents = self.prompt.format(**inputs),
                config=types.GenerateContentConfig(
                    response_schema=self.response_model,
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.candidates[0].content.parts[0].text)
           
        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
