"""Base LLM provider interface.

Defines the abstract interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, config: Dict[str, Any]):
        """Initialize the LLM provider.

        Args:
            api_key: API key for the LLM service
            config: Provider-specific configuration
        """
        self.api_key = api_key
        self.config = config
        self.model = config.get("model", "")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text based on the given prompt.

        Args:
            prompt: User prompt to send to the LLM
            system_prompt: Optional system prompt to guide the LLM

        Returns:
            Generated text response

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def generate_code(
        self,
        description: str,
        file_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate code based on description and type.

        Args:
            description: Description of what the code should do
            file_type: Type of file to generate (e.g., 'php', 'css', 'js')
            context: Additional context for code generation

        Returns:
            Generated code as string

        Raises:
            Exception: If code generation fails
        """
        pass

    @abstractmethod
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze user prompt to extract requirements.

        Args:
            prompt: Natural language description of the website

        Returns:
            Dictionary containing extracted requirements:
                - theme_name: str
                - description: str
                - features: List[str]
                - color_scheme: str
                - pages: List[str]
                - etc.

        Raises:
            Exception: If analysis fails
        """
        pass

    def validate_api_key(self) -> bool:
        """Validate that the API key is set and not empty.

        Returns:
            True if API key is valid, False otherwise
        """
        return bool(self.api_key and self.api_key.strip())
