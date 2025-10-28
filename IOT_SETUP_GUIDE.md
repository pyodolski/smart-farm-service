# 🤖 IoT 촬영 시스템 설정 가이드

## 📋 설정해야 할 것들

### 1️⃣ **네트워크 설정 (필수)**

#### A. Raspberry Pi (IoT 디바이스)의 IP 주소 확인

```bash
# Raspberry Pi에서 실행
hostname -I
# 예: 192.168.1.100
```

#### B. 메인 서버 설정 수정

**파일: `routes/greenhouse.py`**

```python
# 현재 설정 (54번째 줄 근처)
RASPBERRY_PI_IP = "http://192.168.137.9:5002"

# 실제 Raspberry Pi IP로 변경
RASPBERRY_PI_IP = "http://192.168.1.100:5002"  # 실제 IP로 변경!
```

#### C. IoT 디바이스 설정 수정

**파일: `iot_camera_system.py`**

```python
# 현재 설정 (17-18번째 줄)
IMAGE_DIR = "/home/pi/images"
SERVER_BASE_URL = "http://localhost:5001"

# 실제 환경에 맞게 변경
IMAGE_DIR = "/home/pi/images"  # Raspberry Pi 경로 (그대로 사용)
SERVER_BASE_URL = "http://192.168.1.50:5001"  # 메인 서버의 실제 IP로 변경!
```

### 2️⃣ **로컬 테스트 설정 (개발용)**

같은 컴퓨터에서 테스트하려면:

**파일: `routes/greenhouse.py`**

```python
RASPBERRY_PI_IP = "http://localhost:5002"  # 로컬 테스트용
```

**파일: `iot_camera_system.py`**

```python
SERVER_BASE_URL = "http://localhost:5001"  # 로컬 테스트용
```

### 3️⃣ **방화벽 설정**

#### A. 메인 서버 (포트 5001 열기)

```bash
# macOS
sudo pfctl -d  # 방화벽 비활성화 (테스트용)

# Linux
sudo ufw allow 5001
```

#### B. IoT 디바이스 (포트 5002 열기)

```bash
# Raspberry Pi (Linux)
sudo ufw allow 5002
```

### 4️⃣ **필수 패키지 설치**

#### A. 메인 서버

```bash
pip install flask flask-cors psycopg2-binary ultralytics requests
```

#### B. IoT 디바이스 (Raspberry Pi)

```bash
pip install flask requests pillow
```

### 5️⃣ **디렉토리 생성**

#### A. 메인 서버

```bash
mkdir -p test_images
mkdir -p static/uploads/crop_images
```

#### B. IoT 디바이스

```bash
mkdir -p /home/pi/images
```

### 6️⃣ **실행 순서**

#### 1단계: 메인 서버 실행

```bash
# 터미널 1
cd /path/to/farm
source venv/bin/activate
python app.py
```

#### 2단계: IoT 시스템 실행

```bash
# 터미널 2 (또는 Raspberry Pi에서)
cd /path/to/farm
python iot_camera_system.py
```

#### 3단계: 프론트엔드 실행

```bash
# 터미널 3
cd front
npm start
```

### 7️⃣ **연결 테스트**

#### A. IoT 디바이스가 실행 중인지 확인

```bash
curl http://192.168.1.100:5002/capture-command \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"group_id": "1", "iot_id": "1", "action": "capture_and_upload"}'
```

**예상 응답:**

```json
{
  "message": "촬영 명령을 수신했습니다. 처리 중...",
  "status": "processing"
}
```

#### B. 메인 서버가 실행 중인지 확인

```bash
curl http://localhost:5001/api/farms
```

### 8️⃣ **실제 하드웨어 연결 (선택사항)**

#### A. Raspberry Pi 카메라 모듈

**파일: `iot_camera_system.py`의 `capture_image()` 함수 수정**

```python
def capture_image(group_id, iot_id):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"iot_{iot_id}_group_{group_id}_{timestamp}.jpg"
        filepath = os.path.join(IMAGE_DIR, filename)

        # 실제 카메라 사용
        import picamera
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            camera.capture(filepath)

        print(f"📸 이미지 촬영 완료: {filename}")
        return filepath

    except Exception as e:
        print(f"❌ 이미지 촬영 실패: {e}")
        return None
```

**필수 패키지:**

```bash
sudo apt-get install python3-picamera
```

#### B. DHT22 온습도 센서

**파일: `iot_camera_system.py`의 `upload_sensor_data()` 함수 수정**

```python
def upload_sensor_data(iot_id, gh_id):
    try:
        # 실제 센서 사용
        import adafruit_dht
        import board

        dht_device = adafruit_dht.DHT22(board.D4)
        temperature = dht_device.temperature
        humidity = dht_device.humidity

        data = {
            "temperature": temperature,
            "humidity": humidity,
            "timestamp": datetime.now().isoformat(),
            "iot_id": iot_id,
            "gh_id": gh_id
        }

        res = requests.post(SENSOR_UPLOAD_URL, json=data, timeout=10)
        res.raise_for_status()
        print(f"✅ 센서 데이터 업로드: 온도 {temperature}°C, 습도 {humidity}%")
        return True

    except Exception as e:
        print(f"❌ 센서 데이터 전송 실패: {e}")
        return False
```

**필수 패키지:**

```bash
pip install adafruit-circuitpython-dht
sudo apt-get install libgpiod2
```

### 9️⃣ **환경 변수 설정 (권장)**

**.env 파일 생성:**

```bash
# 메인 서버용
RASPBERRY_PI_IP=http://192.168.1.100:5002
SERVER_PORT=5001

# IoT 디바이스용
MAIN_SERVER_URL=http://192.168.1.50:5001
IOT_PORT=5002
```

**코드에서 사용:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

RASPBERRY_PI_IP = os.getenv('RASPBERRY_PI_IP', 'http://localhost:5002')
SERVER_BASE_URL = os.getenv('MAIN_SERVER_URL', 'http://localhost:5001')
```

### 🔟 **문제 해결**

#### 문제 1: "Connection refused"

- 방화벽 확인
- IP 주소 확인
- 포트 번호 확인
- 서버가 실행 중인지 확인

#### 문제 2: "Timeout"

- 네트워크 연결 확인
- 같은 네트워크에 있는지 확인
- 타임아웃 시간 증가 (timeout=30)

#### 문제 3: "YOLO 모델 없음"

```bash
# 모델 파일 확인
ls -la model/
# ripe_straw.pt
# rotten_straw.pt
```

#### 문제 4: "Permission denied"

```bash
# 디렉토리 권한 설정
chmod 755 /home/pi/images
chmod 755 static/uploads/crop_images
```

### ✅ 체크리스트

- [ ] Raspberry Pi IP 주소 확인
- [ ] 메인 서버 IP 주소 확인
- [ ] `routes/greenhouse.py`의 `RASPBERRY_PI_IP` 수정
- [ ] `iot_camera_system.py`의 `SERVER_BASE_URL` 수정
- [ ] 방화벽 포트 5001, 5002 열기
- [ ] 필수 패키지 설치
- [ ] 디렉토리 생성
- [ ] 메인 서버 실행 확인
- [ ] IoT 시스템 실행 확인
- [ ] 연결 테스트 성공
- [ ] 웹 브라우저에서 촬영 버튼 테스트

### 🚀 빠른 시작 (로컬 테스트)

```bash
# 터미널 1: 메인 서버
python app.py

# 터미널 2: IoT 시스템
python iot_camera_system.py

# 터미널 3: 프론트엔드
cd front && npm start

# 브라우저에서 http://localhost:3000 접속
# 농장 상세 페이지 → 촬영 버튼 클릭
```

이제 모든 설정이 완료되었습니다! 🎉
