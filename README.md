# FastAPI Social Media Demo

A social media backend built with FastAPI. The project demonstrates REST API development, authentication, database integration, background tasks, email confirmation, automated testing, and third-party API integration.

## Features

- User registration and email confirmation
- JWT-based authentication
- Create and retrieve posts
- Add comments to posts
- Like posts
- Sort posts by newest, oldest, or most liked
- Generate post images asynchronously from text prompts
- Update posts with generated image URLs
- Email notifications for registration and image-generation results
- Structured logging
- Automated tests with `pytest`

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- Databases
- SQLite
- HTTPX
- Pytest
- Mailgun
- DeepAI
- Better Stack / Logtail
- Backblaze B2

## Project Structure

```text
app/
├── main.py
├── config.py
├── database.py
├── security.py
├── tasks.py
├── models/
├── routers/
└── tests/
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/fastapi-social-media-demo.git
cd fastapi-social-media-demo
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Example development configuration:

```env
ENV_STATE=dev

DEV_DATABASE_URL=sqlite:///data.db

DEV_LOGTAIL_API_KEY=
DEV_LOGTAIL_INGESTING_HOST=

DEV_MAILGUN_API_KEY=
DEV_MAILGUN_DOMAIN=

DEV_B2_KEY_ID=
DEV_B2_APPLICATION_KEY=
DEV_B2_BUCKET_NAME=

DEV_DEEPAI_API_KEY=
```

Never commit the real `.env` file or API keys.

## Run the Application

```bash
uvicorn app.main:app --reload
```

API documentation:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Run Tests

```bash
pytest
```

## Main API Flow

```text
Register
  ↓
Confirm email
  ↓
Log in
  ↓
Receive access token
  ↓
Create posts, comments, and likes
```

## Create a Post with an Image Prompt

```http
POST /post?prompt=A cute orange cat
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "body": "My new post"
}
```

The post is created immediately with:

```json
{
  "image_url": null
}
```

FastAPI then runs the image-generation task in the background. When generation succeeds, the post is updated with the returned image URL.

## Background Image Workflow

```text
Create post
  ↓
Return response immediately
  ↓
Generate image in background
  ↓
Update image_url
  ↓
Send success or failure email
```

If image generation fails, the post remains available and `image_url` stays `null`.

## Important Note

DeepAI API access may require an active paid plan. A `402 Payment Required` response indicates an account or subscription issue rather than an application bug.

## Purpose

This repository is a demonstration project created to practice FastAPI and backend development concepts. It is not intended to operate as a production social media platform.

## License

This project is intended for educational use.
