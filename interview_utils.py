from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_answer(answer, ideal_answer, keywords):
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([answer, ideal_answer])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    keyword_list = [word.strip().lower() for word in keywords.split("|")]
    answer_lower = answer.lower()
    matched_words = [word for word in keyword_list if word in answer_lower]
    missing_words = [word for word in keyword_list if word not in answer_lower]

    keyword_score = len(matched_words) / len(keyword_list)
    score = round((similarity * 0.6 + keyword_score * 0.4) * 100)
    word_count = len(answer.split())

    if matched_words:
        strength = "You included: " + ", ".join(matched_words) + "."
    else:
        strength = "You attempted the question and created a starting point."

    if word_count < 25:
        improvement = "Make the answer longer and include a short example."
    elif missing_words:
        improvement = "Connect your experience to the missing ideas below."
    else:
        improvement = "Keep the same content, but practise saying it naturally and clearly."

    missing_text = ", ".join(missing_words) if missing_words else "No major ideas are missing."

    return {
        "score": min(score, 100),
        "matched": len(matched_words),
        "total": len(keyword_list),
        "word_count": word_count,
        "strength": strength,
        "improvement": improvement,
        "missing_text": missing_text
    }


def get_overall_feedback(answer_result, video_result, confidence):
    answer_score = answer_result["score"]
    camera_score = video_result["cue_score"] if video_result else 50
    confidence_score = confidence * 20
    overall = round(answer_score * 0.6 + camera_score * 0.25 + confidence_score * 0.15)

    if overall >= 75:
        level = "Strong start"
    elif overall >= 55:
        level = "Developing"
    else:
        level = "More practice needed"

    strength = answer_result["strength"]
    if video_result is None:
        next_step = "Try the video analysis, then practise the answer aloud one more time."
    elif answer_score < camera_score:
        next_step = "Improve the content by adding the missing ideas and one clear example."
    else:
        next_step = "Practise calm delivery, eye contact, and a steady speaking pace."

    return {"overall": overall, "level": level, "strength": strength, "next_step": next_step}
