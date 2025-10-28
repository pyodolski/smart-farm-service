# pi_client_v4l2_final.py
# - v4l2-ctl 캡처 해상도 640x480
# - 업로드 URL 경로 수정 (/api/greenhouses/iot-image-upload)
# - BASE_URL을 로컬 테스트 주소로 변경

import time
import requests
import os
from datetime import datetime
import adafruit_dht
import board
import json
import threading
import sys
import subprocess
import pathlib
from gpiozero import PWMOutputDevice

if len(sys.argv) < 2:
    print("❌ 오류: gh_id 인자가 필요합니다.")
    sys.exit(1)

try:
    gh_id = int(sys.argv[1])
    print(f"✅ gh_id 수신 완료: {gh_id}")
except ValueError:
    print("❌ 오류: gh_id는 정수여야 합니다.")
    sys.exit(1)

# --- 베이스 URL 설정 ---
# 로컬 테스트용
BASE_URL = "http://165.229.229.242:5001"

# 배포 환경용 (주석 처리)
# BASE_URL = "https://smart-farm-ignore.onrender.com"

# 서버 코드 분석 결과에 따른 API 경로들
IMAGE_UPLOAD_URL = f"{BASE_URL}/api/greenhouses/iot-image-upload"
SENSOR_UPLOAD_URL = f"{BASE_URL}/product/upload-sensor"
GPS_UPLOAD_URL = f"{BASE_URL}/product/upload-gps"
BATTERY_UPLOAD_URL = f"{BASE_URL}/product/upload-battery"
CONFIG_API_URL = f"{BASE_URL}/api/greenhouses/iot-config"
SEND_IOT_DONE_NOTIFICATION_URL = f"{BASE_URL}/send-notification"

# --------------------
IMAGE_DIR = "/home/pi/images"
IOT_CONFIG_FILE = "/home/pi/iot_config.json"
os.makedirs(IMAGE_DIR, exist_ok=True)

# --- [GPIOZERO] ---
PIN_M2A = 17  # 뒷모터 A (구동)
PIN_M2B = 27  # 뒷모터 B (구동)
PWM_FREQ = 1000  # 1kHz
DRIVE_FORWARD_ON_A = False  # True면 '전진' = M2A PWM
# ------------------

# 장치 초기화
dht_device = adafruit_dht.DHT22(board.D26)

CROP_MAPPING = {
    '1': 'strawberry',
    '2': 'tomato',
    '0': 'empty_space',
    'none': 'unknown_crop'
}

def load_config():
    local_config = {
        "iot_id": 1, 
        "gh_id": 1, 
        "num_rows": 1, 
        "num_cols": 1,
        "grid_data": [], 
        "farm_name": "DefaultFarm", 
        "greenhouse_name": "DefaultGreenhouse"
    }
    
    try:
        if os.path.exists(IOT_CONFIG_FILE):
            with open(IOT_CONFIG_FILE, 'r') as f:
                loaded_from_file = json.load(f)
                local_config.update(loaded_from_file)
            print(f"ℹ️ {IOT_CONFIG_FILE}에서 기존 설정 로드 완료.")
        else:
            print(f"ℹ️ {IOT_CONFIG_FILE} 파일을 찾을 수 없어 초기 기본값 사용.")
    except Exception as e_file:
        print(f"❌ 로컬 파일 설정 로드 실패: {e_file}. 기본값 사용.")
    
    current_gh_id_for_request = local_config.get("gh_id", 1)
    
    try:
        response = requests.get(CONFIG_API_URL, params={'gh_id': current_gh_id_for_request})
        response.raise_for_status()
        server_config_data = response.json()
        print(f"✅ 서버에서 최신 설정 수신.")
        
        local_config.update(server_config_data)
        
        if 'grid_data' in local_config and isinstance(local_config['grid_data'], str):
            try:
                local_config['grid_data'] = json.loads(local_config['grid_data'])
            except json.JSONDecodeError:
                print(f"❌ grid_data 파싱 오류. 기본 빈 리스트 사용.")
                local_config['grid_data'] = []
        
        with open(IOT_CONFIG_FILE, 'w') as f:
            json.dump(local_config, f, indent=4)
        print(f"✅ {IOT_CONFIG_FILE} 파일 갱신 완료.")
        
        return local_config
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 서버에서 설정 수신 실패: {e}. 로컬 파일 설정 사용.")
        return local_config

def capture_and_upload(group_id, iot_id, prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_filename = f"{group_id}_{iot_id}_{timestamp}_{prefix}.jpg"
    filepath = os.path.join(IMAGE_DIR, short_filename)
    
    # --- [V4L2 해상도 640x480] ---
    print(f"📸 v4l2-ctl 640x480 촬영 시작... 저장 위치: {filepath}")
    
    try:
        subprocess.run([
            "v4l2-ctl",
            "-d", "/dev/video0",
            "--set-fmt-video=width=640,height=480,pixelformat=MJPG",
            "--stream-mmap",
            "--stream-skip=8",
            "--stream-to", filepath,
            "--stream-count=1"
        ], check=True, timeout=10)
        print(f"✅ v4l2-ctl 촬영 완료: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"❌ v4l2-ctl 캡처 실패 (CalledProcessError): {e}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ v4l2-ctl 캡처 시간 초과 (10초).")
        return False
    except FileNotFoundError:
        print(f"❌ v4l2-ctl 명령을 찾을 수 없습니다. (v4l-utils 설치 필요)")
        return False
    except Exception as e_capture:
        print(f"❌ v4l2-ctl 캡처 중 알 수 없는 오류: {e_capture}")
        return False
    
    # --------------------------
    try:
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"⚠️ v4l2-ctl이 파일을 생성하지 못했거나 파일이 비어있음: {short_filename}, 업로드 스킵.")
            return False
        
        with open(filepath, "rb") as img_file:
            res = requests.post(
                IMAGE_UPLOAD_URL,
                files={"file": (short_filename, img_file, "image/jpeg")},
                data={
                    "group_id": group_id,
                    "iot_id": iot_id
                }
            )
            res.raise_for_status()
            print(f"✅ 이미지 업로드 성공: {short_filename} (HTTP {res.status_code})")
        
        try:
            os.remove(filepath)
            print(f"🗑️ 업로드된 이미지 삭제: {short_filename}")
        except OSError as e:
            print(f"❌ 이미지 삭제 실패: {short_filename} - {e}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 이미지 업로드 실패: {short_filename} - {e}")
        return False
    except Exception as e:
        print(f"❌ 알 수 없는 오류 발생: {short_filename} - {e}")
        return False

def upload_sensor_data(iot_id_val, gh_id_val):
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
    except RuntimeError as e:
        print(f"❌ 센서 오류 (1차 시도): {e}")
        time.sleep(1)
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity
        except RuntimeError as e:
            print(f"❌ 센서 오류 (2차 시도): {e}")
            temperature = None
            humidity = None
    
    try:
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": datetime.now().isoformat(),
            "iot_id": iot_id_val,
            "gh_id": gh_id_val
        }
        res = requests.post(SENSOR_UPLOAD_URL, json=data)
        print(f"✅ 센서 데이터 업로드: {res.status_code}")
    except Exception as e:
        print(f"❌ 센서 전송 실패: {e}")

def send_iot_done_notification(gh_id, user_id="test2"):
    try:
        payload = {
            "receiver_id": user_id,
            "message": "📷 이미지 탐색이 완료되었습니다.",
            "type": "iot 탐색 종료",
            "image_url": None,
            "target_id": gh_id
        }
        res = requests.post(SEND_IOT_DONE_NOTIFICATION_URL, json=payload)
        res.raise_for_status()
        print("✅ 탐색 종료 알림 전송 완료")
    except Exception as e:
        print(f"❌ 알림 전송 실패: {e}")

# --- [GPIOZERO] ---
def setup_gpiozero():
    print("ℹ️ [GPIOZero] 모터 드라이버 초기화 중...")
    p2a = PWMOutputDevice(PIN_M2A, frequency=PWM_FREQ, initial_value=0)
    p2b = PWMOutputDevice(PIN_M2B, frequency=PWM_FREQ, initial_value=0)
    print("✅ [GPIOZero] 모터 드라이버 초기화 완료.")
    return p2a, p2b

def coast(pA, pB):
    pA.value = 0
    pB.value = 0

def _pulse_on(pA, pB, use_A, speed_pct, duration_s):
    speed = max(0.0, min(1.0, speed_pct / 100.0))
    if use_A:
        pB.value = 0
        pA.value = speed
    else:
        pA.value = 0
        pB.value = speed
    print(f"ℹ️ [GPIOZero] 모터 구동 ({'A' if use_A else 'B'}핀, Speed={speed:.2f}, {duration_s}초)")
    time.sleep(duration_s)
    coast(pA, pB)
    print("ℹ️ [GPIOZero] 모터 정지 (Coast)")

def drive_forward_once(p2a, p2b, speed_pct=60, duration_s=1.0):
    print(f"▶️ [GPIOZero] 1초 전진 (속도: {speed_pct}%)")
    _pulse_on(p2a, p2b, DRIVE_FORWARD_ON_A, speed_pct, duration_s)

# --------------------
# 메인 로직
p2a, p2b = None, None

try:
    config = load_config()
    p2a, p2b = setup_gpiozero()
    
    current_iot_id = config.get("iot_id", 1)
    current_gh_id = config.get("gh_id", 1)
    
    for row_idx in range(1):
        for col_idx in range(1):
            current_row = row_idx
            current_col = col_idx
            
            farm_name = config.get("farm_name", "DefaultFarm")
            greenhouse_name = config.get("greenhouse_name", "DefaultGreenhouse")
            grid_info = config.get("grid_data", [])
            
            crop_type_id = 'none'
            crop_name = CROP_MAPPING['none']
            
            if grid_info and len(grid_info) > current_row and len(grid_info[current_row]) > current_col:
                crop_type_id = str(grid_info[current_row][current_col])
                crop_name = CROP_MAPPING.get(crop_type_id, CROP_MAPPING['none'])
            else:
                print(f"⚠️ 그리드 정보 ({current_row},{current_col})에 작물 데이터가 없거나 유효하지 않습니다. '{CROP_MAPPING['none']}' 사용.")
            
            print(f"\n[메인] 시연 시작: 그리드 ({current_row},{current_col}) 방문, 작물: {crop_name}")
            
            # 1. 전진 1초 수행
            drive_forward_once(p2a, p2b, speed_pct=60, duration_s=1.0)
            print("ℹ️ [메인] 1초 전진 동작 완료. 2초 대기...")
            time.sleep(2)
            
            # 2. 전진 후, 정지 상태에서 1회 촬영
            print("ℹ️ [메인] 정지 상태에서 1회 촬영 시도...")
            # ✅ 수정: group_id, iot_id → current_gh_id, current_iot_id
            capture_and_upload(current_gh_id, current_iot_id, f"capture_after_move_r{current_row}_c{current_col}")
            
            send_iot_done_notification(current_gh_id, user_id="test2")
            upload_sensor_data(current_iot_id, current_gh_id)

except KeyboardInterrupt:
    print("🛑 종료 요청")
finally:
    if p2a and p2b:
        print("ℹ️ [GPIOZero] 모터 리소스 정리 중...")
        coast(p2a, p2b)
        p2a.close()
        p2b.close()
    dht_device.exit()
    print("✅ 종료 및 정리 완료")
