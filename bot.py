import telebot
from telebot import types
import requests

TELEGRAM_TOKEN = '8884416865:AAFRPlIkjkKxMALBiD7_G-keQp-SG5qsSrM'
RAPIDAPI_KEY = 'ae9e39d4d7msh5dfd38375890dd0p129279jsn7569f0a2b185'

RAPIDAPI_HOST = "://rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Foydalanuvchilarning holatini saqlash uchun lug'at (Uchburchak holatlar uchun)
user_states = {}

# Asosiy menyu tugmalarini yaratish funksiyasi
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_create = types.KeyboardButton("🎵 Musiqa yaratish")
    btn_my_music = types.KeyboardButton("📂 Mening musiqalarim")
    btn_lang = types.KeyboardButton("🌐 Tilni tanlash / Language")
    markup.add(btn_create, btn_my_music)
    markup.add(btn_lang)
    return markup

# /start buyrug'i kelganda
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Salom! Men Moona — sizning shaxsiy musiqa yaratuvchi AI yordamchingizman. 🎶\n\n"
        "Quyidagi menyudan oʻzingizga kerakli boʻlimni tanlang 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# Tugmalar bosilganda va matnli xabarlar kelganda ishlash
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🎵 Musiqa yaratish":
        user_states[chat_id] = "waiting_for_prompt"
        bot.send_message(chat_id, "📝 Menga qanday qoʻshiq yaratishni xohlayotganingizni ingliz tilida yozib yuboring.\n\n"
                                  "Misol: *sad acoustic guitar melody* yoki *happy pop synthwave*", parse_mode="Markdown")
        
    elif text == "📂 Mening musiqalarim":
        bot.send_message(chat_id, "🗂 Siz yaratgan musiqalar tarixi tez kunda shu boʻlimda koʻrinadi!")

    elif text == "🌐 Tilni tanlash / Language":
        markup = types.InlineKeyboardMarkup()
        btn_uz = types.InlineKeyboardButton("🇺🇿 Oʻzbekcha", callback_data="lang_uz")
        btn_en = types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")
        markup.add(btn_uz, btn_en)
        bot.send_message(chat_id, "Iltimos, bot tilini tanlang / Please choose bot language:", reply_markup=markup)

    # Agar foydalanuvchi oldin "Musiqa yaratish" tugmasini bosgan bo'lsa va matn yuborayotgan bo'lsa
    elif user_states.get(chat_id) == "waiting_for_prompt":
        user_states[chat_id] = None  # Holatni tozalash
        status_msg = bot.send_message(chat_id, "⏳ Moona AI soʻrovingizni qabul qildi... Musiqa bastalanmoqda, iltimos 1-2 daqiqa kuting.")
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": text,
            "make_instrumental": False,
            "wait_audio_type": "complete"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/generate", json=payload, headers=headers)
            if response.status_code != 200:
                bot.edit_message_text("❌ Musiqa yaratishda xatolik boʻldi. API kalitingiz yoki balansingizni tekshiring.", chat_id=chat_id, message_id=status_msg.message_id)
                return
                
            task_data = response.json()
            if isinstance(task_data, list) and len(task_data) > 0:
                audio_url = task_data[0].get("audio_url")
                title = task_data[0].get("title", "AI Song")
                
                if audio_url:
                    bot.delete_message(chat_id=chat_id, message_id=status_msg.message_id)
                    bot.send_audio(chat_id=chat_id, audio=audio_url, caption=f"✨ Moona AI tomonidan yaratildi:\n🎵 **{title}**")
                else:
                    bot.edit_message_text("⚠️ Musiqa havolasi topilmadi.", chat_id=chat_id, message_id=status_msg.message_id)
            else:
                bot.edit_message_text("😔 AI noto'g'ri ma'lumot qaytardi.", chat_id=chat_id, message_id=status_msg.message_id)
        except Exception as e:
            bot.edit_message_text("⚠️ Kutilmagan xatolik yuz berdi.", chat_id=chat_id, message_id=status_msg.message_id)
            print(e)
            
    else:
        bot.send_message(chat_id, "Tushunmadim. Iltimos, pastdagi menyu tugmalaridan foydalaning.", reply_markup=main_menu())

# Til tanlash tugmalari bosilganda (Inline buttons)
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def callback_language(call):
    if call.data == "lang_uz":
        bot.answer_callback_query(call.id, "Oʻzbek tili tanlandi!")
        bot.send_message(call.message.chat.id, "🇺🇿 Bot tili muvaffaqiyatli oʻzgartirildi!")
    elif call.data == "lang_en":
        bot.answer_callback_query(call.id, "English language selected!")
        bot.send_message(call.message.chat.id, "🇺🇸 Bot language has been successfully changed!")

print("Yangilangan Moona Bot ishga tushdi...")
bot.infinity_polling()
  
