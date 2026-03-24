# 인간 실망 지수 — 설정 가이드

## 1단계 — GitHub 저장소 생성

1. GitHub 접속 → **New repository** 클릭
2. Repository name: `human-disappointment-index` (또는 원하는 이름)
3. **Public** 선택 (GitHub Pages 무료 사용을 위해)
4. **Create repository** 클릭
5. 이 폴더의 모든 파일을 해당 저장소에 업로드

---

## 2단계 — API 키 발급

### NewsAPI (뉴스 수집)
1. https://newsapi.org 접속 → 무료 가입
2. 대시보드에서 **API Key** 복사

### Google Gemini API (AI 분석)
1. https://aistudio.google.com 접속 → Google 계정으로 로그인
2. **Get API Key** → **Create API key** 클릭
3. 생성된 키 복사

---

## 3단계 — GitHub Secrets 등록

저장소 페이지에서:
**Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `NEWS_API_KEY` | NewsAPI에서 발급받은 키 |
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 키 |

---

## 4단계 — GitHub Pages 활성화

저장소 페이지에서:
**Settings → Pages → Source: Deploy from a branch → Branch: main / (root) → Save**

잠시 후 `https://{유저명}.github.io/{저장소명}/human-index.html` 로 접속 가능

---

## 5단계 — 첫 실행 테스트

저장소의 **Actions** 탭 → **인간 실망 지수 일일 업데이트** → **Run workflow** 클릭

정상 실행되면 `data/today.json`이 업데이트됩니다.

이후에는 매일 오전 9시(KST)에 자동 실행됩니다.

---

## 파일 구조

```
├── fetch_news.py              # 뉴스 수집 + AI 분석 스크립트
├── requirements.txt           # Python 의존성
├── human-index.html           # 프론트엔드 (GitHub Pages로 서빙)
├── data/
│   ├── today.json             # 오늘의 결과 (자동 업데이트)
│   └── history.json           # 최근 30일 히스토리 (자동 업데이트)
└── .github/workflows/
    └── daily.yml              # GitHub Actions 스케줄러
```

---

## 비용

| 항목 | 비용 |
|---|---|
| GitHub Actions | 무료 (월 2,000분) |
| GitHub Pages | 무료 |
| NewsAPI | 무료 (하루 100건) |
| Google Gemini Flash | 무료 (하루 1,500건) |
| **합계** | **0원** |
