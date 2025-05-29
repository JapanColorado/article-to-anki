# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-01-29

### Added
- `--overwrite` flag for automated file export without prompting
- `--to-file` export with smart file handling (overwrite, append, or create timestamped files)
- Comprehensive card cleanup system for malformed separators and formatting
- Automatic removal of title suffixes and redundant content from exported cards
- OpenAI free credits guide with data sharing instructions

### Improved
- **Major Card Generation Overhaul**: Enhanced cloze card generation to create multiple separate cards instead of single cards with many deletions
- Limited cloze cards to maximum 1-3 deletions per card for better learning effectiveness
- Updated prompt with explicit examples showing correct multi-card approach vs incorrect single-card approach
- Prioritized quality over quantity in card generation - removed rigid word count requirements
- Enhanced content filtering to avoid trivial details, specific examples, dates, names, and redundant concepts
- Added quality threshold guidance focusing on concepts worth remembering weeks later
- Improved anti-redundancy rules to prevent multiple cards testing the same knowledge
- Flexible card generation based on content richness rather than fixed ratios
- Enhanced card generation prompt with semicolon replacement instruction
- Robust card parsing that handles malformed input gracefully
- Better export file management with user choice prompts
- Significantly improved README organization and clarity (26% shorter, better structured)
- Accurate file organization documentation reflecting actual search behavior
- Empty card filtering and validation during export

### Fixed
- Card tagging to use title with underscores for both AnkiConnect and file export
- Malformed card separators (e.g., `; ; ;`) automatically cleaned up
- Punctuation conflicts in card content (semicolons replaced with commas)
- Export files now contain properly formatted cards instead of raw malformed content
- File export logic properly handles empty card lists
- Corrected README examples to show actual file location requirements (articles/ directory)

### Changed
- **BREAKING**: Changed multi-word CLI flags from underscores to hyphens for consistency:
  - `--use_cache` → `--use-cache`
  - `--to_file` → `--to-file`
  - `--custom_prompt` → `--custom-prompt`
  - `--allow_duplicates` → `--allow-duplicates`
  - `--process_all` → `--process-all`
  - `--similarity_threshold` → `--similarity-threshold`
- **BREAKING**: Dropped Python 3.8 support, now requires Python 3.9+
- Updated type annotations to use modern syntax (tuple[str, str] instead of Tuple[str, str])
- Updated README documentation to reflect new hyphenated flag names
- Export format is now cleaner with automatic malformed content cleanup
- File export provides three clear options: overwrite, append, or create new timestamped files
- Updated documentation to be more concise and better organized
- Improved model recommendations to include latest GPT-4.1 variants

## [0.3.0] - 2025-01-27

### Added
- `--model` command line argument to specify OpenAI model (default: gpt-4o-mini)
- Support for using different OpenAI models like gpt-4o, gpt-4-turbo, gpt-4.1 mini, gpt-4.1
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
