import os
import json
import requests
import google.generativeai as genai
from datetime import datetime, date

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def fetch_news():
    articles = []
    url = "https://newsapi.org/v2/top-headlines"

    # 국내 뉴스
    resp_kr = requests.get(url, params={
        "country": "kr",
        "pageSize": 15,
        "apiKey": NEWS_API_KEY,
    })

    # 해외 뉴스
    resp_intl = requests.get(url, params={
        "language": "en",
        "pageSize": 15,
        "apiKey": NEWS_API_KEY,
        "sources": "bbc-news,cnn,reuters,the-guardian-uk,associated-press",
    })

    if resp_kr.status_code == 200:
        articles.extend(resp_kr.json().get("articles", []))
    else:
        print(f"국내 뉴스 오류: {resp_kr.status_code} {resp_kr.text}")

    if resp_intl.status_code == 200:
        articles.extend(resp_intl.json().get("articles", []))
    else:
        print(f"해외 뉴스 오류: {resp_intl.status_code} {resp_intl.text}")

    # 제목/설명 없는 항목 제거
    articles = [a for a in articles if a.get("title") and a.get("description")]
    print(f"수집된 기사: {len(articles)}개")
    return articles[:25]


def analyze_with_gemini(articles):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    news_text = "\n\n".join([
        f"[{i+1}] 제목: {a['title']}\n내용: {a.get('description', '')}"
        for i, a in enumerate(articles)
    ])

    prompt = f"""당신은 수십 년간 인류를 관찰해온 냉소적인 연구원입니다.
오늘의 뉴스를 분석하여 '인간 실망 지수'를 산출하는 공식 보고서를 작성합니다.

오늘의 뉴스 목록:
{news_text}

아래 JSON 형식으로만 응답하세요. 다른 텍스트, 마크다운 없이 순수 JSON만:
{{
  "score": 0에서 100 사이의 정수 (높을수록 인류에 더 실망, 평균은 55~65 수준),
  "grade": "등급 문자열 (score 기준: 0-20은 '기적적으로 양호', 21-40은 '그나마 인간적', 41-60은 '예상된 수준', 61-80은 '역시 인간', 81-100은 '인류 멸망 예약됨')",
  "summary": "오늘 인류에 대한 냉소적 총평 2~3문장. 마치 외계인이 지구를 관찰하는 듯한 톤으로.",
  "top_events": [
    {{
      "title": "사건 제목 (한국어, 20자 이내로 요약)",
      "comment": "냉소적 한 줄 코멘트 (30자 이내)",
      "score_impact": 이 사건이 점수에 기여한 수치 (양의 정수)
    }}
  ]
}}
top_events는 가장 실망스러운 사건 3개만 포함하세요."""

    response = model.generate_content(prompt)
    text = response.text.strip()

    # 마크다운 코드블록 제거
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    return json.loads(text)


def save_results(analysis):
    today = date.today().isoformat()

    result = {
        "date": today,
        "score": analysis["score"],
        "grade": analysis["grade"],
        "summary": analysis["summary"],
        "top_events": analysis["top_events"],
        "updated_at": datetime.now().isoformat(),
    }

    os.makedirs("data", exist_ok=True)

    # 오늘 결과 저장
    with open("data/today.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("data/today.json 저장 완료")

    # 히스토리에 추가
    history_file = "data/history.json"
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    history = [h for h in history if h.get("date") != today]
    history.append(result)
    history = sorted(history, key=lambda x: x["date"])[-30:]

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print("data/history.json 저장 완료")


if __name__ == "__main__":
    print("=" * 40)
    print("인간 실망 지수 산출 시작")
    print("=" * 40)

    print("\n[1/3] 뉴스 수집 중...")
    articles = fetch_news()

    print("\n[2/3] Gemini 분석 중...")
    analysis = analyze_with_gemini(articles)
    print(f"오늘의 인간 실망 지수: {analysis['score']}점 ({analysis['grade']})")

    print("\n[3/3] 결과 저장 중...")
    save_results(analysis)

    print("\n완료!")
