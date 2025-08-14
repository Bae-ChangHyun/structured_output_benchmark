from typing import Any

from structured_output_benchmark.extraction_module.base import BaseFramework
from structured_output_benchmark.extraction_module.frameworks.openai_framework import OpenAIFramework
from structured_output_benchmark.extraction_module.frameworks.instructor_framework import InstructorFramework
from structured_output_benchmark.extraction_module.frameworks.langchain_tool_framework import LangchainToolFramework
from structured_output_benchmark.extraction_module.frameworks.langchain_parser_framework import LangchainParserFramework
from structured_output_benchmark.extraction_module.frameworks.mirascope_framework import MirascopeFramework
from structured_output_benchmark.extraction_module.frameworks.llamaindex_framework import LlamaIndexFramework
from structured_output_benchmark.extraction_module.frameworks.marvin_framework import MarvinFramework
from structured_output_benchmark.extraction_module.frameworks.ollama_framework import OllamaFramework
from structured_output_benchmark.extraction_module.frameworks.google_framework import GoogleFramework
from structured_output_benchmark.extraction_module.frameworks.lm_format_enforcer_framework import LMFormatEnforcerFramework
from structured_output_benchmark.extraction_module.frameworks.anthropic_framework import AnthropicFramework



def factory(class_name: str, *args, **kwargs) -> Any:
    """Factory function to create an instance of a framework class

    Args:
        class_name (str): name of the class to instantiate

    Raises:
        ValueError: If the class name is not found in the globals

    Returns:
        Any: An object of the requested framework class
    """
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
        "AnthropicFramework": AnthropicFramework
    }
    
    if class_name in frameworks:
        return frameworks[class_name](*args, **kwargs)
    else:
        raise ValueError(f"Invalid class name: {class_name}. Available frameworks: {list(frameworks.keys())}")
