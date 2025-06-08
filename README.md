# Jaiger

## Overview

`Jaiger` is a modular, extensible Python framework for developing AI-based applications. It provides an easy way to develop and orchestrate high performance AI applications.

---

## Features

- **Developer-friendly Tool Interface**  
  - The `Tool` interface is simple and easy to use.
  - Develop and test your AI Tool quickly and easily.

- **Schema-less Tool**
  - No schema definition needed for your tool functions.
  - Jaeger automatically infers your function's schema through type hints and docstrings.

- **Pydantic Support**  
  - You can use `pydantic` models for type hinting.

- **Tools as Processes**  
  - Each tool runs in its own process.
  - Makes developing CPU-intensive tools feasible.

---

## Getting Started

### Prerequisites

- Python 3.8+  
- Git  

### Installation

```bash
git clone https://github.com/hanstjua/jaiger.git
cd jaiger
pip install -e .
```

---

## Motivation

Jaiger is my attempt to gain better understanding of how the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) could be implemented. While there are significant differences between the actual implementation of Jaiger and the MCP, both makes it easier to (1) develop LLM-compatible tools and (2) utilize said tools to build AI-powered applications.