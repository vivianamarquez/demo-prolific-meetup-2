# Prolific Study Demo: Halloween Costumes 2025 🎃

Automated workflow for creating, publishing, and analyzing Prolific surveys. Built for the Prolific SF Meetup #2.

## Files

- **`config.yaml`** - Survey configuration (questions, rewards, participant settings)
- **`prolific_helpers.py`** - Helper functions for Prolific API interactions
- **`Halloween Demo Prolific.ipynb`** - Main notebook workflow

## Setup

1. Set environment variables:
   ```bash
   PROLIFIC_API_TOKEN=your_token
   PROLIFIC_WORKSPACE_ID=your_workspace_id
   PROLIFIC_PROJECT_ID=your_project_id
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
