import telebot
import requests
import re
import os
from yt_dlp import YoutubeDL
import threading
from flask import Flask

# Настройки
TOKEN = 'ТВОЙ_ТОКЕН_ЗДЕСЬ'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

def get_tumblr_media(url):
    """Улучшенный метод поиска только нужного медиа"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        html = response.text

        # 1. Ищем видео (теги <source> или ссылки на mp4)
        videos = re.findall(r'https://va\.media\.tumblr\.com/[^"\s<>]+?\.mp4', html)
        if videos:
            # Берем самое первое видео, обычно это оригинал
            return {'type': 'video', 'url': videos[0]}

        # 2. Ищем фото (только крупные оригиналы)
        # Фильтруем ссылки, чтобы там были признаки высокого разрешения (s1280, s2048 или raw)
        images = re.findall(r'https://\d+\.media\.tumblr\.com/[^"\s<>]+', html)
        valid_photos = []
        for img in list(set(images)):
            # Игнорируем аватарки, баннеры и иконки
            if any(junk in img.lower() for junk in ['avatar', 'header', 'logo', 'theme']):
                continue
            # Оставляем только те, что выглядят как основной контент (обычно длинные ID)
            if len(img.split('/')[-1]) > 20: 
                valid_photos.append(img)
        
        if valid_photos:
            return {'type': 'photo', 'urls': valid_photos[:10]} # Лимит 10 фото

    except Exception as e:
        print(f"Ошибка парсинга: {e}")
    return None

@bot.message_handler(func=lambda message: 'tumblr.com' in message.text)
def handle_link(message):
    url = re.search(r'(https?://[^\s]+)', message.text).group(1)
    bot.reply_to(message, "⚙️ Фильтрую контент...")

    result = get_tumblr_media(url)
    
    if not result:
        bot.reply_to(message, "❌ Не удалось найти видео или фото в хорошем качестве.")
        return

    if result['type'] == 'video':
        bot.send_video(message.chat.id, result['url'], caption="Ваше видео готово!")
    
    elif result['type'] == 'photo':
        for img_url in result['urls']:
            try:
                bot.send_photo(message.chat.id, img_url)
            except:
                continue

# Блок для Render (Flask)
@server.route("/")
def hello():
    return "Бот работает!"

if __name__ == "__main__":
    threading.Thread(target=bot.infinity_polling).start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host='0.0.0.0', port=port)
