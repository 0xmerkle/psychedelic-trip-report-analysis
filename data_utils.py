# data_utils.py
from typing import List, NamedTuple
from collections import Counter
from typing import Dict
import plotly.express as px
from analysis_pipeline import AnalysisResultJSON


def aggregate_data(analysis_results: List[AnalysisResultJSON]) -> Dict[str, Counter]:
    theme_counter = Counter()
    emotion_counter = Counter()

    for analysis in analysis_results:
        theme_counter.update(analysis.themes)
        emotion_counter.update(analysis.emotions)

    return {"themes": theme_counter, "emotions": emotion_counter}


def create_theme_pie_chart(theme_counter: Counter):
    fig = px.pie(
        values=theme_counter.values(), names=theme_counter.keys(), title="Common Themes"
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def create_emotion_bar_chart(emotion_counter: Counter):
    fig = px.bar(
        x=list(emotion_counter.keys()),
        y=list(emotion_counter.values()),
        title="Emotions Distribution",
    )
    fig.update_layout(xaxis_title="Emotion", yaxis_title="Count")
    return fig


def export_visualization(fig, filename: str):
    fig.write_image(f"visualizations/{filename}.png")
