"""
Setup script for AI Terminal
"""

from setuptools import setup, find_packages

setup(
    name="aiterm",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai>=0.27.0",
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "aiterm=aiterm.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered terminal application",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aiterm",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
)
