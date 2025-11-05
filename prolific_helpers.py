"""
Helper functions for Prolific API interactions and study management.
"""

import json
import uuid
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from io import StringIO
import pandas as pd


def get_researcher_id(headers: dict) -> str:
    """
    Fetch the Prolific researcher ID.

    Args:
        headers: Dictionary containing API authorization headers

    Returns:
        str: The researcher ID
    """
    res = requests.get("https://api.prolific.com/api/v1/users/me/", headers=headers)
    res.raise_for_status()
    return res.json()["id"]


def create_survey(headers: dict, researcher_id: str, survey_config: dict) -> str:
    """
    Create a Prolific survey with the specified configuration.

    Args:
        headers: Dictionary containing API authorization headers
        researcher_id: The Prolific researcher ID
        survey_config: Dictionary containing survey configuration with keys:
            - title: Survey title
            - question_text: The question to ask
            - answers: List of answer options

    Returns:
        str: The survey ID
    """
    # Generate UUIDs
    section_id = str(uuid.uuid4())
    question_id = str(uuid.uuid4())
    answer_ids = [str(uuid.uuid4()) for _ in survey_config["answers"]]

    # Build answers list
    answers = [
        {"id": answer_id, "value": answer_text}
        for answer_id, answer_text in zip(answer_ids, survey_config["answers"])
    ]

    # Build question structure
    question = {
        "id": question_id,
        "title": survey_config["question_text"],
        "type": "single",
        "answers": answers,
    }

    # Build the payload
    survey_data = {
        "researcher_id": researcher_id,
        "title": survey_config["title"],
        "sections": [
            {
                "id": section_id,
                "title": survey_config["question_text"],
                "questions": [question],
            }
        ],
        "questions": [question],
    }

    response = requests.post(
        "https://api.prolific.com/api/v1/surveys/",
        headers=headers,
        data=json.dumps(survey_data)
    )
    response.raise_for_status()

    return response.json()["_id"]


def create_study(
    headers: dict,
    survey_id: str,
    study_config: dict,
    project_id: str
) -> str:
    """
    Create a draft Prolific study.

    Args:
        headers: Dictionary containing API authorization headers
        survey_id: The survey ID to link to this study
        study_config: Dictionary containing study configuration with keys:
            - name: Study name
            - internal_name_prefix: Prefix for internal name
            - description: Study description
            - reward: Reward amount in dollars
            - participants: Number of participants
            - estimated_time: Estimated time in minutes
            - max_time: Maximum time in minutes
            - device_compatibility: List of compatible devices
            - privacy_notice: Privacy notice text
        project_id: The Prolific project ID

    Returns:
        str: The study ID
    """
    # Generate completion code with timestamp
    completion_code = f"AI_DAILYLIFE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Build the study payload
    study_data = {
        "name": study_config["name"],
        "internal_name": f"{study_config.get('internal_name_prefix', study_config['name'])} {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": study_config["description"],
        "external_study_url": f"https://prolific.com/surveys/{survey_id}",
        "completion_codes": [
            {
                "code": completion_code,
                "code_type": "COMPLETED",
                "actions": [{"action": "AUTOMATICALLY_APPROVE"}],
            }
        ],
        "estimated_completion_time": study_config["estimated_time"],
        "max_time": study_config["max_time"],
        "reward": int(study_config["reward"] * 100),  # convert to cents
        "total_available_places": study_config["participants"],
        "device_compatibility": study_config["device_compatibility"],
        "peripheral_requirements": [],
        "privacy_notice": study_config["privacy_notice"],
        "project": project_id
    }

    # Create draft study
    study_response = requests.post(
        "https://api.prolific.com/api/v1/studies/",
        headers=headers,
        data=json.dumps(study_data)
    )
    study_response.raise_for_status()

    return study_response.json().get("id")


def publish_study(headers: dict, study_id: str) -> int:
    """
    Publish a Prolific study.

    Args:
        headers: Dictionary containing API authorization headers
        study_id: The study ID to publish

    Returns:
        int: HTTP status code
    """
    publish_response = requests.post(
        f"https://api.prolific.com/api/v1/studies/{study_id}/transition/",
        headers=headers,
        data=json.dumps({"action": "PUBLISH"})
    )
    publish_response.raise_for_status()

    return publish_response.status_code


def show_study_results(study_id: str, headers: dict, timezone_str: str = "America/Los_Angeles") -> pd.DataFrame:
    """
    Fetch and display Prolific study info, latest response, and completion duration.

    Args:
        study_id: The study ID
        headers: Dictionary containing API authorization headers
        timezone_str: Timezone string for displaying times (default: "America/Los_Angeles")

    Returns:
        pd.DataFrame: DataFrame containing study responses
    """
    display_tz = ZoneInfo(timezone_str)

    # --- Get study details ---
    study_url = f"https://api.prolific.com/api/v1/studies/{study_id}/"
    study_response = requests.get(study_url, headers=headers)
    study_response.raise_for_status()
    study_info = study_response.json()

    status = study_info.get("status")
    name = study_info.get("name")
    total_places = study_info.get("total_available_places")
    total_places_taken = study_info.get("places_taken")

    # Parse published_at as UTC, then convert to specified timezone for display
    published_iso = study_info.get("published_at")  # e.g. "2025-09-29T13:08:00Z"
    created_at_utc = datetime.fromisoformat(published_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    created_at_display = created_at_utc.astimezone(display_tz)

    # --- Print basic study info ---
    print(f"✅ Study Name: {name}")
    print(f"📊 Status: {status}")
    print(f"👥 Total Places: {total_places}")
    print(f"📩 Total Submissions: {total_places_taken}")
    print(f"⏳ Created at: {created_at_display.strftime('%d %b %Y, %I:%M %p %Z')}")

    # --- Get response exports ---
    responses_url = f"https://api.prolific.com/api/v1/studies/{study_id}/export/"
    resp = requests.get(responses_url, headers=headers)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))

    if "Completed at" not in df.columns:
        print("⚠️ 'Completed at' column not found in export.")
        return df

    # --- Process completion times ---
    completed_times = pd.to_datetime(df["Completed at"], errors="coerce", utc=True)
    latest_completion_utc = completed_times.dropna().max()

    if pd.isna(latest_completion_utc):
        print("⚠️ No completions yet.")
        return df

    latest_completion_display = latest_completion_utc.tz_convert(display_tz)
    print(f"🕒 Last Response At: {latest_completion_display.strftime('%d %b %Y, %I:%M %p %Z')}")

    # --- Compute duration (use UTC to avoid DST pitfalls), display in minutes ---
    duration_minutes = (latest_completion_utc - created_at_utc).total_seconds() / 60
    print(f"⏱️ Time Lapsed: {duration_minutes:.0f} minutes")

    return df


def plot_survey_responses(df: pd.DataFrame, question_column: str, wrap_width: int = 32, figsize: tuple = None):
    """
    Create a horizontal bar chart of survey responses.

    Args:
        df: DataFrame containing survey responses
        question_column: Name of the column containing responses
        wrap_width: Width for wrapping long labels (default: 32)
        figsize: Figure size as (width, height). If None, auto-calculated based on response count

    Returns:
        matplotlib figure and axes objects
    """
    import matplotlib.pyplot as plt
    from textwrap import fill

    response_counts = (
        df[question_column]
        .dropna()
        .astype(str)
        .value_counts()
        .sort_values(ascending=True)
    )

    labels_wrapped = [fill(lbl, width=wrap_width) for lbl in response_counts.index]

    # Auto-calculate height if not specified
    if figsize is None:
        height = max(6, 0.6 * len(response_counts))
        figsize = (12, height)

    fig, ax = plt.subplots(figsize=figsize)

    ax.barh(labels_wrapped, response_counts.values)

    ax.set_title(question_column, wrap=True)
    ax.set_xlabel("Count")
    ax.set_ylabel("Response")

    ax.invert_yaxis()

    fig.tight_layout()

    return fig, ax
