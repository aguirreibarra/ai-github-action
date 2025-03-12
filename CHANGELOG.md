# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Consistent structured outputs
- PR Review action can choose between commenting, requesting changes, or approve PRs.
- Introduced `max-turns` parameter.

### Changed
- Refactored codebase to integrate openai-agents-sdk

### Removed
- Removed the `auto-approval` input. The agents will aprove PRs if they consider them approvable.
- Removed the `max-files`, `include-patterns` and `exclude-patterns` inputs. They were removed at the moment for easier integration with OpenAI agents SDK.

## [1.1.0] - 2025-03-09

### Added
- Comprehensive unit tests for PR review action functionality
- Direct issue creation in code scan action instead of returning output data

### Changed
- Improved file prioritization in PR review action - files are now sorted by number of changes
- Enhanced section parsing logic for more robust extraction of review content
- Added better error handling for individual file processing in PR reviews
- Improved logging for PR review process
- Completely redesigned auto-approval mechanism to use direct tool calls instead of text parsing
- Updated GitHub agent to properly capture and return tool calls information
- Changed action methods to return None instead of dictionaries with output data
- Simplified workflow examples by removing unnecessary output handling

### Removed
- Removed outputs section from action.yml
- Removed detailed output parsing in PR reviews, issue analysis and code scan actions
- Removed complex output formatting logic in main.py

### Fixed
- Fixed potential issues with files exceeding max_files limit
- Fixed section detection in AI responses that could miss certain section headers
- Fixed reliability issues with PR auto-approval by moving to a direct tool call approach

## [1.0.0] - Initial Release

### Added
- Pull Request review action
- Issue analyze action
- Code scan action
- GitHub tools for interacting with repository, PRs, and issues
- OpenAI integration for AI-powered code reviews
- Configurable file patterns for inclusion/exclusion
- Auto-approve functionality for favorable reviews