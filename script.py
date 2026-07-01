import os
import sys
import time
import json
from curl_cffi import requests
from pyrogram import Client

# সব আউটপুট ফাইলে সেভ করার জন্য সিস্টেম (গিটহাব এরর ট্র্যাকিং)
log_file = open("script_output.log", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_URL = os.environ.get("TARGET_URL")

channel_raw = os.environ.get("CHANNEL_ID").strip()
if (channel_raw.startswith("-") and channel_raw[1:].isdigit()) or channel_raw.isdigit():
    CHANNEL_ID = int(channel_raw)
else:
    CHANNEL_ID = channel_raw

app = Client("cf_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def main():
    async with app:
        print("[INFO] Bot session started in GitHub Runner.")
        print(f"[INFO] Visiting URL: {TARGET_URL}")
        
        file_path = "downloaded_resource.zip"
        
        try:
            # ক্লাউডফ্লেয়ার বাইপাস ট্রাই করা
            r = requests.get(TARGET_URL, impersonate="chrome", stream=True, timeout=90)
            r.raise_for_status()
            
            print("[SUCCESS] Cloudflare bypass achieved. Extracting cookies...")
            cookies = r.cookies.get_dict()
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            # কুকি সংরক্ষণ
            cookie_file = "cookies.json"
            with open(cookie_file, "w") as f:
                json.dump({"cookies": cookies, "user_agent": user_agent}, f, indent=4)
                
            await app.send_document(CHANNEL_ID, document=cookie_file, caption=f"🍪 Cookies Extracted for {TARGET_URL}")
            print("[INFO] Cookies.json sent to telegram channel.")

            print("[INFO] Starting file download on GitHub Runner...")
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1048576): # ফাস্টার রাইটিংয়ের জন্য ১ মেগাবাইট চাঙ্ক
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            print(f"[DOWNLOAD] Progress: {round(downloaded * 100 / total_size, 2)}% ({downloaded}/{total_size} bytes)")
            
            print("[SUCCESS] Download completed. Uploading file to Telegram...")
            await app.send_document(
                chat_id=CHANNEL_ID,
                document=file_path,
                caption=f"✅ Download & Upload Successful!\nSource: {TARGET_URL}"
            )
            print("[SUCCESS] File successfully sent to telegram.")
            
        except Exception as e:
            print(f"[CRITICAL ERROR] Script crashed during process: {str(e)}")
            raise e # ওয়ার্কফ্লোকে এরর স্টেট জানানোর জন্য
            
        finally:
            if os.path.exists(file_path): os.remove(file_path)
            if os.path.exists("cookies.json"): os.remove("cookies.json")
            print("[INFO] Cleanup finished.")

if __name__ == "__main__":
    try:
        app.run(main())
    finally:
        log_file.close()
