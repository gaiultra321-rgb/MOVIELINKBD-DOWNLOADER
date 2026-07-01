import os
import sys
import time
import json
from curl_cffi import requests
from pyrogram import Client

# ==== ১. পরিবেশ ভেরিয়েবল থেকে ডাটা সংগ্রহ ====
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_URL = os.environ.get("TARGET_URL")

channel_raw = os.environ.get("CHANNEL_ID").strip()
if (channel_raw.startswith("-") and channel_raw[1:].isdigit()) or channel_raw.isdigit():
    CHANNEL_ID = int(channel_raw)
else:
    CHANNEL_ID = channel_raw

# Pyrogram বট ক্লায়েন্ট
app = Client("cf_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==== ২. টেলিগ্রাম লাইভ লগিং সিস্টেম ====
class TelegramLogger:
    """গিটহাবের ইন্টারনাল লগ এবং প্রিন্ট স্টেটমেন্ট সরাসরি টেলিগ্রামে পাঠাবে"""
    def __init__(self, client, chat_id):
        self.client = client
        self.chat_id = chat_id
        self.terminal = sys.stdout  # আসল টার্মিনাল ব্যাকআপ
        self.log_buffer = ""
        self.last_update = time.time()
        self.log_message = None

    def write(self, message):
        self.terminal.write(message)  # গিটহাব টার্মিনালেও প্রিন্ট হবে
        if message.strip():
            self.log_buffer += f"ℹ️ {message.strip()}\n"
            # প্রতি ৩ সেকেন্ড পর পর টেলিগ্রামের লগ মেসেজটি আপডেট করবে জাতে স্প্যাম না হয়
            if time.time() - self.last_update > 3:
                self.flush_telegram()

    def flush(self):
        self.terminal.flush()
        self.flush_telegram()

    def flush_telegram(self):
        if self.log_buffer and self.client.is_connected:
            try:
                # প্রথমবার মেসেজ ক্রিয়েট করবে, পরের বার এডিট করবে
                if not self.log_message:
                    self.log_message = self.client.send_message(
                        self.chat_id, 
                        f"📋 **Workflow Live Logs:**\n\n{self.log_buffer[-3500:]}" # টেলিগ্রামের ক্যারেক্টার লিমিট ঠিক রাখার জন্য
                    )
                else:
                    self.log_message.edit(f"📋 **Workflow Live Logs:**\n\n{self.log_buffer[-3500:]}")
                self.last_update = time.time()
            except Exception as e:
                self.terminal.write(f"\nLogger Error: {str(e)}\n")

# ==== ৩. মূল কার্যপ্রক্রিয়া (Main Handler) ====
async def main():
    async with app:
        # লাইভ লগ সিস্টেম চালু করা
        logger = TelegramLogger(app, CHANNEL_ID)
        sys.stdout = logger
        sys.stderr = logger

        print("গিটহাব ওয়ার্কফ্লো সফলভাবে শুরু হয়েছে।")
        print("আসল ক্রোম ব্রাউজারের সিগনেচার দিয়ে পেজ ভিজিট করা হচ্ছে...")
        
        file_path = "downloaded_resource.zip"
        
        try:
            # impersonate="chrome" দেওয়ার কারণে ক্লাউডফ্লেয়ার একে আসল ক্রোম মনে করবে
            r = requests.get(TARGET_URL, impersonate="chrome", stream=True, timeout=60)
            r.raise_for_status()
            
            print("ক্লাউডফ্লেয়ার বাইপাস সফল! কুকি এক্সট্রাক্ট করা হচ্ছে...")
            cookies = r.cookies.get_dict()
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            # কুকি ফাইল সেভ এবং আপলোড
            cookie_file = "cookies.json"
            with open(cookie_file, "w") as f:
                json.dump({"cookies": cookies, "user_agent": user_agent}, f, indent=4)
                
            await app.send_document(CHANNEL_ID, document=cookie_file, caption=f"🍪 Cookies Extracted for {TARGET_URL}")
            print("কুকি ফাইল (.json) চ্যানেলে পাঠানো হয়েছে।")

            print("গিটহাব রানার সার্ভারে ফাইল ডাউনলোড শুরু হচ্ছে...")
            
            # ডাউনলোড প্রোগ্রেস ট্র্যাকিং
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=65536): # ফাস্ট ডাউনলোডের জন্য চাঙ্ক সাইজ বাড়ানো হয়েছে
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size and time.time() - start_time > 10: # প্রতি ১০ সেকেন্ড পর পর ডাউনলোডের হিসাব লগে দেখাবে
                            print(f"ডাউনলোড প্রোগ্রেস: {round(downloaded * 100 / total_size, 1)}%")
                            start_time = time.time()
                            
            print("ডাউনলোড সম্পূর্ণ! এখন টেলিগ্রাম চ্যানেলে আপলোড করা হচ্ছে...")
            
            # ফাইলটি চ্যানেলে আপলোড
            await app.send_document(
                chat_id=CHANNEL_ID,
                document=file_path,
                caption=f"✅ ডাউনলোড এবং আপলোড সফলভাবে সম্পন্ন হয়েছে!\nSource: {TARGET_URL}"
            )
            print("অভিনন্দন! ফাইলটি সফলভাবে চ্যানেলে আপলোড হয়েছে।")
            
        except Exception as e:
            print(f"ক্র্যাশ এরর: {str(e)}")
            
        finally:
            print("গিটহাব রানার ক্লিয়ারিং প্রসেস শুরু হচ্ছে...")
            # লগিং বন্ধ করে টার্মিনাল রিলিজ করা
            sys.stdout = logger.terminal
            sys.stderr = logger.terminal
            logger.flush_telegram() # শেষ লগ আপডেট পুশ করা
            
            # ফাইল ডিলিট
            if os.path.exists(file_path): os.remove(file_path)
            if os.path.exists("cookies.json"): os.remove("cookies.json")
            print("ক্লিনআপ সম্পূর্ণ।")

if __name__ == "__main__":
    app.run(main())
