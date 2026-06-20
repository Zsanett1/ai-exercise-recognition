# AI Home Personal Assistant

AI Home Personal Assistant is a university graduation thesis project focused on supporting home workouts with artificial intelligence. The goal of the application is not to be a simple pose detection demo, but to provide a home training assistant that helps users explore exercises, prepare workout sessions, and later receive AI-based movement recognition and repetition tracking.

The project combines pose estimation, exercise classification, rule-based repetition logic, and a Streamlit web interface.

## Project Purpose

Many people prefer or need to train at home, but home workouts often lack feedback, structure, and progress tracking. This project explores how AI-based pose analysis can make independent training more accessible, measurable, and easier to follow.

The application is developed as part of a university graduation thesis project.

## Main Features

- Exercise recognition based on pose landmarks
- Training data collection from exercise videos
- Model training for exercise classification
- Rule-based repetition counting for supported exercises
- Streamlit web application
- User registration and login
- Profile management
- Exercise library with categories and detailed instructions
- Workout history and daily progress tracking
- SQLite database for users, workouts, exercises, and categories

## Application Structure

```text
application.py        Streamlit application entry point
database.py           SQLite database setup and helper functions
views/                Streamlit pages
src/                  AI, data collection, training, and realtime detection logic
assets/               UI images and exercise illustrations
models/               Trained model files
data/                 Dataset files
videos/               Training, validation, and test videos
```

## Streamlit Pages

- **Home**: overview, user progress, and daily goal summary
- **Exercises**: exercise library, category browsing, details popup, and session preparation
- **Profile**: login, registration, profile settings, and daily target setup
- **History**: workout history by date with session details
- **About**: project motivation and purpose

## Current Status

The web application UI and database structure are implemented. The exercise library is database-driven, and the app separates guest and logged-in user behavior.

The real-time AI tracking logic exists separately and is being prepared for integration into the Streamlit application.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Streamlit App

```bash
streamlit run application.py
```

## Notes

This project is developed for educational and research purposes as part of a university graduation thesis. It is not intended to replace professional medical, physiotherapy, or personal training advice.
