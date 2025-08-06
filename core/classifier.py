from transformers import pipeline

model = pipeline("text-classification", model="cardiffnlp/tweet-topic-21-multi")

tragedy_keywords = {"died", "killed", "death", "murder", "injured", "attack"}

label_mapping = {
    "news_&_social_concern": "World News",
    "sports": "Sports",
    "music": "Entertainment",
    "arts_&_culture": "Entertainment",
    "celebrity_&_pop_culture": "Entertainment",
    "politics": "Politics",
    "science_&_technology": "Technology",
    "business_&_entrepreneurs": "Business",
    "health": "Health",
    "family": "General News",
    "education": "General News",
    "diaries_&_daily_life": "General News",
    "film_tv_&_video": "Entertainment",
    "environmental_issues": "World News",
    "other": "General News"
}

def classify_headline(text):
    result = model(text, top_k=3)
    best = max(result, key=lambda x: x["score"])
    label = best["label"]
    score = best["score"]
    category = label_mapping.get(label, "General News")

    if score < 0.5 and any(word in text.lower() for word in tragedy_keywords):
        category = "World News"

    return category, label, score
