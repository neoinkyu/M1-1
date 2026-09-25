# M1-1 | AI 데이터 분석: 데이터 기반 트렌드 분석

## 프로젝트 개요

옥션슈트(AuctionSuit)는 경매·공매·소송 관련 정보를 제공하는 웹사이트입니다.

본 프로젝트에서는 옥션슈트 운영 과정에서 수집한 Google Search Console, GA4, Google AdSense, WordPress 데이터를 활용하여 검색 유입과 사이트 이용 성과의 변화를 시계열 관점에서 분석했습니다.

분석 과정에서 검색 노출수는 크게 감소했지만 검색 클릭수는 상대적으로 유지되고, CTR과 사용자·페이지뷰·광고수익은 초기보다 높은 수준을 보이는 현상을 확인했습니다.

이에 다음 질문을 중심으로 분석을 수행했습니다.

1. 옥션슈트의 검색·방문·수익 지표는 분석기간 동안 어떻게 변화했는가?
2. 검색 노출 감소는 어떤 페이지와 검색어에서 주로 발생했는가?
3. 검색 노출 감소에도 클릭과 CTR이 상대적으로 유지·개선된 현상은 어떻게 설명할 수 있는가?
4. 사이트 이용량과 AdSense 예상수익은 어떤 관계를 보이는가?

---

## 분석 주제

**옥션슈트 검색 노출 감소는 성과 악화인가?  
검색 유입 구조와 사이트 이용 성과의 시계열 분석**

---

## 분석 데이터

### 데이터 출처

Google Sheets에 자동 수집 중인 옥션슈트 운영 데이터를 사용했습니다.

| 데이터 | 주요 항목 |
|---|---|
| Google Search Console | 클릭, 노출, CTR, 평균 검색순위, 페이지, 검색어 |
| Google Analytics 4 | 사용자, 페이지뷰 |
| Google AdSense | 예상수익 |
| WordPress | 게시물 수 |

### 분석기간

- 2026-06-02 ~ 2026-09-21
- 총 112일
- 일별 시계열 데이터

분석기간은 재현성을 위해 `src/config.py`에서 고정했습니다.

```python
ANALYSIS_START_DATE = "2026-06-02"
ANALYSIS_END_DATE = "2026-09-21"
```

운영용 Streamlit 대시보드는 고정 분석기간과 별도로 Google Sheets의 최신 데이터를 조회합니다.

---

## 주요 분석 방법

- 데이터 타입 변환 및 날짜 정렬
- 결측값·중복 날짜·누락 날짜 확인
- 7일 이동평균
- 28일 구간별 성과 비교
- 요일별 평균 분석
- 페이지별·검색어별 검색성과 증감 분석
- Pearson 상관분석
- 시계열 분해
- Holt-Winters Exponential Smoothing 예측

### 분석 방법 보충 설명

- **28일 구간별 비교**: 전체 112일을 28일씩 4개 구간으로 나누고, 각 구간의 클릭·노출·CTR·사용자·PV·수익 등을 **일평균 값**으로 비교했습니다.
- **페이지·검색어 증감 비교**: 전체 112일 중 초기 28일과 최근 28일을 대상으로 페이지별·검색어별 **누적 노출수와 클릭수 합계**를 직접 비교했습니다.
- **시계열 분해**: 요일성이 예상되어 `period=7`로 설정하고 `Observed = Trend + Seasonal + Residual` 형태의 additive 분해를 적용했습니다.
- **상관분석**: Pearson 상관계수는 관계의 방향과 강도를 기술하기 위해 사용했으며, 일별 시계열의 자기상관과 계절성으로 인해 일반 Pearson 유의성 검정의 독립성 가정이 충족되지 않을 수 있어 별도의 p-value 검정은 수행하지 않았습니다.
- **Holt-Winters 예측**: 최근 관측값에 더 큰 가중치를 두는 지수평활의 특성과 추세·7일 계절성을 함께 반영할 수 있다는 점을 이용해 베이스라인 예측을 수행했습니다.

---

## 주요 분석 결과

### 1. 검색 노출은 크게 감소했지만 사이트 전체 성과는 같은 방향으로 움직이지 않음

28일 구간별 비교에서 검색 노출은 초기 평균 약 3,154회에서 최근 약 1,556회로 크게 감소했습니다.

반면 사용자, 페이지뷰, AdSense 예상수익은 초기 구간보다 최근 구간에서 높은 수준을 기록했습니다.

![28일 구간별 비교](images/09_28day_index_comparison.png)

### 2. 검색 노출 감소는 일부 기존 대형 페이지에 집중

특히 다음과 같은 페이지에서 검색 노출 감소폭이 크게 나타났습니다.

- `land-register-issuance`
- `real-estate-register-issuance`
- `corporate-employee-litigation-representation`
- `real-estate-registration-fee-payment`

![노출 감소 상위 페이지](images/10_top_page_impression_decreases.png)

전체 검색 노출 감소를 사이트 전체의 균등한 하락으로 해석하기보다는 페이지별 구조 변화를 함께 확인할 필요가 있었습니다.

이때 페이지별 감소 수치는 전체 112일의 처음과 끝 하루를 비교한 값이 아니라, **초기 28일(2026-06-02 ~ 2026-06-29)**과 **최근 28일(2026-08-25 ~ 2026-09-21)**의 페이지별 누적 노출수를 비교한 값입니다. 가운데 56일은 이 직접 비교값에는 포함하지 않았습니다.

### 3. 검색 클릭에는 강한 7일 계절성이 존재

검색 클릭 시계열을 분해한 결과 반복적인 7일 주기가 뚜렷하게 나타났습니다.

![검색 클릭 시계열 분해](images/12_clicks_decomposition.png)

특정 하루의 성과보다 이동평균이나 동일 요일 간 비교가 운영 성과 판단에 더 적합할 수 있음을 확인했습니다.

시계열 분해 그래프는 위에서부터 다음을 의미합니다.

- **Observed**: 실제 일별 검색 클릭수
- **Trend**: 단기 변동과 반복 패턴을 완화한 중기 흐름으로, `period=7`에서는 기본적으로 중심 7일 이동평균에 기반해 추정
- **Seasonal**: 7일 주기로 반복된다고 가정한 계절 성분
- **Residual**: Trend와 Seasonal로 설명되지 않는 불규칙한 변동

이번 분석에서 `period=7`은 요일별 패턴이 예상되었기 때문에 사전에 설정했습니다. 따라서 Seasonal 그래프가 정확히 7일마다 반복되는 모습 자체는 `period=7` 설정의 결과입니다. 주간 계절성이 존재한다는 판단은 이 반복 모양만으로 내린 것이 아니라, 실제 요일별 평균 차이와 일별 시계열의 반복 패턴, 계절 성분의 크기를 함께 확인하여 내렸습니다.

additive 방식을 사용한 것은 계절성을 추출하기 위한 필수 조건이어서가 아니라, 이번 데이터의 계절 변동을 현재 클릭 수준의 배수보다 **일정한 절대량이 더해지거나 빠지는 구조**로 단순화해 해석했기 때문입니다.

### 4. 페이지뷰와 AdSense 예상수익은 양의 상관관계를 보임

페이지뷰와 AdSense 예상수익의 Pearson 상관계수는 약 **0.732**로 나타났습니다.

![PV와 AdSense 예상수익](images/11_pv_adsense_relationship.png)

다만 상관관계는 인과관계를 의미하지 않으므로 직접적인 원인으로 해석하지 않았습니다.

또한 본 프로젝트에서는 Pearson 상관계수의 별도 p-value 유의성 검정을 수행하지 않았습니다. 분석 데이터가 연속된 일별 시계열이므로 특정 날짜의 값이 전날·다음 날의 값과 연관되는 자기상관이 있을 수 있고, 7일 계절성도 존재합니다. 일반적인 Pearson p-value 검정은 관측값의 독립성을 전제로 하므로, 본 프로젝트에서는 `r = 0.732`를 **PV와 AdSense 예상수익이 함께 움직이는 정도를 나타내는 기술적 지표**로 해석했습니다.

---

## 시계열 예측

Holt-Winters Exponential Smoothing을 사용하여 검색 클릭수의 7일 계절성을 반영한 14일 예측을 수행했습니다.

마지막 14일을 테스트 데이터로 사용한 백테스트 결과:

**MAE = 9.377**

![검색 클릭 예측](images/13_clicks_forecast.png)

본 예측은 정밀한 미래 클릭수 예측보다는 기존 주간 패턴이 계속된다는 가정에 따른 베이스라인 모델로 해석했습니다.

Holt-Winters Exponential Smoothing을 사용한 이유는 검색 클릭 데이터에서 확인된 **추세와 7일 계절성을 함께 반영**할 수 있고, 지수평활 방식이 일반적으로 **최근 관측값에 더 큰 가중치**를 두기 때문입니다. 복잡한 예측모형보다 구조와 가정을 설명하기 쉬워 이번 과제의 베이스라인 예측에 적합했습니다.

---

## Streamlit 대시보드

분석 결과를 실제 사이트 운영에도 활용할 수 있도록 Streamlit 기반 대시보드를 구현했습니다.

Streamlit은 Python에서 `pip install streamlit`로 설치해 사용하는 데이터 앱 프레임워크입니다. 기존 `pandas`, `matplotlib`, `gspread` 기반 분석 코드를 거의 그대로 재사용하면서 기간 선택, KPI 카드, 탭, 그래프 등의 인터랙티브 UI를 빠르게 구현할 수 있어 이번 과제에 적합했습니다.

Vercel을 사용해 Next.js/React 기반 대시보드를 만드는 것도 가능하지만, 이번 프로젝트의 목적은 복잡한 프론트엔드 웹서비스가 아니라 **Python 분석 결과를 빠르게 탐색하는 대시보드**였습니다. 따라서 별도의 프론트엔드와 API 계층을 구축하는 것보다 Python 중심으로 단순하게 구현·배포할 수 있는 Streamlit을 선택했습니다.

### 주요 기능

- Google Sheets 최신 데이터 조회
- 조회기간 변경
- Google 검색 클릭·노출·CTR·평균순위 확인
- 사용자·페이지뷰 확인
- AdSense 예상수익 확인
- 7일 이동평균 표시
- 검색 성과 / 사이트 이용 / 수익 탭
- 최신 데이터 다시 불러오기

### 배포 주소

https://auctionsuit-dashboard.streamlit.app/

### 대시보드 화면

![AuctionSuit 운영 대시보드](images/14_dashboard_overview.png)

![AuctionSuit 대시보드 기간 변경](images/15_dashboard_interactive.png)

---

## 프로젝트 구조

```text
M1-1/
├─ images/
│  ├─ 01_search_clicks_trend.png
│  ├─ 02_search_impressions_trend.png
│  ├─ 03_website_traffic_trend.png
│  ├─ 04_adsense_revenue_trend.png
│  ├─ 05_search_ctr_trend.png
│  ├─ 06_search_position_trend.png
│  ├─ 07_weekday_clicks.png
│  ├─ 08_weekday_impressions.png
│  ├─ 09_28day_index_comparison.png
│  ├─ 10_top_page_impression_decreases.png
│  ├─ 11_pv_adsense_relationship.png
│  ├─ 12_clicks_decomposition.png
│  ├─ 13_clicks_forecast.png
│  ├─ 14_dashboard_overview.png
│  └─ 15_dashboard_interactive.png
├─ src/
│  ├─ analysis.py
│  ├─ config.py
│  ├─ data_loader.py
│  └─ preprocess.py
├─ app.py
├─ REPORT.md
├─ README.md
├─ requirements.txt
└─ .gitignore
```

`credentials/service_account.json`은 보안상 GitHub 저장소에 포함하지 않습니다.

---

## 실행 방법

### 1. 저장소 복제

```bash
git clone https://github.com/neoinkyu/M1-1.git
cd M1-1
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. Google Sheets 인증

로컬 환경에서는 다음 위치에 Google Cloud 서비스 계정 인증파일이 필요합니다.

```text
credentials/service_account.json
```

해당 인증파일은 `.gitignore`를 통해 GitHub에서 제외했습니다.

Streamlit Community Cloud에서는 Secrets 기능을 통해 인증정보를 관리합니다.

### 4. 분석 실행

```bash
python src/analysis.py
```

분석 결과는 터미널에 출력되며 시각화 결과는 `images/` 폴더에 저장됩니다.

### 5. Streamlit 실행

```bash
streamlit run app.py
```

---

## 사용 기술

| 구분 | 기술 |
|---|---|
| 언어 | Python |
| 데이터 처리 | pandas, numpy |
| 시각화 | matplotlib |
| 시계열 분석 | statsmodels |
| 웹 대시보드 | Streamlit |
| 데이터 연결 | gspread, Google Sheets API |
| 버전 관리 | Git, GitHub |
| 개발환경 | VS Code |

### 주요 Python 패키지 역할

| 패키지 | 역할 |
|---|---|
| pandas | 데이터 전처리, 병합, 집계 및 분석 |
| numpy | 수치 계산 지원 |
| matplotlib | 정적 시각화 |
| statsmodels | 시계열 분해 및 Holt-Winters 예측 |
| gspread | Google Sheets 데이터 조회 |
| streamlit | Python 기반 인터랙티브 웹 대시보드 구현 |

---

## 분석 한계

현재 데이터만으로는 검색 클릭 감소와 사이트 사용자·페이지뷰 증가가 동시에 발생한 원인을 유입 채널별로 설명할 수 없습니다.

향후 GA4의 Organic Search, Direct, Referral, Social 등 유입 채널 데이터를 추가하면 검색 외 유입의 영향을 분석할 수 있습니다.

또한 Google Search Console의 일별 데이터는 Pacific Time 기준이므로 현재 요일 분석은 한국 현지 요일과 직접 일치하지 않습니다. 향후 시간별 데이터를 수집해 한국시간으로 변환할 필요가 있습니다.

검색어 역시 검색 의도별로 체계적으로 분류하지 않았으므로 검색 유입의 질적 변화에 관한 해석은 가설 수준으로 제한했습니다.

---

## AI 활용

생성형 AI는 다음 과정에서 활용했습니다.

- 분석 질문 구조화
- Python 코드 작성 보조
- 오류 원인 분석 및 수정
- 분석 결과 해석 보조
- Streamlit 대시보드 구현
- 보고서 구성 및 문장 정리

AI의 제안을 그대로 사용하지 않고 Python 실행 결과, Google Sheets 원본 데이터, 시각화 결과를 직접 확인해 검증했습니다.

관찰된 사실과 가능한 해석을 구분했으며 상관관계를 인과관계로 해석하지 않았습니다.

---

## 상세 분석 보고서

분석 과정, 결과, 해석, 한계 및 AI 활용 기록은 아래 문서에 정리했습니다.

**[REPORT.md](REPORT.md)**

---

## GitHub Repository

https://github.com/neoinkyu/M1-1
