# Video Generator API

A modular platform for automatic video generation, based on a highly customizable **pipeline** and **step** architecture.

## Overview

This project organizes video creation into logical and independent steps, making it easy to combine features like:

- Animated caption generation
- Automatic narration (TTS)
- Visual composition with images, backgrounds, and effects
- Final video export

Each pipeline allows different combinations of steps to create videos such as interactive quizzes or visual fun facts.

## Environment Setup

Before running the project, configure the environment variable:

```bash
export PYTHONPATH={yourPath}/video-generator-api/src
```

Replace `{yourPath}` with the absolute path to the `src` directory of the project.

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Available Examples

- **Quiz Pipeline**: generates an animated video with one question and four answer choices.
- **Fun Facts Pipeline**: creates a fun facts video with an image, title, and narration.

## Running the Pipelines

To run the fun facts pipeline:

```python
from fun_facts.fun_facts_pipeline import pipeline_fun_fact
pipeline_fun_fact.execute({})
```

To run the quiz pipeline:

```python
from quiz.quiz_pipeline import pipeline
pipeline.execute({})
```

## License

This project is licensed under the MIT License.

Developed by **Rafael Marotta** (rafaelmarottag@gmail.com) as part of the undergraduate thesis (TCC) at **PUC Minas**.

