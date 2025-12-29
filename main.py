import telebot
import requests
import re
import os
from yt_dlp import YoutubeDL
import threading
from flask import Flask
from telebot.types import InputMediaPhoto

TOKEN = '8585002370:AAFXBAT7k5j-6vjD1N6g6h97XGwyusi4Fgo'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

def get_media_with_ydl(url):
    ydl_opts = {
        'quiet': True, 'no_warnings': True,
        'format': 'bestvideo+bestaudio/best', 'socket_timeout': 10
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                return {'type': 'video', 'url': info['url']}
    except:
        return None

def get_media_manual(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        video_links = re.findall(r'https://va\.media\.tumblr\.com/[^"\s<>]+?\.mp4', html)
        if video_links:
            return {'type': 'video', 'url': video_links[0]}

        image_links = re.findall(r'https://\d+\.media\.tumblr\.com/[^"\s<>]+', html)
        valid_photos = []
        for img in list(set(image_links)):
            if any(x in img.lower() for x in ['avatar', 'header', 'logo', 'theme', 'face']):
                continue
            if 's1280' in img or 's2048' in img or '74.media' in img:
                valid_photos.append(img)
        
        if valid_photos:
            return {'type': 'photo', 'urls': valid_photos} # Забираем ВСЕ найденные фото
            
    except:
        pass
    return None

@bot.message_handler(func=lambda message: 'tumblr.com' in message.text)
def handle_link(message):
    url = re.search(r'(https?://[^\s]+)', message.text).group(1)
    msg = bot.reply_to(message, "🔍 Собираю все медиа...")

    try:
        result = get_media_with_ydl(url)
        if not result:
            result = get_media_manual(url)

        if result:
            if result['type'] == 'video':
                bot.send_video(message.chat.id, result['url'], reply_to_message_id=message.message_id)
            elif result['type'] == 'photo':
                photos = result['urls']
                for i in range(0, len(photos), 10):
                    chunk = photos[i:i + 10]
                    media_group = [InputMediaPhoto(img_url) for img_url in chunk]
                    bot.send_media_group(message.chat.id, media_group, reply_to_message_id=message.message_id)
            bot.delete_message(message.chat.id, msg.message_id)
        else:
            bot.edit_message_text("Не удалось найти файлы. Проверьте ссылку.", message.chat.id, msg.message_id)

    except Exception as e:
        # Теперь любая ошибка будет видна в логах Render!
        print(f"!!! ERROR: {e}") 
        bot.edit_message_text(f"❌ Ошибка: {str(e)[:50]}", message.chat.id, msg.message_id)

@server.route("/")
def hello():
    return "OK"

if __name__ == "__main__":
    # skip_pending=True заставит бота игнорировать старые сообщения после пробуждения
    threading.Thread(target=bot.infinity_polling, kwargs={'skip_pending': True}).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host='0.0.0.0', port=port)
