from typing import Any

from structured_output_kit.extraction.frameworks.openai_framework import OpenAIFramework
from structured_output_kit.extraction.frameworks.instructor_framework import InstructorFramework
from structured_output_kit.extraction.frameworks.langchain_tool_framework import LangchainToolFramework
from structured_output_kit.extraction.frameworks.langchain_parser_framework import LangchainParserFramework
from structured_output_kit.extraction.frameworks.mirascope_framework import MirascopeFramework
from structured_output_kit.extraction.frameworks.llamaindex_framework import LlamaIndexFramework
from structured_output_kit.extraction.frameworks.marvin_framework import MarvinFramework
from structured_output_kit.extraction.frameworks.ollama_framework import OllamaFramework
from structured_output_kit.extraction.frameworks.google_framework import GoogleFramework
from structured_output_kit.extraction.frameworks.lm_format_enforcer_framework import LMFormatEnforcerFramework
from structured_output_kit.extraction.frameworks.anthropic_framework import AnthropicFramework


def factory(class_name: str, *args, **kwargs) -> Any:
    frameworks = {
        "OpenAIFramework": OpenAIFramework,
        "InstructorFramework": InstructorFramework,
        "LangchainToolFramework": LangchainToolFramework,
        "LangchainParserFramework": LangchainParserFramework,
        "MirascopeFramework": MirascopeFramework,
        "LlamaIndexFramework": LlamaIndexFramework,
        "MarvinFramework": MarvinFramework,
        "OllamaFramework": OllamaFramework,
        "GoogleFramework": GoogleFramework,
        "LMFormatEnforcerFramework": LMFormatEnforcerFramework,
        "AnthropicFramework": AnthropicFramework,
    }
    try:
        cls = frameworks[class_name]
    except KeyError as e:
        raise ValueError(f"Invalid class name: {class_name}. Available frameworks: {list(frameworks.keys())}") from e
    return cls(*args, **kwargs)
