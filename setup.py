"""Setup configuration for wpgen - WordPress Theme Generator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements from requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith("#"):
                requirements.append(line)

setup(
    name="wpgen",
    version="1.0.0",
    author="WPGen Contributors",
    author_email="",
    description=(
        "AI-powered WordPress theme generator with multi-modal support and "
        "LLM-based site management"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/wpgen",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/wpgen/issues",
        "Source": "https://github.com/yourusername/wpgen",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wpgen=wpgen.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "wpgen": [
            "*.yaml",
            "*.yml",
            "*.json",
        ],
    },
    zip_safe=False,
    keywords=[
        "wordpress",
        "theme",
        "generator",
        "ai",
        "llm",
        "openai",
        "anthropic",
        "claude",
        "gpt-4",
        "multi-modal",
        "vision",
        "rest-api",
    ],
)
