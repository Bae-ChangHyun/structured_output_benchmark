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
        # if self.llm_host == "openai":
        #     self.instructor_client = instructor.from_openai(
        #         client = OpenAI(max_retries=0),)
            
        # elif self.llm_host == "ollama" or self.llm_host == "vllm":
        #     self.instructor_client = instructor.from_openai(
        #         client = OpenAI(
        #         base_url = self.base_url,
        #         api_key = "empty",
        #         timeout = self.timeout,
        #         max_retries = 0),
        #         mode=instructor.Mode.JSON)
            
        # elif self.llm_host == "google":
        #     self.instructor_client = instructor.from_provider(
        #         model=f"google/{self.llm_model}",
        #         mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS
        #     )

        llm_host = self.llm_host if self.llm_host != "vllm" else "ollama"
        
        if self.llm_host in ['ollama', 'vllm']:
            base_url = os.getenv("OLLAMA_BASEURL") if self.llm_host=='ollama' else os.getenv("VLLM_BASEURL")
            llm_host = 'ollama'
            self.client = instructor.from_provider(f"{llm_host}/{self.llm_model}",
                                                   base_url=base_url)
        else:
            self.client = instructor.from_provider(f"{llm_host}/{self.llm_model}")

    @observe(name='Instructor Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            # if self.llm_host == "google":
            #     response = self.instructor_client.chat.completions.create(
            #         response_model=self.response_model,
            #         max_retries=retries,
            #         messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
            #         temperature=self.temperature,
            #     )
            # else:
            #     response = self.instructor_client.chat.completions.create(
            #         model=self.llm_model,
            #         response_model=self.response_model,
            #         max_retries=retries,
            #         messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
            #         temperature=self.temperature,
            #     )
            response = self.client.chat.completions.create(
                response_model=self.response_model,
                messages=[{"role": "user", "content": self.prompt.format(**inputs)}],
                temperature=self.temperature,
            )
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
