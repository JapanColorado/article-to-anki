# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2025-01-27

### Added
- `--model` command line argument to specify OpenAI model (default: gpt-4o-mini)
- Support for using different OpenAI models like gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- Model parameter propagated to both card generation and fallback text extraction

### Improved
- Enhanced card generation prompt to intelligently select optimal format (cloze vs basic) for each concept
- Eliminated redundancy between cloze and basic cards by choosing the best format for each idea
- Updated package description to reflect intelligent card format selection approach
- Updated default model from gpt-4.1-mini to gpt-4o-mini for better performance

## [0.2.1] - 2025-01-27

### Fixed
- Fixed --url-files path resolution to work from any directory
- Fixed tool failing when run from articles/ directory
- Improved error messages with detailed path search information
- Enhanced file discovery to check multiple common locations

### Changed
- Tool now works regardless of current working directory
- Better help text explaining file path resolution behavior

## [0.2.0] - 2025-01-27

### Added
- `--url-files` option to process URLs from multiple organized files
- Enhanced error handling for missing URL files
- Better organization support for topic-based, priority-based, or source-based URL management
- Improved README with comprehensive examples and troubleshooting

### Changed
- Updated project structure and cleaned up repository for PyPI release

## [0.1.0] - 2025-01-27

### Added
- Initial release
- Core functionality for generating Anki cards from articles
- Support for URLs and local files (PDF, EPUB, DOCX, TXT, etc.)
- Smart duplicate detection with semantic similarity
- AnkiConnect integration for direct card export
- Custom prompts and flexible configuration
- Setup and troubleshooting utilities
