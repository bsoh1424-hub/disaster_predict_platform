# 해수면 이상 상승 폭풍해일 예측 플랫폼 (Storm Surge Prediction Platform)

> **PRD v0.2 및 시스템 아키텍처 v1.0 설계서 기반 구현 완료**  
> Next.js 프론트엔드, Spring Boot 4.1 서비스 서버, MariaDB, 그리고 FastAPI 딥러닝/RAG 모델 서버를 잇는 연안 재난 방재 예측 시스템

---

## 1. 아키텍처 및 역할 분담 (PRD & 아키텍처 규격 준수)

```
[ 사용자 (지자체/어항/상황실) ]
            ↓ HTTP (3000)
    [ Next.js 16 프론트엔드 ]  (App Router, TypeScript 엄격 모드, 차트 & 근거 패널, RAG 챗봇)
            ↓ REST API (Spring만 호출, FastAPI 직접호출 금지)
   [ Spring Boot 4.1 / Java 21 ]  (포트 8080: 인증/보안, 총수위 환산, 임계초과 판정, 배치 스케줄러, 장애 폴백)
       ↙                  ↘
[ MariaDB 단일 저장소 ]      [ FastAPI 모델 서버 (포트 8000) ]
(10개소 관측소, 임계치,     (수집 모듈: KHOA/KMA 데이터 수집
 관측/예보, 예측결과)         추론 모듈: 12h/24h 잔차 + 초과확률 계산
                             RAG 모듈: 방재 전문가 RAG 질의응답)
```

- **Next.js (포트 3000)**:
  - 사용자 조회 전용. OpenAPI 키 미보유, 브라우저에서 임계 계산 금지(Spring 결과 표시).
  - 1차 표시: **총 수위(예상 조위)** 곡선 (주의보/경보 가이드라인 포함).
  - 근거 표시: **조위 편차(잔차)** 곡선.
  - **만조 겹침 판정 배지(F3)**, **근거 패널(F4)**, **공식 정보 대조 배지(F5)**, **실시간 재계산(A1)**, **방재 RAG 챗봇**.
  - **태풍 사례 백테스트 & 3자 비교 평가 페이지 (`/backtest`)**: 매미(2003), 차바(2016), 힌남노(2022) 벤치마크.
- **Spring Boot 4.1 (포트 8080, Gradle, Java 21 LTS)**:
  - 사용자 API 유일 창구 및 Spring Security (JWT 인증/인가) 탑재.
  - **환산 원칙(PRD Q7)**: `총 수위 = 천문조 예측조위 + 예측 잔차`.
  - 관측소별 임계값(주의보/경보/지역침수문턱) 비교 판정.
  - **매시간 정시 자동 배치 스케줄러** 및 **FastAPI 장애 시 천문조 베이스라인 폴백(잔차 0) 안전망**.
- **FastAPI (포트 8000)**:
  - 수집(KHOA 조위, KMA 수치예보) + 물리-딥러닝 하이브리드 추론 + 방재 RAG 엔진.
  - 계산 및 서빙 전담 (Spring Boot와 API 계약으로 통신).
- **MariaDB (단일 저장소)**:
  - 10개 조위관측소 마스터, 임계치, 관측/예보, 예측 실행 이력(BATCH/REALTIME), 평가 지표 저장.

---

## 2. 전국 10개 주요 조위관측소 및 특보 임계값

| 관측소 코드 | 관측소명 | 해역 | 주의보 총수위 | 경보 총수위 | 지형 특성 |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **BUSAN** | 부산 | 남해 | 183 cm | 214 cm | 남해안 대표 (조차 작음, 월파 취약) |
| **INCHEON** | 인천 | 서해 | 966 cm | 1,004 cm | 서해 대조차 (간만 격차 극심) |
| **PYEONGTAEK** | 평택 | 서해 | 1,010 cm | 1,030 cm | 서해 대조차 항만 |
| **MOKPO** | 목포 | 서해 | 522 cm | 544 cm | 남서해 영산강 하구 |
| **YEOSU** | 여수 | 남해 | 420 cm | 440 cm | 남해안 산업항 |
| **ULSAN** | 울산 | 동해 | 120 cm | 170 cm | 동해남부 연안 |
| **POHANG** | 포항 | 동해 | 109 cm | 150 cm | 동해 (특보 기준 가장 낮음) |
| **BORYEONG** | 보령 | 서해 | 780 cm | 830 cm | 서해 중부 대천 연안 |
| **GUNSAN** | 군산 | 서해 | 740 cm | 790 cm | 서해 금강 하구 |
| **JEJU** | 제주 | 제주 | 280 cm | 310 cm | 제주 해역 |

---

## 3. 원클릭 실행 방법

루트 디렉터리의 배치 스크립트를 통해 서버 3개를 한 번에 실행할 수 있습니다:

### 전체 실행 (원클릭)
```cmd
start_all.bat
```
*(새 콘솔 창 3개가 열리며 FastAPI → Spring Boot → Next.js 순으로 자동 구동됩니다)*

### 개별 수동 실행
1. **FastAPI 모델 서버**:
   ```cmd
   start_fastapi.bat
   # 또는: cd fastapi-model && python app/main.py (포트 8000)
   ```
2. **Spring Boot 백엔드**:
   ```cmd
   start_spring.bat
   # 또는: cd backend && gradlew bootRun (포트 8080)
   ```
3. **Next.js 프론트엔드**:
   ```cmd
   start_frontend.bat
   # 또는: cd frontend && npm run dev (포트 3000)
   ```

---

## 4. 접속 URL 및 계정 정보

- **프론트엔드 대시보드**: [http://localhost:3000](http://localhost:3000)
- **태풍 백테스트 & 평가**: [http://localhost:3000/backtest](http://localhost:3000/backtest)
- **Spring Boot 헬스체크**: [http://localhost:8080/api/health](http://localhost:8080/api/health)
- **FastAPI API 문서**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **기본 관리자 계정**: `admin` / `admin123` (재난상황실 관리자)
- **기본 사용자 계정**: `user` / `user123` (어항관리 담당자)
