import psycopg2
import os
# from dotenv import load_dotenv  # 주석 처리

# load_dotenv()  # 주석 처리

# PostgreSQL 연결 정보
DB_CONFIG = {
    'host': 'dpg-d2phrcn5r7bs739nu8jg-a',
    'user': 'smartfarm_0587_user',
    'password': 'EYm1AUJZvOzCdD9wMCIFwjVDnQYNXYe6',  # 올바른 비밀번호
    'database': 'smartfarm_0587',
    'port': 5432
}

def create_tables():
    try:
        # PostgreSQL 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ PostgreSQL 데이터베이스에 연결되었습니다.")
        
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
        
        print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
        
        # 생성된 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\n📋 생성된 테이블 목록:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_tables()
