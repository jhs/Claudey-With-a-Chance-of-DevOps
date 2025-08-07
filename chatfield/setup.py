from setuptools import setup, find_packages

setup(
    name="chatfield",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ]
    },
    python_requires=">=3.8",
)