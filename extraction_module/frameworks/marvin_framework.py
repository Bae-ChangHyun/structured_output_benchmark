import os
from typing import Any

import marvin
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider


from langfuse import observe
from extraction_module.base import BaseFramework, experiment


class MarvinFramework(BaseFramework):
    '''
    https://ai.pydantic.dev/models/
    marvin의 task를 이용하여 structured data를 추출(https://askmarvin.ai/concepts/tasks)
    '''
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.llm_provider == "openai":
            self.model = OpenAIModel(self.llm_model)    
            
        elif self.llm_provider == "ollama" or self.llm_provider == "vllm":
            provider = OpenAIProvider(
                base_url=self.base_url,
                api_key='dummmy'
            )
            self.model = OpenAIModel(self.llm_model, provider=provider)
            
        elif self.llm_provider == "google":
            provider = GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY"))
            settings = GoogleModelSettings(
                temperature=self.temperature,
                timeout=self.timeout
            )
            self.model = GoogleModel(self.llm_model, 
                                     provider=provider,
                                      settings=settings)

        elif self.llm_provider == "anthropic":
            provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = AnthropicModel(self.llm_model)

        self.client = marvin.Agent(model=self.model)
        
    @observe(name='Marvin Framework')
    def run(
        self, retries: int, inputs: dict = {}
    ) -> tuple[list[Any], float, dict, list[list[float]]]:
        @experiment(retries=retries)
        def run_experiment(inputs):
            response = self.client.run(self.prompt.format(**inputs), result_type=self.response_model)
            return response

        predictions, percent_successful, latencies = run_experiment(inputs)
        return predictions, percent_successful, latencies