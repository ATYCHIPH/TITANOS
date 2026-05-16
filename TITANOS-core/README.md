# TITANOS

[![PyPI Version](https://img.shields.io/pypi/v/titanos-core.svg)](https://pypi.org/project/titanos-core/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/titanos/titanos-core/actions/workflows/ci.yml/badge.svg)](https://github.com/titanos/titanos-core/actions)

TITANOS is a robust, cross-platform agentic framework. It combines a sophisticated reasoning engine with flexible body-system contracts to enable autonomous, secure AI operations across Windows, macOS, and Linux.

## Features
- **Cross-Platform**: Run consistently on any major OS.
- **Secure by Default**: JWT authentication, TLS encryption, and secure shell execution.
- **API First**: Exposes operations via a modern FastAPI backend.
- **Extensible Body Systems**: Add new adapters for specialized environments.

## Installation

You can install TITANOS directly from PyPI:

```bash
pip install titanos-core
```

Or run it via Docker:

```bash
docker run -p 8000:8000 ghcr.io/titanos/titanos-core:latest
```

## Quick Start

Initialize your TITANOS environment:
```bash
titanos init
```

Start the TITANOS operator API server in development mode:
```bash
titanos dev
```

Start the production server with TLS:
```bash
titanos serve
```

## Documentation

Full API reference and advanced usage guides can be found at [TITANOS Documentation](https://titanos.github.io/titanos-core).

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on our coding standards and how to submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
