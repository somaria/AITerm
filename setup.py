"""Setup script for AITerm."""

from setuptools import setup, find_packages

setup(
    name="aiterm",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic>=2.0.0",
        "openai>=0.28.1,<1.0.0",
        "python-dotenv==1.0.0",
    ],
    extras_require={
        "macos": ["pyobjc-framework-Cocoa>=9.0"],
    },
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'aiterm=aiterm.main:main',
        ],
    },
)
