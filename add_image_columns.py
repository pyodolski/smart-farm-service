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
    
    print("📊 crop_groups 테이블에 이미지 관련 컬럼 추가 중...")
    
    cur = conn.cursor()
    
    # last_image_path 컬럼 추가
    try:
        cur.execute("""
            ALTER TABLE crop_groups 
            ADD COLUMN IF NOT EXISTS last_image_path VARCHAR(255)
        """)
        print("✅ last_image_path 컬럼 추가 완료")
    except Exception as e:
        print(f"⚠️ last_image_path 컬럼 추가 실패 (이미 존재할 수 있음): {e}")
    
    # last_analysis_result 컬럼 추가
    try:
        cur.execute("""
            ALTER TABLE crop_groups 
            ADD COLUMN IF NOT EXISTS last_analysis_result JSONB
        """)
        print("✅ last_analysis_result 컬럼 추가 완료")
    except Exception as e:
        print(f"⚠️ last_analysis_result 컬럼 추가 실패 (이미 존재할 수 있음): {e}")
    
    conn.commit()
    conn.close()
    
    print("🎉 테이블 업데이트 완료!")
    
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
