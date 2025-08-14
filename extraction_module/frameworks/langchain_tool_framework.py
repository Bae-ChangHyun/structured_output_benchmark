import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

from structured_output_benchmark.extraction_module.base import BaseFramework, experiment
from typing import Any
from langfuse import observe

class LangchainToolFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        if self.llm_host == "openai":
            self.llm = ChatOpenAI(model=self.llm_model,max_retries=0, **self.extra_kwargs)

        elif self.llm_host == "ollama" or self.llm_host == "vllm":
            self.llm = ChatOpenAI(model=self.llm_model,
                                  base_url=self.base_url,
                                  api_key="dummy",
                                  max_retries=0, **self.extra_kwargs)
            
        elif self.llm_host == "google":
            self.llm = ChatGoogleGenerativeAI(model=self.llm_model,
                                              google_api_key=os.environ.get("GOOGLE_API_KEY"),
                                              max_retries=0,  **self.extra_kwargs)
        
        elif self.llm_host == "anthropic":
            self.llm = ChatAnthropic(model=self.llm_model,max_retries=0,  **self.extra_kwargs)

        self.structured_llm = self.llm.with_structured_output(self.response_model)

    @observe(name='LangchainTool Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, list[float]]:
        @experiment(retries=retries)
        def run_experiment(inputs):

            prompt = ChatPromptTemplate.from_messages([
                ("user", self.prompt)
            ])

            chain = prompt | self.structured_llm

            response = chain.invoke(inputs) 
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies
