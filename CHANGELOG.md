# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
