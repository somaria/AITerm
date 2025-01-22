from setuptools import setup, find_packages

setup(
    name="aiterm",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai==0.28.1",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "aiterm=main:main",
        ],
    },
)
