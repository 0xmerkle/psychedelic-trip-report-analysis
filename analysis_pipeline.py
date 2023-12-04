from openai import OpenAI
import os
import dotenv
import json
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
from collections import Counter
from uuid import uuid4

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)
extracted_data_dir = "processed_data"


class AnalysisResultJSON(BaseModel):
    substance: str
    themes: List[str]
    emotions: List[str]
    age: Optional[str] = "N/A"
    gender: Optional[str] = "N/A"


anlaysis_prompt = """
    You are a psychedelic experience analyst. You are tasked with analyzing the experiences of a group of people who have experienced a psychedelic experience.
    You will be given the following information about each person:
    - Substance used
    - Age
    - Gender
    - Raw Experience
    ----
    Please find the information for that below:
    # PSYCHEDELIC EXPERIENCE REPORT
    Raw Experience: {raw_experience}
    ----
    Your task is to identify the following information from the trip report:
    ---
    1. Common themes 
    2. Substance used
    3. Age of reporter
    4. Gender of reporter
    5. Common emotions
    ---
    If gender or age is not available please say that they are "N/A". Begin!
"""

extraction_prompt = """
    You are a psychedelic experience analyst. You are tasked with extracting the experiences of a group of people who have experienced a psychedelic experience.
    You will be given a raw text analysis of a given experience below delimited by <e> tags:
    # RAW ANALYSIS
    {raw_analysis}
    ----
    Your task is to identify themes from the trip report and return the most common themes, emotions as well as the substance used and return it in the following JSON format:
    {{
        "substance": "<substance name>",
        "themes": [
            <"Theme 1">,
            <"Theme 2">,
            <"Theme 3">,
        ],
        "emotions": [
            <"Emotion 1">,
            <"Emotion 2">,
            <"Emotion 3">,
        ],
        "age": "<age>",
        "gender": "<gender>"
    }}
    ----
    If no specific age or gender is mentioned, please use "N/A" for those fields.
    Begin!
    """

find_broad_themes_prompt = """
    You are a psychedelic experience analyst. You are tasked with finding the broad themes of a group of people who have experienced a psychedelic experience.
    You will be given a list of themes found from the trip reports below delimited by <t> tags:
    <t>
    # THEMES
    {items}
    # END OF THEMES
    <t>
    Return the high-level categories in the following JSON format below:
    {{
        "common_themes": [
            <"Theme 1">,
            <"Theme 2">,
            <"Theme 3">,
            ]
    }}
    ----
    Begin!
    """

find_broad_emotions_prompt = """
    You are a psychedelic experience analyst. You are tasked with finding the broad emotions of a group of people who have experienced
    a psychedelic experience.
    You will be given a list of emotions found from the trip reports below delimited by <e> tags:
    <e>
    # EMOTIONS
    {items}
    # END OF EMOTIONS
    <e>
    Return the high-level categories in the following JSON format below:
    {{
        "common_emotions": [
        <"Emotion 1">,
        <"Emotion 2">,
        <"Emotion 3">,
        ]
    }}
    ----
    Begin!
    """

map_individual_to_broad_categories_prompt = """
    You are a psychedelic experience analyst. You are tasked with grouping the common themes and emotions that were found from the trip reports.
    You will group the {category_type} items into the following categories:
    # CATEGORIES
    {categories}
    # END OF CATEGORIES
   
    You will be given a list of {category_type} items found from the trip reports below delimited by <t>
    <t>
    # {all_items_for_category_type_title}
    {all_items_for_category_type}
    # END OF {all_items_for_category_type_title}
    <t>
   
    ---
    Return the high-level categories in the following JSON format below:
    {{
       
            '{category_type}_category_1': [
                <"{category_type} 1">,
                <"{category_type} 2">,
                <"{category_type} 3">,
                ],
            '{category_type}_category_2': [
                <"{category_type} 4">,
                <"{category_type} 5">,
                <"{category_type} 6">,
                ],
            
    }}
    ----
    Begin!
"""


def find_broad_categories(prompt_template: str, items):
    """
    General function to find broad categories for themes or emotions.
    """
    formatted_items = "\n".join(
        f"- {item}" for item in set(items)
    )  # Remove duplicates and format
    prompt = prompt_template.format(items=formatted_items)
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    json_loaded_res = json.loads(response.choices[0].message.content)
    if not isinstance(json_loaded_res, dict):
        raise ValueError("The response is not a dictionary.")
    return json_loaded_res


def map_individual_to_broad_categories(
    individual_items, category_type, broad_categories
) -> Dict[str, Any]:
    """
    Map individual themes or emotions to the broad categories identified by the LLM.
    """
    category_delimiter_title = "THEMES" if category_type == "theme" else "EMOTIONS"
    prompt = map_individual_to_broad_categories_prompt.format(
        category_type=category_type,
        categories="\n".join(f"- {category}" for category in broad_categories),
        all_items_for_category_type_title=category_delimiter_title,
        all_items_for_category_type="\n".join(f"- {item}" for item in individual_items),
    )

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )

    return json.loads(response.choices[0].message.content)


def categorize_analysis_results(analysis_results):
    # Extract all themes and emotions from the analysis results
    all_themes = [theme for result in analysis_results for theme in result.themes]
    all_emotions = [
        emotion for result in analysis_results for emotion in result.emotions
    ]

    # Find broad categories for themes and emotions
    broad_themes = find_broad_categories(find_broad_themes_prompt, all_themes)
    broad_emotions = find_broad_categories(find_broad_emotions_prompt, all_emotions)
    print(f"===== Broad Themes =====:\n{broad_themes}\n")
    print(f"===== Broad Emotions =====:\n{broad_emotions}")
    # Map individual themes and emotions to broad categories
    theme_mapping = map_individual_to_broad_categories(
        individual_items=all_themes,
        category_type="theme",
        broad_categories=broad_themes["common_themes"],
    )
    print(f"===== Theme Mapping =====:\n{theme_mapping}\n")
    emotion_mapping = map_individual_to_broad_categories(
        individual_items=all_emotions,
        category_type="emotion",
        broad_categories=broad_emotions["common_emotions"],
    )
    print(f"===== Emotion Mapping =====:\n{emotion_mapping}\n")

    # Return mappings
    return theme_mapping, emotion_mapping


def analyze_themes(raw_experience):
    prompt = anlaysis_prompt.format(raw_experience=raw_experience)
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message


def extract_data_to_json(raw_analysis):
    prompt = extraction_prompt.format(raw_analysis=raw_analysis)
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def save_data(data, file_name, session_id):
    with open(f"{extracted_data_dir}/{session_id}-{file_name}", "w") as f:
        json.dump(data, f, indent=4)


def run_analysis(raw_experience, output_filename, session_id):
    try:
        raw_analysis = analyze_themes(raw_experience=raw_experience)
        json_data = extract_data_to_json(raw_analysis=raw_analysis)
        data = json.loads(json_data)  # Parse the JSON string into a Python dict

        analysis_result = AnalysisResultJSON(**data)
        themes = analysis_result.themes
        emotions = analysis_result.emotions
        substance = analysis_result.substance
        age = analysis_result.age if analysis_result.age else "N/A"
        gender = analysis_result.gender if analysis_result.gender else "N/A"
        save_data(
            data=data,
            file_name=f"{output_filename}.json",
            session_id=session_id,
        )
        return themes, substance, emotions, age, gender
    except ValidationError as e:
        print(e)
        return None, None, None, None, None


def aggregate_mapping_counts(mapping):
    """
    Aggregate counts from a mapping where each key maps to a list of items.
    """
    counts = Counter()
    for category, items in mapping.items():
        for item in items:
            counts[category] += 1
    return counts


def run_analysis_and_categorize(df, selected_titles, output_dir="processed_data"):
    # Collect all individual themes and emotions
    all_themes = []
    all_emotions = []
    analysis_results = []
    curr_session_id = str(uuid4())
    for title in selected_titles:
        raw_experience = df[df["title"] == title]["text"].iloc[0]
        try:
            themes, substance, emotions, age, gender = run_analysis(
                raw_experience, title, session_id=curr_session_id
            )
            if themes is not None:
                all_themes.extend(themes)
                all_emotions.extend(emotions)
                analysis_results.append(
                    {
                        "substance": substance,
                        "themes": themes,
                        "emotions": emotions,
                        "age": age,
                        "gender": gender,
                    }
                )
        except Exception as e:
            print(f"An error occurred while analyzing report titled '{title}': {e}")

    # Use the LLM to generate broader categories for themes and emotions
    broad_theme_categories = find_broad_categories(find_broad_themes_prompt, all_themes)
    broad_emotion_categories = find_broad_categories(
        find_broad_emotions_prompt, all_emotions
    )
    print(f"===== Broad Themes =====:\n{broad_theme_categories}\n")
    print(f"===== Broad Emotions =====:\n{broad_emotion_categories}")
    # Map individual themes and emotions to the broad categories
    theme_mapping = map_individual_to_broad_categories(
        individual_items=all_themes,
        category_type="theme",
        broad_categories=broad_theme_categories["common_themes"],
    )
    print(f"===== Theme Mapping =====:\n{theme_mapping}\n")
    emotion_mapping = map_individual_to_broad_categories(
        individual_items=all_emotions,
        category_type="emotion",
        broad_categories=broad_emotion_categories["common_emotions"],
    )
    print(f"===== Emotion Mapping =====:\n{emotion_mapping}\n")

    # Aggregate the mapped data for visualization
    theme_counts = aggregate_mapping_counts(theme_mapping)
    emotion_counts = aggregate_mapping_counts(emotion_mapping)

    # Save the results

    save_data(
        data={
            "theme_counts": theme_counts,
            "emotion_counts": emotion_counts,
            "analysis_results": analysis_results,
        },
        file_name="aggregated_analysis.json",
        session_id=curr_session_id,
    )

    return theme_counts, emotion_counts, analysis_results
