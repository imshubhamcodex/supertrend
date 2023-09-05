#pip install BeautifulSoup TextBlob
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import time
from datetime import datetime, timedelta
from mercury_Bot import send_message

# Initialize NLTK's VADER sentiment analyzer
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()


def analyze_news(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('li')


        sentiment_scores = []
        titles_and_scores = [] 
        valid_article_count = 0

        if len(articles) > 0:
            for article in (articles):
                title_element = article.find('h2')
                content_element = article.find('p')

                if title_element and content_element:
                    title = title_element.text.strip()
                    content = content_element.text.strip()
                    blob = TextBlob(content)
                    polarity = blob.sentiment.polarity
                    subjectivity = blob.sentiment.subjectivity

                    vader_scores = sia.polarity_scores(content)
                    compound_score = vader_scores['compound']

                    sentiment_scores.append(compound_score)
                    titles_and_scores.append((title, compound_score))
                    valid_article_count += 1

                    if valid_article_count >= 4:
                        break

        if len(sentiment_scores) == 4:
            if sentiment_scores != analyze_news.previous_scores:
                text =""
                for title, compound_score in titles_and_scores:
                    text += "*" + str(title) + "*\n"
                    text += "--------------------------------------------\n"

                overall_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                text += "Sentiment : -1 < *" + str(round(overall_sentiment, 2)) + "* < 1"
                
                # print(text)
                send_message(text)
            else:
                print("Sentiment scores have not changed.")

            analyze_news.previous_scores = sentiment_scores
            analyze_news.previous_titles_and_scores = titles_and_scores

    else:
        print(f'Failed to retrieve content. Status code: {response.status_code}')



yahoo_finance_url = 'https://www.moneycontrol.com/news/tags/bank-nifty.html'
analyze_news.previous_scores = []
analyze_news.previous_titles_and_scores = []

while True:
    print(" ")
    analyze_news(yahoo_finance_url)
    current_time = datetime.now().time()
    print("\r" +"Time: "+ str(current_time), end='', flush=True)
    print(" ")
    time.sleep(15 * 60)
