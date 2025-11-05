# Prolific Study Demo: Halloween Costumes 2025 🎃

Automated workflow for creating, publishing, and analyzing Prolific surveys. Built for the Prolific SF Meetup #2.

## Files

- **`config.yaml`** - Survey configuration (questions, rewards, participant settings)
- **`prolific_helpers.py`** - Helper functions for Prolific API interactions
- **`Halloween Demo Prolific.ipynb`** - Main notebook workflow
- **`.env.example`** - Template for environment variables

## Setup

1. Copy `.env.example` to `.env` and add your credentials:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install pandas matplotlib pyyaml requests python-dotenv
   ```

## Usage

1. Edit `config.yaml` to customize your study
2. Run the notebook to create and publish your survey
3. View results with demographic breakdowns (generation, gender)

## Features

- Create surveys and studies via Prolific API
- Auto-publish and monitor submissions
- Visualize results by demographics
- Export data to CSV
