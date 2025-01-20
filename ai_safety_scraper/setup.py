from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="ai_safety_scraper",
    version="0.1.0",
    packages=find_packages(),
    install_requires=requirements,
    author="AI Safety Research Team",
    description="A tool for scraping and analyzing AI safety related content",
    python_requires=">=3.6",
    include_package_data=True,
    package_data={
        "ai_safety_scraper": ["data/*"]
    }
) 