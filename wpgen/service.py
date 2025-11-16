"""Unified service layer for WordPress theme generation.

This module provides a centralized, high-level API for theme generation
that can be used by CLI, Gradio UI, and Flask web UI. It handles the
complete pipeline from prompt to deployed theme.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .generators import WordPressGenerator
from .github import GitHubIntegration
from .parsers import PromptParser
from .utils import get_llm_provider, get_logger
from .utils.image_analysis import ImageAnalyzer
from .utils.text_utils import TextProcessor
from .wordpress import WordPressAPI
from .design_profiles import get_design_profile, get_profile_names

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_LMSTUDIO = "local-lmstudio"
    LOCAL_OLLAMA = "local-ollama"


class GenerationRequest(BaseModel):
    """Request model for theme generation."""

    # Core input
    prompt: str = Field(..., min_length=10, description="Natural language description of the WordPress site")

    # File inputs
    image_files: Optional[List[str]] = Field(default=None, description="Paths to design mockup images")
    text_files: Optional[List[str]] = Field(default=None, description="Paths to content documents (PDF, MD, TXT)")

    # LLM configuration
    llm_provider: Optional[LLMProvider] = Field(default=None, description="LLM provider to use")
    llm_model: Optional[str] = Field(default=None, description="Specific model name")
    llm_brains_model: Optional[str] = Field(default=None, description="Brains model for local LLMs")
    llm_brains_base_url: Optional[str] = Field(default=None, description="Brains model base URL")
    llm_vision_model: Optional[str] = Field(default=None, description="Vision model for local LLMs")
    llm_vision_base_url: Optional[str] = Field(default=None, description="Vision model base URL")

    # Guided mode parameters
    guided_mode: Optional[Dict[str, Any]] = Field(default=None, description="Structured theme configuration")

    # Design profile
    design_profile: Optional[str] = Field(default=None, description="Design profile (streetwear_modern, minimalist, corporate, vibrant_bold, earthy_natural, bold_neon, dark_mode)")

    # Optional features
    optional_features: Optional[Dict[str, Any]] = Field(default=None, description="Optional theme features")

    # Output configuration
    output_dir: Optional[str] = Field(default=None, description="Output directory for generated theme")

    # GitHub integration
    push_to_github: bool = Field(default=False, description="Push theme to GitHub")
    github_repo_name: Optional[str] = Field(default=None, description="GitHub repository name")

    # WordPress deployment
    deploy_to_wordpress: bool = Field(default=False, description="Deploy theme to WordPress site")
    wordpress_activate: bool = Field(default=True, description="Activate theme after deployment")

    # Validation options
    strict_validation: bool = Field(default=False, description="Fail on validation warnings")

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Ensure prompt is not empty."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class GenerationResult(BaseModel):
    """Result model for theme generation."""

    success: bool = Field(..., description="Whether generation succeeded")
    theme_dir: Optional[str] = Field(default=None, description="Path to generated theme directory")
    theme_name: str = Field(..., description="Generated theme name")
    theme_display_name: str = Field(..., description="Theme display name")
    description: str = Field(..., description="Theme description")
    features: List[str] = Field(default_factory=list, description="Theme features")

    # GitHub information
    github_url: Optional[str] = Field(default=None, description="GitHub repository URL")

    # WordPress information
    wordpress_deployed: bool = Field(default=False, description="Whether theme was deployed to WordPress")
    wordpress_activated: bool = Field(default=False, description="Whether theme was activated")
    wordpress_theme_id: Optional[str] = Field(default=None, description="WordPress theme ID")

    # Validation results
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")

    # Error information
    error: Optional[str] = Field(default=None, description="Error message if generation failed")
    error_details: Optional[str] = Field(default=None, description="Detailed error information")


class ThemeGenerationService:
    """Service for generating WordPress themes."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the theme generation service.

        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.logger = logger

    def generate_theme(self, request: GenerationRequest) -> GenerationResult:
        """Generate a WordPress theme from a request.

        Args:
            request: Generation request with all parameters

        Returns:
            GenerationResult with theme information and status
        """
        try:
            self.logger.info("Starting theme generation")
            self.logger.debug(f"Request: {request.model_dump()}")

            # Apply request overrides to config
            cfg = self._apply_request_overrides(request)

            # Initialize LLM provider
            llm_provider = get_llm_provider(cfg)
            provider_name = cfg.get("llm", {}).get("provider", "openai")
            self.logger.info(f"Initialized LLM provider: {provider_name}")

            # Process images and documents if provided
            enhanced_prompt = self._enhance_prompt(request, llm_provider)

            # Parse prompt to extract requirements
            self.logger.info("Parsing prompt to extract requirements")
            parser = PromptParser(llm_provider)
            requirements = parser.parse(enhanced_prompt)

            self.logger.info(f"Theme: {requirements['theme_display_name']}")
            self.logger.info(f"Features: {', '.join(requirements.get('features', []))}")

            # Apply design profile if provided
            if request.design_profile:
                requirements = self._apply_design_profile(requirements, request.design_profile)

            # Apply guided mode overrides if provided
            if request.guided_mode:
                requirements = self._apply_guided_mode(requirements, request.guided_mode)

            # Apply optional features if provided
            if request.optional_features:
                requirements = self._apply_optional_features(requirements, request.optional_features)

            # Generate theme
            self.logger.info("Generating WordPress theme files")
            output_dir = request.output_dir or cfg.get("output", {}).get("output_dir", "output")
            generator = WordPressGenerator(llm_provider, output_dir, cfg.get("wordpress", {}))
            theme_dir = generator.generate(requirements)

            self.logger.info(f"Theme generated: {theme_dir}")

            # Initialize result
            result = GenerationResult(
                success=True,
                theme_dir=str(theme_dir),
                theme_name=requirements.get("theme_name", "unknown"),
                theme_display_name=requirements.get("theme_display_name", "Unknown Theme"),
                description=requirements.get("description", ""),
                features=requirements.get("features", []),
            )

            # Validate theme
            validation_result = self._validate_theme(theme_dir, request.strict_validation)
            result.validation_errors = validation_result.get("errors", [])
            result.validation_warnings = validation_result.get("warnings", [])

            # Check if validation should fail the build
            if request.strict_validation and (result.validation_errors or result.validation_warnings):
                result.success = False
                result.error = "Theme validation failed in strict mode"
                result.error_details = f"Errors: {len(result.validation_errors)}, Warnings: {len(result.validation_warnings)}"
                return result

            # Push to GitHub if requested
            if request.push_to_github:
                github_result = self._push_to_github(theme_dir, request, requirements, cfg)
                result.github_url = github_result.get("url")
                if not github_result.get("success"):
                    self.logger.warning(f"GitHub push failed: {github_result.get('error')}")

            # Deploy to WordPress if requested
            if request.deploy_to_wordpress:
                wp_result = self._deploy_to_wordpress(theme_dir, request, requirements, cfg)
                result.wordpress_deployed = wp_result.get("deployed", False)
                result.wordpress_activated = wp_result.get("activated", False)
                result.wordpress_theme_id = wp_result.get("theme_id")
                if not wp_result.get("success"):
                    self.logger.warning(f"WordPress deployment failed: {wp_result.get('error')}")

            self.logger.info("Theme generation completed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Theme generation failed: {e}", exc_info=True)
            return GenerationResult(
                success=False,
                theme_name="error",
                theme_display_name="Error",
                description="",
                error=str(e),
                error_details=repr(e),
            )

    def _apply_request_overrides(self, request: GenerationRequest) -> Dict[str, Any]:
        """Apply request parameters as overrides to config.

        Args:
            request: Generation request

        Returns:
            Modified configuration dictionary
        """
        cfg = self.config.copy()

        # Override LLM provider
        if request.llm_provider:
            if "llm" not in cfg:
                cfg["llm"] = {}
            cfg["llm"]["provider"] = request.llm_provider.value

        # Override LLM model
        if request.llm_model:
            if "llm" not in cfg:
                cfg["llm"] = {}
            cfg["llm"]["model"] = request.llm_model

        # Override local LLM models
        if request.llm_brains_model or request.llm_brains_base_url:
            provider = cfg.get("llm", {}).get("provider", "")
            if provider in ["local-lmstudio", "local-ollama"]:
                if provider not in cfg["llm"]:
                    cfg["llm"][provider] = {}
                if request.llm_brains_model:
                    cfg["llm"][provider]["brains_model"] = request.llm_brains_model
                if request.llm_brains_base_url:
                    cfg["llm"][provider]["brains_base_url"] = request.llm_brains_base_url

        if request.llm_vision_model or request.llm_vision_base_url:
            provider = cfg.get("llm", {}).get("provider", "")
            if provider in ["local-lmstudio", "local-ollama"]:
                if provider not in cfg["llm"]:
                    cfg["llm"][provider] = {}
                if request.llm_vision_model:
                    cfg["llm"][provider]["vision_model"] = request.llm_vision_model
                if request.llm_vision_base_url:
                    cfg["llm"][provider]["vision_base_url"] = request.llm_vision_base_url

        return cfg

    def _enhance_prompt(self, request: GenerationRequest, llm_provider) -> str:
        """Enhance prompt with image and document analysis.

        Args:
            request: Generation request
            llm_provider: LLM provider instance

        Returns:
            Enhanced prompt string
        """
        prompt = request.prompt

        # Analyze images if provided
        if request.image_files:
            self.logger.info(f"Analyzing {len(request.image_files)} images")
            try:
                analyzer = ImageAnalyzer(llm_provider)
                for image_path in request.image_files:
                    if Path(image_path).exists():
                        analysis = analyzer.analyze_design_mockup(image_path)
                        prompt += f"\n\nDesign Analysis:\n{analysis}"
            except Exception as e:
                self.logger.warning(f"Image analysis failed: {e}")

        # Process text documents if provided
        if request.text_files:
            self.logger.info(f"Processing {len(request.text_files)} documents")
            try:
                processor = TextProcessor()
                for text_path in request.text_files:
                    if Path(text_path).exists():
                        content = processor.extract_text(text_path)
                        prompt += f"\n\nDocument Content:\n{content[:2000]}"  # Limit to 2000 chars
            except Exception as e:
                self.logger.warning(f"Document processing failed: {e}")

        return prompt

    def _apply_design_profile(self, requirements: Dict[str, Any], profile_name: str) -> Dict[str, Any]:
        """Apply design profile to requirements.

        Args:
            requirements: Base requirements from parser
            profile_name: Name of the design profile to apply

        Returns:
            Modified requirements dictionary
        """
        self.logger.info(f"Applying design profile: {profile_name}")
        profile = get_design_profile(profile_name)
        requirements["design_profile"] = profile.to_dict()
        return requirements

    def _apply_guided_mode(self, requirements: Dict[str, Any], guided_mode: Dict[str, Any]) -> Dict[str, Any]:
        """Apply guided mode parameters to requirements.

        Args:
            requirements: Base requirements from parser
            guided_mode: Guided mode parameters

        Returns:
            Modified requirements dictionary
        """
        self.logger.info("Applying guided mode parameters")
        # Merge guided mode into requirements
        requirements["guided_mode"] = guided_mode
        return requirements

    def _apply_optional_features(self, requirements: Dict[str, Any], optional_features: Dict[str, Any]) -> Dict[str, Any]:
        """Apply optional features to requirements.

        Args:
            requirements: Base requirements
            optional_features: Optional features dict

        Returns:
            Modified requirements dictionary
        """
        self.logger.info(f"Applying optional features: {optional_features}")
        requirements["optional_features"] = optional_features
        return requirements

    def _validate_theme(self, theme_dir: str, strict: bool) -> Dict[str, Any]:
        """Validate generated theme.

        Args:
            theme_dir: Path to theme directory
            strict: Whether to use strict validation

        Returns:
            Dictionary with validation results
        """
        self.logger.info(f"Validating theme (strict={strict})")
        errors = []
        warnings = []

        try:
            from .utils.code_validator import CodeValidator
            from .utils.theme_validator import ThemeValidator

            # Validate code
            code_validator = CodeValidator(strict=strict)
            code_results = code_validator.validate_directory(theme_dir)
            errors.extend(code_results.get("errors", []))
            warnings.extend(code_results.get("warnings", []))

            # Validate theme structure
            theme_validator = ThemeValidator(strict=strict)
            theme_results = theme_validator.validate(theme_dir)
            errors.extend(theme_results.get("errors", []))
            warnings.extend(theme_results.get("warnings", []))

        except Exception as e:
            self.logger.warning(f"Validation failed: {e}")
            if strict:
                errors.append(f"Validation error: {str(e)}")
            else:
                warnings.append(f"Validation error: {str(e)}")

        return {"errors": errors, "warnings": warnings}

    def _push_to_github(self, theme_dir: str, request: GenerationRequest, requirements: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Push theme to GitHub.

        Args:
            theme_dir: Path to theme directory
            request: Generation request
            requirements: Theme requirements
            cfg: Configuration

        Returns:
            Dictionary with push results
        """
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            if not github_token:
                return {"success": False, "error": "GITHUB_TOKEN environment variable not set"}

            self.logger.info("Pushing theme to GitHub")
            github = GitHubIntegration(github_token, cfg.get("github", {}))

            repo_name = request.github_repo_name
            if not repo_name:
                repo_name = github.generate_repo_name(requirements["theme_name"])

            repo_url = github.push_to_github(theme_dir, repo_name, requirements)
            self.logger.info(f"Pushed to GitHub: {repo_url}")

            return {"success": True, "url": repo_url}

        except Exception as e:
            self.logger.error(f"GitHub push failed: {e}")
            return {"success": False, "error": str(e)}

    def _deploy_to_wordpress(self, theme_dir: str, request: GenerationRequest, requirements: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy theme to WordPress site.

        Args:
            theme_dir: Path to theme directory
            request: Generation request
            requirements: Theme requirements
            cfg: Configuration

        Returns:
            Dictionary with deployment results
        """
        try:
            wp_config = cfg.get("wordpress_api", {})
            site_url = os.getenv("WP_SITE_URL") or wp_config.get("site_url")
            username = os.getenv("WP_USERNAME") or wp_config.get("username")
            password = os.getenv("WP_APP_PASSWORD") or wp_config.get("app_password")

            if not all([site_url, username, password]):
                return {"success": False, "error": "WordPress credentials not configured"}

            self.logger.info(f"Deploying theme to WordPress: {site_url}")
            wp_api = WordPressAPI(site_url, username, password)

            # Test connection
            if not wp_api.test_connection():
                return {"success": False, "error": "WordPress connection test failed"}

            # Create theme ZIP
            from .utils.file_handler import FileHandler
            file_handler = FileHandler()
            zip_path = file_handler.create_zip(theme_dir)

            # Upload theme
            theme_id = wp_api.upload_theme(zip_path)
            self.logger.info(f"Theme uploaded: {theme_id}")

            # Activate if requested
            activated = False
            if request.wordpress_activate:
                wp_api.activate_theme(requirements["theme_name"])
                activated = True
                self.logger.info("Theme activated")

            return {
                "success": True,
                "deployed": True,
                "activated": activated,
                "theme_id": theme_id,
            }

        except Exception as e:
            self.logger.error(f"WordPress deployment failed: {e}")
            return {"success": False, "error": str(e)}


# Convenience function for simple usage
def generate_theme(config: Dict[str, Any], request: GenerationRequest) -> GenerationResult:
    """Generate a WordPress theme (convenience function).

    Args:
        config: Application configuration
        request: Generation request

    Returns:
        Generation result
    """
    service = ThemeGenerationService(config)
    return service.generate_theme(request)
