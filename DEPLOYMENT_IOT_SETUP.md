# 🚀 배포 환경 IoT 설정 가이드

## 📋 현재 구조

```
배포된 서버 (Render)
https://smart-farm-ignore.onrender.com
         ↕️
    인터넷
         ↕️
Raspberry Pi (로컬 네트워크)
http://192.168.x.x:5002
```

## ⚠️ 문제점

Raspberry Pi는 로컬 네트워크에 있어서 배포된 서버에서 직접 접근할 수 없습니다.

## ✅ 해결 방법: ngrok 사용

### 1️⃣ **ngrok 설치 (Raspberry Pi에서)**

```bash
# ngrok 다운로드
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz

# 압축 해제
tar xvzf ngrok-v3-stable-linux-arm.tgz

# 실행 권한 부여
chmod +x ngrok

# ngrok 이동
sudo mv ngrok /usr/local/bin/
```

### 2️⃣ **ngrok 계정 생성 및 인증**

1. https://ngrok.com 에서 무료 계정 생성
2. 인증 토큰 복사
3. Raspberry Pi에서 인증:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 3️⃣ **IoT 시스템 실행**

```bash
# 터미널 1: IoT Flask 서버 실행
cd /path/to/farm
python iot_camera_system.py
```

### 4️⃣ **ngrok 터널 시작**

```bash
# 터미널 2: ngrok 실행
ngrok http 5002
```

**출력 예시:**

```
Session Status                online
Account                       your_account (Plan: Free)
Version                       3.0.0
Region                        Asia Pacific (ap)
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5002
```

### 5️⃣ **백엔드 설정 업데이트**

ngrok URL을 복사하여 환경 변수에 설정:

**방법 1: .env 파일 사용 (권장)**

`.env` 파일에 추가:

```bash
RASPBERRY_PI_IP=https://abc123.ngrok-free.app
```

**방법 2: 직접 코드 수정**

`routes/greenhouse.py`:

```python
RASPBERRY_PI_IP = "https://abc123.ngrok-free.app"
```

### 6️⃣ **배포된 서버에 환경 변수 설정**

Render 대시보드에서:

1. 프로젝트 선택
2. Environment 탭
3. 환경 변수 추가:
   - Key: `RASPBERRY_PI_IP`
   - Value: `https://abc123.ngrok-free.app`
4. 서버 재배포

## 🔄 전체 플로우 (배포 환경)

```
[웹 브라우저]
    ↓
[Render 서버]
https://smart-farm-ignore.onrender.com
    ↓ POST /api/greenhouses/crop_groups/read
    ↓
    ↓ POST https://abc123.ngrok-free.app/capture-command
    ↓
[ngrok 터널]
    ↓
[Raspberry Pi]
http://localhost:5002
    ↓ 카메라 촬영
    ↓
    ↓ POST https://smart-farm-ignore.onrender.com/api/greenhouses/iot-image-upload
    ↓
[Render 서버]
    ↓ YOLO 분석
    ↓ DB 업데이트
    ↓
[웹 브라우저]
    ↓ 결과 확인
```

## 📝 설정 체크리스트

### Raspberry Pi (IoT 디바이스)

- [ ] `iot_camera_system.py` 실행
- [ ] ngrok 설치 및 인증
- [ ] ngrok 터널 시작 (`ngrok http 5002`)
- [ ] ngrok URL 복사 (예: `https://abc123.ngrok-free.app`)

### 배포 서버 (Render)

- [ ] 환경 변수 `RASPBERRY_PI_IP` 설정
- [ ] 서버 재배포
- [ ] 로그 확인

### 로컬 개발 환경

- [ ] `.env` 파일에 `RASPBERRY_PI_IP` 추가
- [ ] 서버 재시작

## 🧪 테스트

### 1. ngrok 터널 테스트

```bash
curl https://abc123.ngrok-free.app/capture-command \
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

### 2. 배포 서버에서 테스트

```bash
curl https://smart-farm-ignore.onrender.com/api/greenhouses/crop_groups/read \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Cookie: session=YOUR_SESSION" \
  -d '{"group_id": 1, "iot_id": 1}'
```

## ⚡ 빠른 시작 (배포 환경)

```bash
# Raspberry Pi에서

# 1. IoT 시스템 실행
python iot_camera_system.py

# 2. 새 터미널에서 ngrok 실행
ngrok http 5002

# 3. ngrok URL 복사 (예: https://abc123.ngrok-free.app)

# 4. Render 대시보드에서 환경 변수 설정
#    RASPBERRY_PI_IP=https://abc123.ngrok-free.app

# 5. 웹 브라우저에서 테스트
#    https://smart-farm-ignore.onrender.com
```

## 🔒 보안 고려사항

### ngrok 무료 플랜 제한

- URL이 세션마다 변경됨
- 동시 연결 제한
- 대역폭 제한

### 해결 방법

1. **ngrok 유료 플랜**: 고정 URL 사용
2. **포트 포워딩**: 공유기 설정으로 고정 IP 사용
3. **VPN**: Tailscale, ZeroTier 등 사용

## 🛠️ 대안: 로컬 개발 환경

배포 서버 대신 로컬에서 테스트:

```bash
# 터미널 1: 로컬 백엔드
python app.py

# 터미널 2: IoT 시스템
python iot_camera_system.py

# 터미널 3: 프론트엔드
cd front && npm start
```

**설정:**

- `routes/greenhouse.py`: `RASPBERRY_PI_IP = "http://localhost:5002"`
- `iot_camera_system.py`: `SERVER_BASE_URL = "http://localhost:5001"`

## 📞 문제 해결

### ngrok 연결 실패

```bash
# ngrok 상태 확인
curl http://localhost:4040/api/tunnels

# ngrok 재시작
pkill ngrok
ngrok http 5002
```

### Render 서버 로그 확인

```bash
# Render 대시보드 → Logs 탭
# "IoT 명령 전송" 관련 로그 확인
```

### 타임아웃 오류

- ngrok 무료 플랜은 60초 제한
- 촬영 + 업로드 시간 고려
- 타임아웃 설정 증가: `timeout=120`

## ✅ 최종 확인

1. Raspberry Pi에서 `iot_camera_system.py` 실행 중
2. ngrok 터널 활성화 중
3. Render 환경 변수 설정 완료
4. 웹에서 촬영 버튼 클릭 → 정상 작동

완료! 🎉
