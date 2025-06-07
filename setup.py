from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setup(
    name="tjrn_api",
    version="0.1.0",
    packages=find_packages(include=['app*']),
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'tjrn-scraper=app.scripts.run_scraper:main',
        ],
    },
    package_data={
        'app': ['data/*.json'],
    },
    python_requires='>=3.8',
)
