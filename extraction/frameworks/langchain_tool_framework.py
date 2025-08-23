import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langfuse import observe
from structured_output_kit.extraction.base import BaseFramework, experiment


class LangchainToolFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
        if self.provider == "openai":
            self.llm = ChatOpenAI(model=self.model,max_retries=0, **self.extra_kwargs)

        elif self.provider == "ollama":
            self.llm = ChatOpenAI(model=self.model,
                                  base_url=self.base_url,
                                  api_key=self.api_key or os.getenv("OLLAMA_API_KEY", "dummy"),
                                  max_retries=0, **self.extra_kwargs)

        elif self.provider == "openai_compatible":
            self.llm = ChatOpenAI(model=self.model,
                                  base_url=self.base_url,
                                  api_key=self.api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
                                  max_retries=0, **self.extra_kwargs)

        elif self.provider == "google":
            self.llm = ChatGoogleGenerativeAI(model=self.model,
                                              google_api_key=os.environ.get("GOOGLE_API_KEY"),
                                              max_retries=0,  **self.extra_kwargs)
        
        elif self.provider == "anthropic":
            self.llm = ChatAnthropic(model=self.model,max_retries=0,  **self.extra_kwargs)

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
