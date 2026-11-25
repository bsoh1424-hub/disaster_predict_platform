@echo off
chcp 65001 >nul
REM run_surge_daily.bat — 폭풍해일 잔차 예측 파이프라인 매일 실행 파일
REM 스케줄러가 매일 06:10에 이 파일을 실행해.
REM 이 파일은 껍데기야. 진짜 일은 surge_pipeline.py가 해.
REM
REM 스케줄러 등록 (한 번만):
REM   schtasks /create /tn "SurgePipelineDaily" /tr "C:\project\sample_project\run_surge_daily.bat" /sc daily /st 06:10
REM 스케줄러 확인 (확인할 때마다):
REM   schtasks /query /tn "SurgePipelineDaily"
REM 실행 코드 (직접 돌릴 때):
REM   .\run_surge_daily.bat

REM result 폴더를 먼저 만들어. (파이프라인 파일 확인보다 먼저여야 로그가 안 날아가.)
if not exist result mkdir result

REM surge_pipeline.py가 있는지 확인해.
if not exist surge_pipeline.py (
    echo surge_pipeline.py 파일을 찾지 못했습니다.
    echo 이 bat 파일과 같은 폴더에 surge_pipeline.py가 있는지 확인해 주세요.
    pause
    exit /b 1
)

REM 데이터 파일 확인 — CSV 모드에서만 필요해.
REM   CSV 모드(DATA_MODE="csv")면 merged_busan_1yr.csv가 이 폴더에 있어야 해.
REM   DB 모드(DATA_MODE="db")면 CSV가 필요 없어. DB에서 가져오니까.
REM   그래서 여기서는 CSV가 없어도 멈추지 않아. CSV 모드면 surge_pipeline.py가
REM   파일을 못 찾아서 알려줄 거야.
REM   (★ DB 모드로 바꿀 때 이 bat 파일은 고칠 게 없어. surge_pipeline.py의 DATA_MODE만 "db"로 바꿔.)

echo [%date% %time%] 파이프라인을 시작합니다.
python surge_pipeline.py >> result\daily_log.txt 2>&1
echo [%date% %time%] 파이프라인이 끝났습니다. (종료 코드: %errorlevel%)
echo 자세한 내용은 result\daily_log.txt를 확인해 주세요.
