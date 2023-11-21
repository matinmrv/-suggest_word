# FastAPI Masked Word Suggestion

FastAPI-based web service for suggesting words in masked sentences and completing sentences based on user selection.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
  - [Word Suggestion](#word-suggestion)
  - [Sentence Completion](#sentence-completion)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
  - [Word Suggestion](#word-suggestion-usage)
  - [Sentence Completion](#sentence-completion-usage)


## Introduction

This FastAPI application provides two main functionalities: suggesting words for masked sentences and completing sentences based on user selection. It uses a pre-trained masked language model from the Hugging Face Transformers library.

## Features

### Word Suggestion

Given an input sentence with a masked token (e.g., "Elon Musk is the founder of [MASK]"), the service suggests possible words to complete the sentence.

### Sentence Completion

After receiving word suggestions, the user can select a word, and the service completes the original sentence by replacing the masked token.

## Getting Started

### Prerequisites

Ensure you have Python and pip installed. Additionally, set up a PostgreSQL database and provide the necessary environment variables.

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/matinmrv/-suggestword.git
    cd yourrepository
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the FastAPI application:

    ```bash
    uvicorn app:app --reload
    ```

## Usage

1. ### Access the Swagger documentation:

   Open your browser and go to http://127.0.0.1:8000/docs to interact with the API using the Swagger UI.

2. ### Test the API:

   Use the provided endpoints to suggest words and complete sentences.

### Word Suggestion Usage

Send a POST request to `/suggest_word` with a JSON payload:

```json
{
  "sequence": "Elon Musk is the founder of [MASK]"
}
```
The response will contain suggested words.
### Sentence Completion Usage

1. After obtaining word suggestions, send a POST request to /select_word with the selected word ID:
Send a POST request to `/select_word`:

```json
{
  "selected_word_id": 1
}
```
2. The response will contain the completed sentence.



## Thanks for your time:>
