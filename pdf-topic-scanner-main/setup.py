from setuptools import setup, find_packages

setup(
    name="pdf-topic-scanner",
    version="0.0.1",
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "streamlit>=1.0",
        "pdfplumber>=0.5",
    ],
    author="",
    description="Prototype project for scanning PDF topics and building hierarchies.",
)
