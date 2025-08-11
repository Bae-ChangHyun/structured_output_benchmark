from typing import List, Any

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langfuse import observe
from marvin.agents import team
from extraction_module.base import BaseFramework, experiment


class LangchainParserFramework(BaseFramework):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.llm_provider == "openai":
            self.llm = ChatOpenAI(model=self.llm_model,
                                  max_retries=0,
                                  temperature=self.temperature,
                                  timeout=self.timeout)

        elif self.llm_provider == "ollama":
            self.llm = ChatOllama(model=self.llm_model,
                                  base_url=self.base_url,
                                  api_key="dummy",
                                  temperature=self.temperature,
                                 )
            
        elif self.llm_provider == "vllm":
            self.llm = ChatOpenAI(model=self.llm_model,
                                  base_url=self.base_url,
                                  api_key="dummy",
                                  max_retries=0,
                                  timeout=self.timeout,
                                  temperature=self.temperature
                                  )
            
        elif self.llm_provider == "google":
            self.llm = ChatGoogleGenerativeAI(model=self.llm_model,
                                              max_retries=0,
                                              temperature=self.temperature)

        elif self.llm_provider == "anthropic":
            self.llm = ChatAnthropic(model=self.llm_model,
                                     max_retries=0,
                                     temperature=self.temperature,
                                     timeout=self.timeout)

        self.parser = PydanticOutputParser(pydantic_object=self.response_model)
        
    @observe(name='LangchainParser Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            
            prompt = ChatPromptTemplate.from_messages([
                ("user", self.prompt + "\n{format_instructions}")
            ])

            prompt = prompt.partial(format_instructions=self.parser.get_format_instructions())

            chain = prompt | self.llm | self.parser

            response = chain.invoke(inputs)
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies