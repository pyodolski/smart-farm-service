#!/usr/bin/env python3
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    
    print("=== sensor_log 테이블 구조 확인 ===")
    
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'sensor_log'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    if columns:
        print("\n컬럼 목록:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]}")
    else:
        print("❌ sensor_log 테이블이 존재하지 않습니다.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
