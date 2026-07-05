import os
import json
import time
import hashlib
import requests
from dotenv import load_dotenv
from markdownify import markdownify as md
from google import genai
from google.genai import types

# Tải biến môi trường từ file .env
load_dotenv()

# CẤU HÌNH HỆ THỐNG
API_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json?per_page=30"
OUTPUT_DIR = "Data"
STATE_FILE = os.path.join("state_dir", "state.json")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
STORE_NAME = os.environ.get("GEMINI_STORE_NAME")

# Khởi tạo client Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# CÁC HÀM HỖ TRỢ
def load_state():
    """Đọc trạng thái từ file JSON (Lịch sử các file đã upload)"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    """Lưu trạng thái mới nhất vào file JSON"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def get_content_hash(text):
    """Tạo mã băm (hash) để nhận diện nội dung thay đổi"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def clean_html_to_markdown(html_content):
    """Chuyển đổi HTML sang Markdown"""
    return md(html_content, heading_style="ATX", strip=['script', 'style'])

def upload_to_gemini(file_path, display_name):
    """Upload file lên Gemini File Search Store có cơ chế Retry"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  ☁️ Đang upload lên Gemini: {display_name}...")
            operation = client.file_search_stores.upload_to_file_search_store(
                file=file_path,
                file_search_store_name=STORE_NAME,
                config={'display_name': display_name, 'mime_type': 'text/markdown'}
            )
            while not operation.done:
                time.sleep(1)
                operation = client.operations.get(operation)
            
            return "uploaded" 
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Lỗi upload. Thử lại sau 2s...")
                time.sleep(2)
            else:
                print(f"Thất bại khi upload {display_name}: {e}")
                return None

# MAIN
def main():
    print("BẮT ĐẦU CHẠY JOB ĐỒNG BỘ DỮ LIỆU TỪ ZENDESK...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    state = load_state()
    response = requests.get(API_URL)
    
    if response.status_code != 200:
        print(f"Lỗi khi lấy dữ liệu từ Zendesk: {response.status_code}")
        return

    articles = response.json().get('articles', [])[:30] # Giới hạn 30 bài
    print(f"Đã tải danh sách {len(articles)} bài viết từ website.\n")

    # Khởi tạo bộ đếm
    counts = {"added": 0, "updated": 0, "skipped": 0}

    for article in articles:
        article_id = str(article.get('id'))
        title = article.get('title', 'Untitled')
        html_body = article.get('body', '')
        url = article.get('html_url', '')
        
        if not html_body:
            continue
            
        slug = url.split('/')[-1] if url else title.replace(' ', '-').lower()
        
        # 1. TÍNH TOÁN HASH ĐỂ SO SÁNH (DETECT DELTA)
        current_hash = get_content_hash(html_body)
        status = "new"

        if article_id in state:
            if state[article_id]['hash'] == current_hash:
                counts["skipped"] += 1
                status = "skipped"
            else:
                counts["updated"] += 1
                status = "updated"
        else:
            counts["added"] += 1

        if status == "skipped":
            continue

        # 3. XỬ LÝ NẾU LÀ FILE MỚI HOẶC BỊ CẬP NHẬT
        print(f"🔄 Đang xử lý [{status.upper()}]: {slug}")
        
        # Tạo Markdown
        markdown_content = f"# {title}\n\n" + clean_html_to_markdown(html_body)
        md_file_path = os.path.join(OUTPUT_DIR, f"{slug}.md")
        
        with open(md_file_path, "w", encoding="utf-8") as f_md:
            f_md.write(markdown_content)

        # Upload lên Gemini
        upload_result = upload_to_gemini(md_file_path, f"{slug}.md")

        # 4. CẬP NHẬT TRẠNG THÁI (STATE)
        if upload_result:
            state[article_id] = {
                "hash": current_hash,
                "slug": slug,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            save_state(state) 

    # TỔNG KẾT 
    print("\n" + "="*40)
    print("TỔNG KẾT KẾT QUẢ JOB:")
    print(f"  🟢 Thêm mới (Added):   {counts['added']}")
    print(f"  🟡 Cập nhật (Updated): {counts['updated']}")
    print(f"  ⚪ Bỏ qua (Skipped):   {counts['skipped']}")
    print("="*40)
    print("Job hoàn thành thành công!")

if __name__ == "__main__":
    main()