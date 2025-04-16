from setuptools import setup, find_packages

setup(
    name="financial_planning",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'requests',
        'python-dotenv',
    ],
) 