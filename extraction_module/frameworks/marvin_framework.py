import os
from typing import Any

import marvin
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider

from langfuse import observe
from structured_output_kit.extraction_module.base import BaseFramework, experiment


class MarvinFramework(BaseFramework):
    '''
    https://ai.pydantic.dev/models/
    marvin의 task를 이용하여 structured data를 추출(https://askmarvin.ai/concepts/tasks)
    '''
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.provider == "openai":
            settings = OpenAIModelSettings(**self.extra_kwargs)
            self.llm = OpenAIModel(self.model, settings=settings)

        elif self.provider == "ollama":
            provider = OpenAIProvider(
                base_url=self.base_url,
                api_key=self.api_key or os.environ.get("OLLAMA_API_KEY", "dummy")
            )
            settings = OpenAIModelSettings(**self.extra_kwargs)
            self.llm = OpenAIModel(self.model, provider=provider, settings=settings)
        
        elif self.provider == "openai_compatible":
            provider = OpenAIProvider(
                base_url=self.base_url,
                api_key=self.api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY", "dummy")
            )
            settings = OpenAIModelSettings(**self.extra_kwargs)
            self.llm = OpenAIModel(self.model, provider=provider, settings=settings)

        elif self.provider == "google":
            provider = GoogleProvider(api_key=os.getenv("GOOGLE_API_KEY"))
            settings = GoogleModelSettings(**self.extra_kwargs)
            self.llm = GoogleModel(self.model, 
                                     provider=provider,
                                      settings=settings)

        elif self.provider == "anthropic":
            provider = AnthropicProvider(api_key=os.getenv("ANTHROPIC_API_KEY"))
            settings = AnthropicModelSettings(**self.extra_kwargs)
            self.llm = AnthropicModel(self.model, provider=provider, settings=settings)

        self.client = marvin.Agent(model=self.llm)
        
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