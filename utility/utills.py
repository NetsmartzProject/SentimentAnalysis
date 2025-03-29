import requests
from bs4 import BeautifulSoup
import json
import os
import re
import uuid
from collections import Counter
from dotenv import load_dotenv
from groq import Groq
from gtts import gTTS
from deep_translator import GoogleTranslator

load_dotenv()

class Agent:
    def __init__(self, model_name):
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model_name = model_name

    def run(self, prompt):
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_name,
            temperature=0.2,
            max_tokens=512,
            top_p=0.9
        )
        return chat_completion.choices[0].message.content

# Global agent instance
agent = Agent(model_name="llama3-8b-8192")

def translate_to_hindi_deep(text: str) -> str:
    """Translate input text to Hindi using deep-translator."""
    try:
        hindi_text = GoogleTranslator(source='auto', target='hi').translate(text)
        return hindi_text
    except Exception as e:
        return text

def generate_tts_deep(text: str, lang: str = 'hi') -> str:
    """Generate a TTS audio file for the given text (translated to Hindi) using deep-translator."""
    hindi_text = translate_to_hindi_deep(text)
    try:
        if not hindi_text or hindi_text.isascii():
            print("Warning: The translated text does not appear to be in Hindi. Received:", hindi_text)
        tts = gTTS(text=hindi_text, lang=lang)
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        return ""

def fetch_news(company: str):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={company}&sortBy=popularity&apiKey=8ebd90bb204348509808d65a70553855"
    )
    response = requests.get(url)
    temp = response.json()
    articles = temp.get("articles", [])
    top_10_news = articles[:10]
    dataset = {
        "Company": company,
        "Articles": [
            {
                "Title": article.get("title", "No headline available"),
                "description": article.get("description", "No summary available"),
                "url": article.get("url", "No Url Available"),
                "content": article.get("content", "")
            }
            for article in top_10_news
        ]
    }
    return dataset

def extract_webpage_content(url):
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            )
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try multiple options to find the main article content
        main_content = (soup.find('div', class_='article__content') or
                        soup.find('main') or
                        soup.find('article'))

        if main_content:
            content_text = main_content.get_text(strip=True)
        else:
            content_text = 'Could not extract main content'
        return {'content': content_text}

    except requests.RequestException as e:
        return {"content": f"Error fetching the URL: {e}"}
    except Exception as e:
        return {"content": f"Error processing URL {url}: {e}"}

def truncate_text(text, max_tokens=500):
    words = text.split()
    return ' '.join(words[:max_tokens])

def generate_article_summary(text):
    text = truncate_text(text, max_tokens=800)  # Allow more tokens for summary generation
    prompt = f"""
Create a concise, informative summary of this news article in 3-5 sentences.
Focus on the key facts, main points, and implications.
Avoid opinions and stick to the information presented in the text.

Article text:
{text}

Summary:
"""
    response = agent.run(prompt)
    # Clean up the response
    summary = re.sub(r'^(Summary:|Here\'s a summary:)', '', response, flags=re.IGNORECASE).strip()
    return summary

def get_sentiment_from_groq(text):
    text = truncate_text(text)
    prompt = f""" 
Analyze the sentiment of this news excerpt. 
Respond with ONLY "Positive", "Negative", or "Neutral".

Excerpt: 
{text} 

Sentiment: 
"""
    response = agent.run(prompt)
    sentiment = response.strip().lower()
    if "positive" in sentiment:
        return "Positive"
    elif "negative" in sentiment:
        return "Negative"
    else:
        return "Neutral"

def extract_topics_from_groq(text):
    text = truncate_text(text)
    prompt = f""" 
Extract 3-5 precise, distinct topics from this news excerpt. 
Respond ONLY with comma-separated topic names. 
Avoid generic terms. Be specific and meaningful.

Excerpt: 
{text} 

Specific Topics:
"""
    response = agent.run(prompt)

    def clean_topic(topic):
        topic = re.sub(r'^(Here are the topics:|Topics:|3-5 key topics:)', '', topic, flags=re.IGNORECASE)
        topic = re.sub(r'^["\']|["\']$', '', topic.strip())
        return topic if topic else None

    topics = [clean_topic(topic) for topic in response.split(',')]
    topics = [topic for topic in topics if topic]
    return topics[:5]

def generate_coverage_differences(articles, company: str):
    # Ensure we have at least two articles for comparison
    if len(articles) < 2:
        return [{
            "Comparison": "Insufficient articles for comparative analysis.",
            "Impact": "No comparative insights available."
        }]
    
    coverage_prompt = f"""
Analyze the following two articles about Tesla:

Article 1:
- Title: {articles[0].get('Title', 'Untitled')}
- Topics: {articles[0].get('Topics', [])}
- Sentiment: {articles[0].get('Sentiment', 'Unspecified')}
- Summary: {articles[0].get('Summary', 'No summary available')}

Article 2:
- Title: {articles[1].get('Title', 'Untitled')}
- Topics: {articles[1].get('Topics', [])}
- Sentiment: {articles[1].get('Sentiment', 'Unspecified')}
- Summary: {articles[1].get('Summary', 'No summary available')}

Provide a detailed comparison that focuses on:
1. Narrative differences between the two articles
2. Contrasting perspectives
3. Potential market or investor implications

Format your response as:
Comparison: [Specific narrative differences]
Impact: [Market or investor implications]
"""
    try:
        coverage_response = agent.run(coverage_prompt)
        comparison_match = re.search(r'Comparison:\s*(.+?)(?=Impact:|$)', coverage_response, re.DOTALL)
        impact_match = re.search(r'Impact:\s*(.+)$', coverage_response, re.DOTALL)
        comparison = comparison_match.group(1).strip() if comparison_match else (
            f"Articles present different perspectives on {company} recent developments."
        )
        impact = impact_match.group(1).strip() if impact_match else (
            "Varying coverage may create mixed signals for investors and market perception."
        )
        return [{"Comparison": comparison, "Impact": impact}]
    except Exception as e:
        return [{
            "Comparison": f"Diverse coverage highlighting different aspects of {company} business.",
            "Impact": "Multiple perspectives provide a nuanced view of the company's current situation."
        }]

def generate_comparative_analysis(articles, company: str):
    sentiment_distribution = Counter(article['Sentiment'] for article in articles)
    unique_topics = [set(article['Topics']) for article in articles if article.get('Topics')]
    common_topics = set.intersection(*unique_topics) if unique_topics else []

    unique_topics_per_article = [
        set(article['Topics']) - set.union(*(unique_topics[:i] + unique_topics[i+1:]))
        for i, article in enumerate(articles) if article.get('Topics')
    ]

    coverage_differences = generate_coverage_differences(articles, company)
    
    final_sentiment_prompt = f"""
Analyze {company} news coverage:
- Article Sentiments: {[article['Sentiment'] for article in articles]}
- Common Themes: {list(common_topics)}

**Please count the right number of Positive, Negative and Neutral sentiments.**

Provide a concise overall sentiment summary focusing on potential market implications.
"""
    final_sentiment_analysis = agent.run(final_sentiment_prompt)

    comparative_analysis = {
        "Comparative Sentiment Score": {
            "Sentiment Distribution": dict(sentiment_distribution),
            "Coverage Differences": coverage_differences,
            "Topic Overlap": {
                "Common Topics": list(common_topics),
                "Unique Topics in Article 1": list(unique_topics_per_article[0]) if unique_topics_per_article else [],
                "Unique Topics in Article 2": list(unique_topics_per_article[1]) if len(unique_topics_per_article) > 1 else []
            }
        },
        "Final Sentiment Analysis": final_sentiment_analysis
    }
    
    return comparative_analysis

def get_netflix_analysis(company: str, generate_hindi_audio=True):
    dataset = fetch_news(company)
    
    # For each article, extract webpage content
    for article in dataset["Articles"]:
        url = article.get("url", "")
        if url:
            content = extract_webpage_content(url)
            article["article_content"] = content
        else:
            article["article_content"] = {"content": "No URL provided"}
    
    # For each article, analyze sentiment, extract topics, and generate summary using Groq
    for article in dataset["Articles"]:
        content_text = article["article_content"]["content"]
        
        # Generate summary
        summary = generate_article_summary(content_text)
        article["Summary"] = summary
        
        # Get sentiment
        sentiment = get_sentiment_from_groq(content_text)
        article["Sentiment"] = sentiment
        
        # Extract topics
        topics = extract_topics_from_groq(content_text)
        article["Topics"] = topics
    
    # Generate a comparative analysis of the articles
    comp_analysis = generate_comparative_analysis(dataset["Articles"], company)
    dataset["Comparative Analysis"] = comp_analysis

    # If requested, generate Hindi audio for the final sentiment analysis text.
    if generate_hindi_audio and "Final Sentiment Analysis" in comp_analysis:
        hindi_audio_filename = generate_tts_deep(comp_analysis["Final Sentiment Analysis"])
        dataset["Comparative Analysis"]["Final Sentiment Analysis Hindi Audio"] = hindi_audio_filename

    return dataset
