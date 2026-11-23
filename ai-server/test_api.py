import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
KMA_KEY = os.environ.get("KMA_AUTH_KEY")

def test_buoy():
    if not KMA_KEY:
        print("KMA_AUTH_KEY가 없어. .env에 키가 들어갔는지 확인해봐.")
        return

    # 부이 자료는 30분마다 나오니까, 1시간 전으로 잡아야 안전해
    tm = (datetime.now() - timedelta(hours=1)).strftime("%Y%m%d%H%M")

    url = "https://apihub.kma.go.kr/api/typ01/url/sea_obs.php"
    params = {
        "tm": tm,
        "stn": 22104,  # 거제도 부이
        "disp": 1,     # 1이면 JSON
        "help": 0,
        "authKey": KMA_KEY,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("요청 자체가 실패했어:", e)
        return

    print("상태코드:", r.status_code)
    print(r.text[:1500])

    if r.status_code == 200 and "22104" in r.text:
        print("성공! 부이 데이터가 왔어.")
    elif r.status_code == 401:
        print("401이야. 키가 틀렸거나 .env에 잘못 들어갔어.")
    elif r.status_code == 403:
        print("403이야. 해양관측 API 활용신청을 안 했을 가능성이 커.")


DATA_KEY = os.environ.get("DATA_GO_KR_KEY")

def test_warning():
    if not DATA_KEY:
        print("DATA_GO_KR_KEY가 없어. .env에 data.go.kr 키가 들어갔는지 확인해봐.")
        return

    url = "https://apis.data.go.kr/1360000/WthrWrnInfoService/getWthrWrnList"
    params = {
        "ServiceKey": DATA_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "dataType": "JSON",
        "fromTmFc": "20261117",
        "toTmFc": "20261123",
    }

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("요청 자체가 실패했어:", e)
        return

    print("특보 상태코드:", r.status_code)
    print(r.text[:1500])

    if r.status_code == 200 and "title" in r.text:
        print("성공! 특보 목록이 왔어.")

def test_tide():
    url = "https://apis.data.go.kr/1192136/surveyTideLevel/GetSurveyTideLevelApiService"
    params = {
        "serviceKey": DATA_KEY,
        "type": "json",
        "obsCode": "DT_0005",  # 부산 조위관측소
        "reqDate": "20261123",
        "min": 60,
        "pageNo": 1,
        "numOfRows": 24,
    }

    try:
        r = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print("요청 자체가 실패했어:", e)
        return

    print("조위 상태코드:", r.status_code)
    print(r.text[:1500])

    if r.status_code == 200 and "DT_0005" in r.text:
        print("성공! 부산 조위 데이터가 왔어.")


if __name__ == "__main__":
    test_buoy()
    test_warning()
    test_tide()

