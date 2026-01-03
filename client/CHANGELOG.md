# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-01-03

### Added
- Comprehensive installation troubleshooting documentation
- `INSTALLATION_TROUBLESHOOTING.md` - Complete guide for PATH issues
- `QUICK_FIX.md` - Quick reference for common installation problems
- `docs/INSTALLATION_ISSUES_EXPLAINED.md` - Technical deep-dive
- `USER_MESSAGE_TEMPLATE.md` - Support response templates
- PATH troubleshooting section in README
- pipx installation recommendation
- Enhanced CLI help with troubleshooting hints

### Changed
- Updated package description to include installation instructions
- Improved help text with `python -m` workaround
- Updated PUBLISHING.md with PATH issue notes

### Documentation
- Documented root cause of "telos is unrecognized" error (PATH configuration)
- Added multiple solutions: python -m, PATH modification, pipx
- Platform-specific installation guides (Windows/Mac/Linux)

## [0.1.2] - 2026-01-03

### Added
- `telos --version` command to check installed version
- Headless environment detection with helpful error message

### Fixed
- Error when running `telos --version` in headless environments
- Better error messaging for users trying to run TUI without display

### Changed
- Help text now shows version number and clearer usage instructions

## [0.1.1] - 2026-01-03

### Fixed
- Import error when running `telos` command after pip install
- API key validation now respects backend mode

### Changed
- **SaaS-first setup**: Backend mode is now the default (no API key needed)
- Setup wizard now offers choice between SaaS mode and local mode
- API key only required in local mode
- Better import fallback logic for pip-installed package

## [0.1.0] - 2026-01-03

### Added
- Initial PyPI release
- `pip install telos-tracker` support
- User data directory at `~/.telos/`
- Interactive setup wizard (`telos setup`)
- Automatic config and prompt initialization
- Cross-platform support (Windows, macOS, Linux)

### Features
- AI-powered screen time tracking with Gemini Vision
- Terminal UI with real-time dashboard
- Smart session building and analysis
- AI chat interface for querying work patterns
- Daily email reports via Gmail
- Background service/daemon mode
- Privacy-first: all data stored locally

### Technical
- Python 3.8+ support
- Modern packaging with `pyproject.toml`
- CLI entry point with user directory handling
- Bundled prompts and configuration templates

## Planned Features

### Future Versions
- Cross-device sync
- Team features
- Advanced analytics
- Package restructuring (move core/tui/utils under telos_tracker namespace)

