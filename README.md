# Newton Architect

**Newton Architect** is an AI-powered physics simulation engine that leverages Google's Gemini models to generate, validate, and visualize physics concepts. This repository contains the core logic and execution engine.

## Overview

The engine is designed to:
- **Ingest Physics Knowledge**: Process and structure physics formulas and concepts.
- **Generate Simulations**: Use Large Language Models (LLMs) to create Manim-based visualizations.
- **Validate Outputs**: Automatically check the correctness of generated code and visual outputs.

## Architecture

The system is organized into several key modules:
- **`src/core`**: Configuration and base utilities.
- **`src/knowledge`**: Modules for ingesting and managing physics knowledge graphs.
- **`src/execution`**: The runtime engine for generating and running simulations.
- **`src/graph`**: Graph-based state management for the simulation workflows.
- **`src/api`**: FastAPI endpoints for interacting with the engine.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

### Prerequisites
- Python 3.11+
- Poetry

### Steps

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Install dependencies:**
    ```bash
    poetry install
    ```

3.  **Environment Setup:**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

## Usage

To run the main execution pipeline (example):

```bash
poetry run python src/main.py
```

To run the validators or batch processes, refer to the scripts in `src/execution`.

## Contributing

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

[MIT](LICENSE)
