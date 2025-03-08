# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Comprehensive unit tests for PR review action functionality

### Changed
- Improved file prioritization in PR review action - files are now sorted by number of changes
- Enhanced section parsing logic for more robust extraction of review content
- Added better error handling for individual file processing in PR reviews
- Improved logging for PR review process

### Fixed
- Fixed potential issues with files exceeding max_files limit
- Fixed section detection in AI responses that could miss certain section headers

## [1.0.0] - Initial Release

### Added
- Pull Request review action
- Issue analyze action
- Code scan action
- GitHub tools for interacting with repository, PRs, and issues
- OpenAI integration for AI-powered code reviews
- Configurable file patterns for inclusion/exclusion
- Auto-approve functionality for favorable reviews