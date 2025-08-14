import os
from typing import Any
from huggingface_hub import User
from loguru import logger
import instructor
from openai import OpenAI
from langfuse import observe

from structured_output_benchmark.extraction_module.base import BaseFramework, experiment


class InstructorFramework(BaseFramework):
    # https://python.useinstructor.com
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
 
        provider = self.provider if self.provider != "openai_compatible" else "ollama"
        
        if self.provider in ['ollama', 'openai_compatible']:
            base_url = os.getenv("OLLAMA_BASEURL") if provider=='ollama' else os.getenv("OPENAI_COMPATIBLE_BASEURL")
            provider = 'ollama'
            self.client = instructor.from_provider(f"{provider}/{self.model}",
                                                   base_url=base_url,
                                                   api_key=self.api_key or os.getenv("OLLAMA_API_KEY") or os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                                                   )
        else:
            self.client = instructor.from_provider(f"{provider}/{self.model}")

    @observe(name='Instructor Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            # if self.provider == "google":
            #     response = self.instructor_client.chat.completions.create(
            #         response_model=self.response_model,
            #         max_retries=retries,
            #         messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
            #         temperature=self.temperature,
            #     )
            # else:
            #     response = self.instructor_client.chat.completions.create(
            #         model=self.model,
            #         response_model=self.response_model,
            #         max_retries=retries,
            #         messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
            #         temperature=self.temperature,
            #     )
            response = self.client.chat.completions.create(
                response_model=self.response_model,
                messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
                **self.extra_kwargs
            )
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
