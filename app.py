# app.py
import os
import pymysql  # psycopg2 대신 pymysql 사용
from flask import Flask, request, session, jsonify, render_template
from flask_cors import CORS
from config import DB_CONFIG

# 블루프린트 임포트
from routes.user import user_bp
from routes.admin import admin_bp
from routes.farm import farm_bp
from routes.post import post_bp
from routes.product import product_bp
# from routes.greenhouse import greenhouse_bp
from routes.notification import notification_bp
from routes.sensor import sensor_bp

# MySQL 연결 함수
def get_db_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"DB 연결 실패: {e}")
        return None

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')

# CORS 허용
CORS(app,
     resources={r"/*": {"origins": ["http://localhost:3000", "https://smart-farm-hub.app", "https://smart-farm-ignore.vercel.app"]}},
     supports_credentials=True)

# 루트 경로 추가
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
# app.register_blueprint(greenhouse_bp, url_prefix='/api/greenhouses')  # 주석 처리
app.register_blueprint(notification_bp)
app.register_blueprint(sensor_bp)

# 서버 실행
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)