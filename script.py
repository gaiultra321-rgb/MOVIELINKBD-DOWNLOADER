import os
import time
import json
import requests
from pyrogram import Client

# Environment Variables থেকে ডাটা নেওয়া
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
TARGET_URL = os.environ.get("TARGET_URL")

# FlareSolverr এর লোকাল হোস্ট ইউআরএল
FLARESOLVERR_URL = "http://localhost:8191/v1"

app = Client(
    "cf_uploader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def get_cloudflare_cookies(url):
    """FlareSolverr ব্যবহার করে ক্লাউডফ্লেয়ার বাইপাস করা এবং কুকি নেওয়া"""
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }
    try:
        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=65)
        res_data = response.json()
        
        if res_data.get("status") == "ok":
            solution = res_data.get("solution", {})
            cookies = solution.get("cookies", [])
            user_agent = solution.get("userAgent", "")
            return cookies, user_agent
    except Exception as e:
        print(f"FlareSolverr Error: {e}")
    return None, None

async def main():
    async with app:
        await app.send_message(CHANNEL_ID, "⏳ FlareSolverr দিয়ে ক্লাউডফ্লেয়ার ভেরিফিকেশন করা হচ্ছে...")
        
        # ১. ক্লাউডফ্লেয়ার বাইপাস করে কুকি আনা
        cookies, user_agent = get_cloudflare_cookies(TARGET_URL)
        
        if not cookies:
            await app.send_message(CHANNEL_ID, "❌ ক্লাউডফ্লেয়ার বাইপাস করা সম্ভব হয়নি!")
            return

        # ২. কুকি ফাইলটি ডিকশনারি ফরম্যাটে সেভ করা জাতে পরে ব্যবহার করা যায়
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        cookie_file = "cookies.json"
        with open(cookie_file, "w") as f:
            json.dump({"cookies": cookie_dict, "user_agent": user_agent}, f, indent=4)

        # ৩. টেলিগ্রাম চ্যানেলে কুকি ফাইলটি সেন্ড করা (যাতে আপনি পরে মাল্টিপল টাইম ইউজ করতে পারেন)
        await app.send_document(
            chat_id=CHANNEL_ID,
            document=cookie_file,
            caption=f"🍪 Cookies for {TARGET_URL}\nUser-Agent: {user_agent}"
        )

        # ৪. ডাউনলোড সোর্স (এখানে আপনার ওয়েবসাইটের লজিক বা ডিরেক্ট ডাউনলোড লিংক বসাবেন)
        # উদাহরণস্বরূপ আমরা রিকোয়েস্ট দিয়ে ফাইল ডাউনলোড দেখাচ্ছি কুকি সহকারে:
        await app.send_message(CHANNEL_ID, "📥 গিটহাব সার্ভারে ফাইল ডাউনলোড শুরু হয়েছে...")
        
        headers = {"User-Agent": user_agent}
        file_path = "downloaded_resource.zip" # ফাইলের নাম ও এক্সটেনশন আপনার প্রয়োজন মতো দেবেন
        
        # কুকি সহ ফাইল ডাউনলোড করা
        with requests.get(TARGET_URL, cookies=cookie_dict, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # ৫. টেলিগ্রাম চ্যানেলে ফাইল আপলোড (TgCrypto ব্যাকএন্ডে অটোমেটিক স্পিড বাড়িয়ে দেবে)
        await app.send_message(CHANNEL_ID, "📤 টেলিগ্রাম চ্যানেলে আপলোড হচ্ছে...")
        await app.send_document(
            chat_id=CHANNEL_ID,
            document=file_path,
            caption="✅ ডাউনলোড এবং আপলোড সম্পূর্ণ হয়েছে (No Data Lost)!"
        )

        # ৬. ক্লিনআপ (সার্ভার থেকে ফাইল ডিলিট)
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(cookie_file): os.remove(cookie_file)

if __name__ == "__main__":
    app.run(main())
