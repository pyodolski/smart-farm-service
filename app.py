# app.py
import os
import psycopg2
from flask import Flask, request, session, jsonify, render_template
from flask_cors import CORS

# 블루프린트 임포트
from routes.user import user_bp
from routes.admin import admin_bp
from routes.farm import farm_bp
from routes.post import post_bp
from routes.product import product_bp
from routes.greenhouse import greenhouse_bp
from routes.notification import notification_bp
from routes.sensor import sensor_bp

# PostgreSQL 연결 함수
def get_db_connection():
    try:
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=os.getenv('DB_PORT')
        )
    except psycopg2.Error as e:
        print(f"DB 연결 실패: {e}")
        return None

# 데이터베이스 초기화 함수
def init_database():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # 테이블 생성 SQL
            tables_sql = """
            -- 사용자 테이블
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(50) NOT NULL,
                password VARCHAR(100) NOT NULL,
                nickname VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                name VARCHAR(50) NOT NULL,
                is_black BOOLEAN NOT NULL DEFAULT FALSE,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                kakao_id VARCHAR(64) UNIQUE,
                oauth_provider VARCHAR(16),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id)
            );

            -- 게시판 테이블
            CREATE TABLE IF NOT EXISTS board (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                nickname VARCHAR(50) NOT NULL,
                title VARCHAR(70) NOT NULL,
                content TEXT NOT NULL,
                wdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                view_count INTEGER DEFAULT 0,
                report_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- 댓글 테이블
            CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY,
                board_id INTEGER NOT NULL,
                commenter VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                report_count INTEGER DEFAULT 0,
                cdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES board(id) ON DELETE CASCADE
            );

            -- 좋아요 테이블
            CREATE TABLE IF NOT EXISTS likes (
                id SERIAL PRIMARY KEY,
                board_id INTEGER NOT NULL,
                user_id VARCHAR(50) NOT NULL,
                ldate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (board_id, user_id),
                FOREIGN KEY (board_id) REFERENCES board(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- 농장 테이블
            CREATE TABLE IF NOT EXISTS farms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                location VARCHAR(255),
                owner_username VARCHAR(100),
                document_path VARCHAR(255),
                is_approved BOOLEAN DEFAULT FALSE
            );

            -- 신고 로그 테이블
            CREATE TABLE IF NOT EXISTS report_log (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                target_type VARCHAR(10) CHECK (target_type IN ('post', 'comment')),
                target_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, target_type, target_id)
            );

            -- 온실 테이블
            CREATE TABLE IF NOT EXISTS greenhouses (
                id SERIAL PRIMARY KEY,
                farm_id INTEGER,
                name VARCHAR(100),
                num_rows INTEGER,
                num_cols INTEGER,
                grid_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- IoT 테이블
            CREATE TABLE IF NOT EXISTS iot (
                id SERIAL PRIMARY KEY,
                iot_name VARCHAR(100) NOT NULL,
                owner_id VARCHAR(50) NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                capture_interval VARCHAR(2) CHECK (capture_interval IN ('5', '15', '30')),
                direction VARCHAR(5) CHECK (direction IN ('left', 'right', 'both')),
                resolution VARCHAR(10) CHECK (resolution IN ('640x480', '1280x720', '1920x1080')),
                camera_on BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- 센서 로그 테이블
            CREATE TABLE IF NOT EXISTS sensor_log (
                id SERIAL PRIMARY KEY,
                gh_id INTEGER,
                temperature REAL,
                humidity REAL,
                timestamp TIMESTAMP,
                FOREIGN KEY (gh_id) REFERENCES greenhouses(id) ON DELETE SET NULL
            );

            -- 알림 테이블
            CREATE TABLE IF NOT EXISTS notification (
                id SERIAL PRIMARY KEY,
                receiver_id VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type VARCHAR(20) CHECK (type IN ('iot 탐색 종료', '병해충 발생', '새 댓글', '승인 허가')),
                image_url VARCHAR(255),
                target_id INTEGER NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- 작물 그룹 테이블
            CREATE TABLE IF NOT EXISTS crop_groups (
                id SERIAL PRIMARY KEY,
                greenhouse_id INTEGER NOT NULL,
                group_cells JSONB NOT NULL,
                crop_type INTEGER NOT NULL,
                is_horizontal BOOLEAN NOT NULL,
                harvest_amount INTEGER DEFAULT 0,
                total_amount INTEGER DEFAULT 0,
                is_read BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (greenhouse_id) REFERENCES greenhouses(id) ON DELETE CASCADE
            );
            """
            
            # SQL 실행
            cursor.execute(tables_sql)
            conn.commit()
            
            print("✅ PostgreSQL 테이블이 성공적으로 생성되었습니다!")
            
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# CORS 허용
CORS(app,
     resources={r"/*": {"origins": ["http://localhost:3000", "https://smart-farm-hub.app"]}},
     supports_credentials=True)

# 루트 경로
@app.route('/')
def home():
    return jsonify({
        'message': 'Smart Farm API is running!',
        'status': 'success',
        'endpoints': {
            'users': '/login',
            'posts': '/api/posts',
            'farms': '/api/farms',
            'products': '/product/subscribe'
        }
    })

# 블루프린트 등록
app.register_blueprint(user_bp)
app.register_blueprint(farm_bp)
app.register_blueprint(post_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(product_bp)
app.register_blueprint(greenhouse_bp, url_prefix='/api/greenhouses')
app.register_blueprint(notification_bp)
app.register_blueprint(sensor_bp)

# 서버 실행
if __name__ == '__main__':
    init_database()  # 데이터베이스 초기화
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)