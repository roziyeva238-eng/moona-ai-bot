import telebot
from telebot import types
import requests
import os
from deep_translator import GoogleTranslator

# 1. SOZLAMALAR
TELEGRAM_TOKEN = '8884416865:AAFRPlIkjkKxMALBiD7_G-keQp-SG5qsSrM'
RAPIDAPI_KEY = 'ae9e39d4d7msh5dfd38375890dd0p129279jsn7569f0a2b185'
ADMIN_ID = 8884416865

RAPIDAPI_HOST = "://rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_states = {}

# Foydalanuvchini bazaga qo'shish funksiyasi
def add_user(user_id):
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f:
            f.write("")
    
    with open("users.txt", "r") as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")

# Foydalanuvchilar sonini sanash funksiyasi
def get_users_count():
    if not os.path.exists("users.txt"):
        return 0
    with open("users.txt", "r") as f:
        return len(f.read().splitlines())

# Asosiy menyu
def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_create = types.KeyboardButton("🎵 Musiqa yaratish")
    btn_my_music = types.KeyboardButton("📂 Mening musiqalarim")
    btn_lang = types.KeyboardButton("🌐 Tilni tanlash")
    markup.add(btn_create, btn_my_music)
    markup.add(btn_lang)
    
    # Agar foydalanuvchi admin bo'lsa, unga panel tugmasini ko'rsatish
    if user_id == ADMIN_ID:
        btn_admin = types.KeyboardButton("📊 Admin Panel")
        markup.add(btn_admin)
        
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.from_user.id)  # Yangi odamni ro'yxatga olish
    welcome_text = (
        "Salom! Men Moona — sizning shaxsiy musiqa yaratuvchi AI yordamchingizman. 🎶\n\n"
        "Menga oʻzbekcha yoki inglizcha matn yuboring, men uni qoʻshiqqa aylantiraman!\n"
        "Quyidagi menyudan kerakli boʻlimni tanlang 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(message.from_user.id))

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    text = message.text
    user_id = message.from_user.id

    if text == "🎵 Musiqa yaratish":
        user_states[chat_id] = "waiting_for_prompt"
        bot.send_message(chat_id, "📝 Menga qanday qoʻshiq yaratishni xohlayotganingizni yozing.\n"
                                  "*(Oʻzbekcha yozsangiz ham boʻladi, bot avtomatik tarjima qiladi!)*\n\n"
                                  "Misol: _gʻamgin yomgʻirli ob-havo uchun sokin gitara musiqasi_", parse_mode="Markdown")
        
    elif text == "📂 Mening musiqalarim":
        bot.send_message(chat_id, "🗂 Siz yaratgan musiqalar tarixi tez kunda shu boʻlimda koʻrinadi!")

    elif text == "🌐 Tilni tanlash":
        bot.send_message(chat_id, "🇺🇿 Bot hozircha toʻliq Oʻzbek tilida ishlamoqda!")

    elif text == "📊 Admin Panel" and user_id == ADMIN_ID:
        count = get_users_count()
        bot.send_message(chat_id, f"📊 **Moona AI Bot statistikasi:**\n\n👥 Umumiy foydalanuvchilar soni: **{count} ta**", parse_mode="Markdown")

    # Matnli xabar musiqa yaratish uchun kelganda
    elif user_states.get(chat_id) == "waiting_for_prompt":
        user_states[chat_id] = None
        status_msg = bot.send_message(chat_id, "⏳ Gʻoyangiz tahlil qilinmoqda...")
        
        try:
            # O'zbekcha matnni avtomatik ingliz tiliga o'girish
            bot.edit_message_text("🔄 Matn ingliz tiliga tarjima qilinmoqda...", chat_id=chat_id, message_id=status_msg.message_id)
            translated_prompt = GoogleTranslator(source='auto', target='en').translate(text)
            
            bot.edit_message_text(f"🎵 Suno AI'ga soʻrov yuborildi...\n_(Tarjima: {translated_prompt})_\nIltimos, 1-2 daqiqa kuting.", chat_id=chat_id, message_id=status_msg.message_id)
            
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST,
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": translated_prompt,
                "make_instrumental": False,
                "wait_audio_type": "complete"
            }
            
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, headers=headers)
            
            if response.status_code == 200:
                task_data = response.json()
                if isinstance(task_data, list) and len(task_data) > 0:
                    audio_url = task_data.get("audio_url")
                    title = task_data.get("title", "AI Song")
                    
                    if audio_url:
                        bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
                        bot.send_audio(chat_id=chat_id, audio=audio_url, caption=f"✨ Moona AI tomonidan yaratildi!\n\n📝 **Sizning soʻrovingiz:** {text}\n🎵 **Nomi:** {title}")
                        return
            
            bot.edit_message_text("❌ Musiqa bastalashda xatolik yuz berdi. Birozdan so'ng qayta urining.", chat_id=chat_id, message_id=status_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text("⚠️ Kutilmagan xatolik yuz berdi.", chat_id=chat_id, message_id=status_msg.message_id)
            print(e)
            
    else:
        bot.send_message(chat_id, "Iltimos, menyu tugmalaridan foydalaning.", reply_markup=main_menu(user_id))

print("Yangilangan bot ishga tushdi...")
bot.infinity_polling()
