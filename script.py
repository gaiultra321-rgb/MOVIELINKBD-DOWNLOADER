import os
import time
import json
import requests
from pyrogram import Client

# ==== ১. পরিবেশ ভেরিয়েবল থেকে ডাটা সংগ্রহ ====
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TARGET_URL = os.environ.get("TARGET_URL")

# CHANNEL_ID সংখ্যা হলে integer, আর ইউজারনেম (@username) হলে string রাখবে
channel_raw = os.environ.get("CHANNEL_ID").strip()
if (channel_raw.startswith("-") and channel_raw[1:].isdigit()) or channel_raw.isdigit():
    CHANNEL_ID = int(channel_raw)
else:
    CHANNEL_ID = channel_raw

# FlareSolverr এর লোকাল ইউআরএল
FLARESOLVERR_URL = "http://localhost:8191/v1"

# Pyrogram বট ক্লায়েন্ট ইনিশিয়েট করা
app = Client(
    "cf_uploader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ==== ২. ক্লাউডফ্লেয়ার বাইপাস ফাংশন ====
def get_cloudflare_cookies(url):
    """FlareSolverr ব্যবহার করে ক্লাউডফ্লেয়ারের Turnstile বাইপাস করা"""
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

# ==== ৩. মূল কার্যপ্রক্রিয়া (Main Handler) ====
async def main():
    async with app:
        print("Bot started inside workflow...")
        await app.send_message(CHANNEL_ID, "⏳ FlareSolverr দিয়ে ক্লাউডফ্লেয়ার ভেরিফিকেশন করা হচ্ছে...")
        
        # ক্লাউডফ্লেয়ার চ্যালেঞ্জ বাইপাস করা
        cookies, user_agent = get_cloudflare_cookies(TARGET_URL)
        
        if not cookies:
            await app.send_message(CHANNEL_ID, "❌ ক্লাউডফ্লেয়ার বাইপাস করা সম্ভব হয়নি! FlareSolverr ব্যর্থ হয়েছে।")
            return

        # কুকিগুলোকে ডিকশনারি ফরম্যাটে নেওয়া
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        cookie_file = "cookies.json"
        with open(cookie_file, "w") as f:
            json.dump({"cookies": cookie_dict, "user_agent": user_agent}, f, indent=4)

        # টেলিগ্রামে কুকি ফাইলটি ব্যাকআপ হিসেবে পাঠানো
        await app.send_document(
            chat_id=CHANNEL_ID,
            document=cookie_file,
            caption=f"🍪 Cookies for {TARGET_URL}\nUser-Agent: {user_agent}"
        )

        await app.send_message(CHANNEL_ID, "📥 গিটহাব সার্ভারে ফাইল ডাউনলোড শুরু হয়েছে...")
        
        headers = {"User-Agent": user_agent}
        file_path = "downloaded_resource.zip" # ফাইলের নাম ও এক্সটেনশন দরকার হলে চেঞ্জ করতে পারেন
        
        # কুকি ও ইউজার-এজেন্ট সহকারে ফাইল ডাউনলোড করা
        try:
            with requests.get(TARGET_URL, cookies=cookie_dict, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except Exception as e:
            await app.send_message(CHANNEL_ID, f"❌ ফাইল ডাউনলোড করতে সমস্যা হয়েছে: {str(e)}")
            if os.path.exists(cookie_file): os.remove(cookie_file)
            return

        # টেলিগ্রাম চ্যানেলে ফাইল আপলোড (TgCrypto ইনস্টল থাকায় ফুল স্পিড পাবেন)
        await app.send_message(CHANNEL_ID, "📤 টেলিগ্রাম চ্যানেলে আপলোড হচ্ছে...")
        try:
            await app.send_document(
                chat_id=CHANNEL_ID,
                document=file_path,
                caption=f"✅ ডাউনলোড এবং আপলোড সম্পূর্ণ হয়েছে!\nSource: {TARGET_URL}"
            )
        except Exception as e:
            await app.send_message(CHANNEL_ID, f"❌ টেলিগ্রামে আপলোড ব্যর্থ হয়েছে: {str(e)}")

        # গিটহাব রানার থেকে ফাইল ক্লিনআপ করা (ডিলিট করা)
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(cookie_file): os.remove(cookie_file)

if __name__ == "__main__":
    # ডাউনলোডের জন্য ডিরেক্টরি চেক করা
    app.run(main())
