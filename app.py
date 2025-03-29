import streamlit as st
import json
import os
import pandas as pd
import uuid
from utility.utills import get_netflix_analysis

def main():
    st.set_page_config(page_title="Company News Analysis", layout="wide")
    
    st.title("Company News Analysis Dashboard")
    st.write("Enter a company name to get news, sentiment analysis, and topic extraction with Hindi audio summary")
    
    if 'displayed_analysis' not in st.session_state:
        st.session_state.displayed_analysis = False
    
    company_name = st.text_input("Enter Company Name", "Tesla")
    
    if st.button("Get Analysis"):
        with st.spinner(f"Fetching and analyzing news for {company_name}..."):
            try:
                analysis_result = get_netflix_analysis(company_name)
                
                st.session_state.analysis_result = analysis_result
                st.session_state.company_name = company_name
                st.session_state.displayed_analysis = False  
                
                st.success(f"Analysis completed for {company_name}")
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    
    if 'analysis_result' in st.session_state and not st.session_state.displayed_analysis:
        display_analysis(st.session_state.analysis_result)
        st.session_state.displayed_analysis = True  

def display_analysis(analysis_result):
    st.header(f"Analysis for {analysis_result['Company']}")
    
    tabs = st.tabs(["Summary", "Articles", "Comparative Analysis"])
    
    with tabs[0]:
        st.subheader("Overall Analysis")
        comp_analysis = analysis_result.get("Comparative Analysis", {})
        
        if "Final Sentiment Analysis" in comp_analysis:
            st.markdown("### Final Sentiment Analysis")
            st.write(comp_analysis["Final Sentiment Analysis"])
            
            if "Final Sentiment Analysis Hindi Audio" in comp_analysis:
                audio_file = comp_analysis["Final Sentiment Analysis Hindi Audio"]
                if os.path.exists(audio_file):
                    unique_id = str(uuid.uuid4())
                    
                    st.audio(audio_file)
                    
                    with open(audio_file, "rb") as file:
                        btn = st.download_button(
                            label="Download Hindi Audio Summary",
                            data=file,
                            file_name=audio_file,
                            mime="audio/mp3",
                            key=f"download_{unique_id}"  
                        )
        
        if "Comparative Sentiment Score" in comp_analysis:
            st.markdown("### Sentiment Distribution")
            sentiment_dist = comp_analysis["Comparative Sentiment Score"].get("Sentiment Distribution", {})
            if sentiment_dist:
                # Create a DataFrame for visualization
                sentiment_df = pd.DataFrame({
                    'Sentiment': list(sentiment_dist.keys()),
                    'Count': list(sentiment_dist.values())
                })
                st.bar_chart(sentiment_df.set_index('Sentiment'))
            
            if "Topic Overlap" in comp_analysis["Comparative Sentiment Score"]:
                st.markdown("### Common Topics")
                topic_overlap = comp_analysis["Comparative Sentiment Score"]["Topic Overlap"]
                if topic_overlap.get("Common Topics"):
                    st.write(", ".join(topic_overlap["Common Topics"]))
                else:
                    st.write("No common topics found across articles")
    
    with tabs[1]:
        st.subheader("News Articles")
        
        for i, article in enumerate(analysis_result.get("Articles", [])):
            with st.expander(f"Article {i+1}: {article.get('Title', 'No Title')}"):
                st.markdown(f"**Sentiment:** {article.get('Sentiment', 'Not analyzed')}")
                st.markdown(f"**URL:** [{article.get('url', 'No URL')}]({article.get('url', '#')})")
                
                # Topics
                if "Topics" in article and article["Topics"]:
                    st.markdown("**Topics:**")
                    st.write(", ".join(article["Topics"]))
                
                if "Summary" in article:
                    st.markdown("**Summary:**")
                    st.write(article["Summary"])
    
    with tabs[2]:
        st.subheader("Comparative Analysis")
        
        if "Coverage Differences" in comp_analysis.get("Comparative Sentiment Score", {}):
            coverage_diff = comp_analysis["Comparative Sentiment Score"]["Coverage Differences"]
            for diff in coverage_diff:
                st.markdown("#### Narrative Differences")
                st.write(diff.get("Comparison", "No comparison available"))
                
                st.markdown("#### Potential Impact")
                st.write(diff.get("Impact", "No impact analysis available"))

if __name__ == "__main__":
    main()