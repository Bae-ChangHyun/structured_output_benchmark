import os
from typing import Any

from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser

from langfuse import observe
from structured_output_kit.extraction.base import BaseFramework, experiment


class LlamaIndexFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        if self.provider == "openai":
            self.client = OpenAI(model=self.model,max_retries=0,)

        elif self.provider == "ollama":
            self.client = OpenAILike(
                api_base=self.base_url,
                api_key=self.api_key or os.getenv("OLLAMA_API_KEY", "dummy"),
                model=self.model,
                max_retries=0, 
            )

        elif self.provider == "openai_compatible":
            self.client = OpenAILike(
                api_base=self.base_url,
                api_key=self.api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                model=self.model,
                max_retries=0, 
            )
            
        elif self.provider == "google":
            self.client = GoogleGenAI(
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=self.model,
                max_retries=0,
            )
        
        self.llamaindex_client = LLMTextCompletionProgram.from_defaults(
            output_parser=PydanticOutputParser(self.response_model),
            prompt_template_str=self.prompt,
            llm=self.client,
        )
    @observe(name='Llamaindex Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):

            response = self.llamaindex_client(llm_kwargs=self.extra_kwargs, **inputs)

            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
