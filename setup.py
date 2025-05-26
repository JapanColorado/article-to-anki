from setuptools import setup, find_packages

setup(
    name="articles-to-anki",
    version="0.1.0",
    description="A tool to generate Anki flashcards from articles using GPT-4.",
    author="japancolorado",
    author_email="japancolorado@duck.com",
    packages=find_packages(),
    install_requires=[
        "openai",
        "requests",
        "tqdm",
        "beautifulsoup4",
        "readability-lxml",
        "pymupdf"
    ],
    # Dependencies for the advanced similarity features
    extras_require={
        "advanced_similarity": ["scikit-learn>=0.24.0", "nltk>=3.7.0"],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "articles-to-anki=articles_to_anki.cli:main",
            "articles-to-anki-setup=articles_to_anki.setup_app:main",
            "articles-to-anki-fix-nltk=articles_to_anki.fix_nltk:fix_nltk_issues",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", ".processed_articles.json", ".card_database.json", "text_utils.py", "fix_nltk.py"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
