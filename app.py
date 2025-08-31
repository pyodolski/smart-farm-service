# app.py
import os
import psycopg2
from flask import Flask, request, session, jsonify, render_template
from flask_cors import CORS

# 기본 블루프린트만 임포트
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

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# CORS 허용
CORS(app,
     resources={r"/*": {"origins": ["http://localhost:3000", "https://smart-farm-hub.app"]}},
     supports_credentials=True)

# 기본 블루프린트만 등록
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
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)