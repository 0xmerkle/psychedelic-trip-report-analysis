import streamlit as st
import openai
import pandas as pd
import json
import glob
import os
import plotly.express as px
from analysis_pipeline import (
    analyze_themes,
    extract_data_to_json,
    run_analysis,
    AnalysisResultJSON,
    run_analysis_and_categorize,
)
from data_utils import (
    aggregate_data,
    create_theme_pie_chart,
    create_emotion_bar_chart,
    export_visualization,
)

# Import other necessary libraries


@st.cache_resource
def load_data():
    dataframes = {}
    for csv_file in glob.glob("raw_experiences/**/*.csv", recursive=True):
        substance = csv_file.split(os.sep)[
            1
        ]  # Assuming the substance name is the directory name
        key = f"{substance}_{os.path.splitext(os.path.basename(csv_file))[0]}"
        dataframes[key] = pd.read_csv(csv_file)
    return dataframes


def main():
    st.title("Psychedelic Experience Analysis with LLMs")
    dataframes = load_data()
    api_key = st.text_input("Enter your OpenAI API key", type="password")
    dataset_options = list(dataframes.keys())

    # Select the dataset (now including the substance in its key)
    dataset_key = st.selectbox("Select the dataset", options=dataset_options)
    df = dataframes[dataset_key]

    # Extract the substance from the selected dataset key
    substance = dataset_key.split("_")[0]

    # Report selection
    report_titles = df["title"].tolist() if "title" in df.columns else []
    selected_titles = st.multiselect(
        "Select reports for analysis", options=report_titles
    )
    if st.button("Analyze Reports"):
        with st.spinner("Fetching and analyzing reports..."):
            theme_counts, emotion_counts, _ = run_analysis_and_categorize(
                df, selected_titles
            )

            # Assuming `run_analysis_and_categorize` returns the aggregate counts
            if theme_counts and emotion_counts:
                # Create visualizations
                theme_fig = create_theme_pie_chart(theme_counts)
                emotion_fig = create_emotion_bar_chart(emotion_counts)

                # Display visualizations in Streamlit
                st.plotly_chart(theme_fig)
                st.plotly_chart(emotion_fig)

                # Optionally save visualizations
                # Note: This will save images to the server running Streamlit.
                # Users will not be able to download them directly from the app without additional steps.
                export_visualization(theme_fig, "theme_distribution")
                export_visualization(emotion_fig, "emotion_distribution")

                st.success(
                    "Visualizations generated. Check the 'visualizations' folder for saved images."
                )
            else:
                st.error("No themes or emotions to display.")
            # if st.button("Analyze Reports"):
            #     with st.spinner("Fetching and analyzing reports..."):
            #         analysis_results = []

            #         for title in selected_titles:
            #             print(f"Analyzing report titled: {title}")
            #             raw_experience = df[df["title"] == title]["text"].iloc[0]
            #             themes, substance, emotions, age, gender = run_analysis(
            #                 raw_experience=raw_experience, output_filename=title
            #             )
            #             if themes is not None:
            #                 analysis_result = {
            #                     "themes": themes,
            #                     "substance": substance,
            #                     "emotions": emotions,
            #                     "age": age,
            #                     "gender": gender,
            #                 }
            #                 analysis_results.append(analysis_result)
            #             else:
            #                 st.error(f"Analysis failed for report titled: {title}")

            #         if analysis_results:
            #             st.success("Analysis complete! See the visualizations below.")

            #             report_analyses = [
            #                 AnalysisResultJSON(**result) for result in analysis_results
            #             ]
            #             aggregated_data = aggregate_data(report_analyses)

            #             # Create visualizations
            #             theme_fig = create_theme_pie_chart(aggregated_data["themes"])
            #             emotion_fig = create_emotion_bar_chart(aggregated_data["emotions"])

            #             # Display visualizations in Streamlit
            #             st.plotly_chart(theme_fig)
            #             st.plotly_chart(emotion_fig)

            # Optionally save visualizations
            export_visualization(theme_fig, "theme_distribution")
            export_visualization(emotion_fig, "emotion_distribution")


# Run the Streamlit app
if __name__ == "__main__":
    main()
