import os
from pyexpat import model
from typing import Any
from loguru import logger

from llama_index.llms.openai import OpenAI
from llama_index.llms.openai_like import OpenAILike
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.program import LLMTextCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser

from langfuse import observe
from extraction_module.base import BaseFramework, experiment


class LlamaIndexFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        if self.llm_provider == "openai":
            self.client = OpenAI(model=self.llm_model,
                                 temperature=self.temperature,
                                 max_retries=0,
                                 timeout=self.timeout)

        elif self.llm_provider == "ollama" or self.llm_provider == "vllm":
            self.client = OpenAILike(
                api_base=self.base_url,
                api_key="dummy",
                model=self.llm_model,
                #max_tokens=16384,  #!TODO: 하드코딩,
                timeout=self.timeout,
                temperature=self.temperature,
                max_retries=0, 
            )
            
        elif self.llm_provider == "google":
            self.client = GoogleGenAI(
                #api_base=self.base_url,
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=self.llm_model,
                temperature=self.temperature,
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

            response = self.llamaindex_client(**inputs)
            
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
