# Video Generator API

A modular platform for automatic video generation, based on a highly customizable **pipeline** and **step** architecture.

## 📈 Overview

This project organizes video creation into logical and independent steps, making it easy to combine features like:

- ✨ Animated caption generation
- 🎧 Automatic narration (TTS)
- 🌈 Visual composition with images, backgrounds, effects, and animated progress bars
- 🎥 Final video export
- 📺 Automatic video upload to YouTube

Each pipeline allows different combinations of steps to create videos such as interactive quizzes or fun facts about countries.

---

## 🔧 Environment Setup

Before running the project, configure the environment variables:

```bash
export PYTHONPATH={yourPath}/video-generator-api/src
export GOOGLE_APPLICATION_CREDENTIALS={pathToYourCredentials}/credentials-speech.json
export GOOGLE_YOUTUBE_SECRETS={pathToYourCredentials}/client_secret_youtube.json
```

Replace `{yourPath}` and `{pathToYourCredentials}` with the absolute paths to your project directory and credentials.

---

## 📚 Installing Dependencies

Install all required dependencies:

```bash
pip install -r requirements.txt
```

---

## 💼 Google Cloud Credentials

### Text-to-Speech (TTS)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to **IAM & Admin** > **Service Accounts**.
4. Create a new service account and assign the role **"Text-to-Speech API User"**.
5. Generate a new key in JSON format and download it.
6. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to this file.

### YouTube Upload

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select your existing project.
3. Enable the **YouTube Data API v3**.
4. Configure the **OAuth Consent Screen** (add yourself as a test user).
5. Create OAuth 2.0 credentials for a **Desktop App**.
6. Download the client secrets JSON file.
7. Set the `GOOGLE_YOUTUBE_SECRETS` environment variable pointing to this file.

---

## 📅 Available Pipelines

- **Quiz Pipeline**:  
  Generates an animated video with a question, multiple answer choices, animated typing effect, a final progress bar, and automatic video export.

- **Fun Facts Pipeline**:  
  Creates a video with a fun fact about a country, using TTS narration, animated captions, visual composition, and uploads the final result automatically to YouTube.

---

## 🔄 Running the Pipelines

Run the Fun Facts Pipeline:

```python
from countries_fun_facts.fun_facts_pipeline import pipeline_fun_fact
pipeline_fun_fact.execute({})
```

Run the Quiz Pipeline:

```python
from quiz.quiz_pipeline import pipeline
pipeline.execute({})
```

---

## 📄 License

This project is licensed under the MIT License.

Developed by **Rafael Marotta** (rafaelmarottag@gmail.com)  
Undergraduate Thesis (TCC) — **Pontifícia Universidade Católica de Minas Gerais (PUC Minas)**

---

## 💬 Notes

- YouTube uploads require manual authorization the first time (OAuth login).
- Token persistence (`token.pickle`) is used to maintain sessions without repeated logins.
- Pipelines are fully modular and can be expanded with new Steps easily.
- New steps like animated progress bars and TTS integration are available for more dynamic videos.

## MongoDB Integration

This project uses MongoDB to track video request status. To configure MongoDB:

- Set the `MONGO_URI` environment variable (default: `mongodb://localhost:27017`).
- Set the `MONGO_DB` environment variable (default: `video_generator`).

Each video request is saved in the `video_requests` collection with fields like `id`, `pipeline`, `text`, `n`, `tone_prompt`, and `status` (pending, processing, completed).

You can run MongoDB with Docker:

```sh
docker run --name mongodb -d -p 27017:27017 -v $(pwd)/mongo-data:/data/db mongo
```