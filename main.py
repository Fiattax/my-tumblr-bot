import telebot
import requests
import re
from yt_dlp import YoutubeDL

TOKEN = '8585002370:AAFXBAT7k5j-6vjD1N6g6h97XGwyusi4Fgo'
bot = telebot.TeleBot(TOKEN)

def get_tumblr_images(url):
    """Метод для поиска картинок напрямую в коде страницы"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        # Ищем ссылки на картинки в высоком качестве
        images = re.findall(r'https://\d+\.media\.tumblr\.com/[^"\s<>]+', response.text)
        # Убираем дубликаты и выбираем только оригиналы (обычно содержат s1280 или s2048)
        unique_images = list(set([img for img in images if 'avatar' not in img]))
        return unique_images[:10] # Возвращаем первые 10 штук
    except:
        return []

@bot.message_handler(func=lambda message: 'tumblr.com' in message.text)
def handle_link(message):
    url = re.search(r'(https?://[^\s]+)', message.text).group(1)
    bot.reply_to(message, "⏳ Магия в процессе...")

    # Сначала пробуем найти картинки нашим "ручным" способом
    images = get_tumblr_images(url)
    
    if images:
        for img_url in images:
            try:
                bot.send_photo(message.chat.id, img_url)
            except:
                continue
        return # Если картинки найдены и отправлены, выходим

    # Если картинок не нашли, пробуем yt-dlp (для видео)
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url') or (info.get('formats')[0].get('url') if info.get('formats') else None)
            if video_url:
                bot.send_video(message.chat.id, video_url)
            else:
                bot.reply_to(message, "Ни видео, ни фото не найдено.")
    except Exception as e:
        bot.reply_to(message, "Не удалось получить медиа. Возможно, пост приватный.")

print("Бот перезапущен с 'ручным' поиском фото!")
bot.infinity_polling()
