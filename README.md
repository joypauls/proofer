[![python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org)
[![PyPI version](https://badge.fury.io/py/proofer.svg)](https://badge.fury.io/py/proofer)

# proofer

A minimal, CLI-based agent built with LangGraph for proofreading and editing short-form writing like blog posts. Displays a helpful git-like diff with suggestions and the option to automatically apply changes with backups.

![Usage Screenshot](./docs/images/screenshot.png)

## User Guide

### OpenAI API Key

For most tasks this library uses OpenAI API's so you'll need to set the `OPENAI_API_KEY` environment variable. An easy way to do this is to put this line:

```
export OPENAI_API_KEY=<your key>
```

in your `.zshrc` file or whichever configuration file your setup uses.

### Install

Available on PyPI (i.e. `pip install proofer`)

### Usage

Either pass in the path to a file (works best with markdown or plain text documents)

```
proofer file.md
```

or some text directly

```
proofer -t "Some text with spelking errors"
```

_Note: The intent of this project is to support short-form writing (<1500 words or so). It will struggle with longer documents, which might be addressed in a future release._

#### Auto-Apply Changes

If you want to live dangerously, you can auto-apply changes identified like so:

```
proofer file.md --yes
```

## Development

This project currently requires Python 3.13 ([pyenv](https://realpython.com/intro-to-pyenv/) is recommended) and uses Poetry as the dependency manager and packaging tool.

For now, checkout the `Makefile` as a guide.

| Command      | Description              |
| ------------ | ------------------------ |
| make install | Install all dependencies |
| make test    | Run unit tests           |
