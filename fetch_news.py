import os
import json
import requests
import google.generativeai as genai
from datetime import datetime, date

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


def fetch_news():
    articles = []
    seen_titles = set()

    def add_articles(resp, label):
        if resp.status_code == 200:
            for a in resp.json().get("articles", []):
                if a.get("title") and a.get("description") and a["title"] not in seen_titles:
                    seen_titles.add(a["title"])
                    articles.append(a)
        else:
            print(f"{label} 오류: {resp.status_code}")

    # ── 관심 주제 키워드 검색 (everything 엔드포인트) ──
    keyword_url = "https://newsapi.org/v2/everything"

    # 국내 키워드
    kr_keywords = "동물학대 OR 동물 학대 OR 환경파괴 OR 살인 OR 갑질 OR 폭행 OR 동물 유기 OR 자연파괴"
    add_articles(requests.get(keyword_url, params={
        "q": kr_keywords,
        "language": "ko",
        "pageSize": 15,
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
    }), "국내 키워드 뉴스")

    # 해외 키워드
    en_keywords = "animal abuse OR animal cruelty OR deforestation OR murder OR environmental destruction OR animal neglect"
    add_articles(requests.get(keyword_url, params={
        "q": en_keywords,
        "language": "en",
        "pageSize": 15,
        "sortBy": "publishedAt",
        "sources": "bbc-news,reuters,the-guardian-uk,associated-press",
        "apiKey": NEWS_API_KEY,
    }), "해외 키워드 뉴스")

    # ── 일반 헤드라인 보충 (키워드 결과가 적을 경우 대비) ──
    add_articles(requests.get("https://newsapi.org/v2/top-headlines", params={
        "country": "kr",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
    }), "국내 헤드라인")

    add_articles(requests.get("https://newsapi.org/v2/top-headlines", params={
        "language": "en",
        "pageSize": 10,
        "sources": "bbc-news,reuters,the-guardian-uk",
        "apiKey": NEWS_API_KEY,
    }), "해외 헤드라인")

    print(f"수집된 기사: {len(articles)}개")
    return articles[:30]


def analyze_with_gemini(articles):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    news_text = "\n\n".join([
        f"[{i+1}] 제목: {a['title']}\n내용: {a.get('description', '')}"
        for i, a in enumerate(articles)
    ])

    prompt = f"""당신은 수십 년간 인류를 관찰해온 냉소적인 연구원입니다.
특히 동물과 자연을 사랑하며, 인간의 잔인함에 깊이 환멸을 느끼고 있습니다.
오늘의 뉴스를 분석하여 '인간 실망 지수'를 산출하는 공식 보고서를 작성합니다.

[채점 가중치 — 아래 항목이 뉴스에 있을수록 점수가 높아집니다]
- 동물 학대 / 동물 유기 / 동물 실험 남용 → 가중치 최상 (+25점)
- 환경 파괴 / 자연 훼손 / 생태계 오염 → 가중치 높음 (+20점)
- 살인 / 폭력 범죄 → 가중치 높음 (+18점)
- 비상식적 갑질 / 공중도덕 무시 / 비매너 행동 → 가중치 중간 (+12점)
- 기타 일반적인 사회 문제 → 가중치 낮음 (+5점)

오늘의 뉴스 목록:
{news_text}

아래 JSON 형식으로만 응답하세요. 다른 텍스트, 마크다운 없이 순수 JSON만:
{{
  "score": 0에서 100 사이의 정수 (높을수록 인류에 더 실망, 평균은 55~65 수준),
  "grade": "등급 문자열 (score 기준: 0-20은 '기적적으로 양호', 21-40은 '그나마 인간적', 41-60은 '예상된 수준', 61-80은 '역시 인간', 81-100은 '인류 멸망 예약됨')",
  "summary": "오늘 인류에 대한 냉소적 총평 2~3문장. 동물과 자연을 사랑하는 관찰자 시점으로.",
  "top_events": [
    {{
      "title": "사건 제목 (한국어, 20자 이내로 요약)",
      "comment": "냉소적 한 줄 코멘트 (30자 이내)",
      "score_impact": 이 사건이 점수에 기여한 수치 (양의 정수)
    }}
  ]
}}
top_events는 위 가중치 기준으로 가장 실망스러운 사건 3개만 포함하세요.
동물 학대나 환경 파괴 관련 사건이 있다면 반드시 top_events에 포함하세요."""

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


def save_results(analysis, articles):
    today = date.today().isoformat()

    # 기사 목록 정리 (필요한 필드만)
    article_list = [
        {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "source": a.get("source", {}).get("name", ""),
            "url": a.get("url", ""),
            "publishedAt": a.get("publishedAt", ""),
        }
        for a in articles
        if a.get("title") and a.get("url")
    ]

    result = {
        "date": today,
        "score": analysis["score"],
        "grade": analysis["grade"],
        "summary": analysis["summary"],
        "top_events": analysis["top_events"],
        "articles": article_list,
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
    save_results(analysis, articles)

    print("\n완료!")
