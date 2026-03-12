import flet as ft
import datetime
import time
import threading
from gtts import gTTS
import os
import sqlite3
import sys

def get_db_path():
    # مسار قاعدة البيانات لضمان اشتغالها على الأندرويد
    data_dir = os.path.abspath(".")
    return os.path.join(data_dir, "reminders.db")

def init_db():
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       text TEXT, 
                       time TEXT, 
                       repeat INTEGER)''')
    conn.commit()
    return conn

db_conn = init_db()

def main(page: ft.Page):
    page.title = "مساعد عبد الله الذكي"
    page.rtl = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.ADAPTIVE

    # مشغل الصوت الأصلي لـ Flet (بديل pygame)
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    active_reminders = []

    def speak_out(text):
        try:
            tts = gTTS(text=text, lang='ar')
            filename = f"voice_{int(time.time())}.mp3"
            temp_path = os.path.join(os.path.abspath("."), filename)
            tts.save(temp_path)
            
            audio_player.src = temp_path
            audio_player.update()
            audio_player.play()
        except: pass

    def load_reminders():
        active_reminders.clear()
        cursor = db_conn.cursor()
        cursor.execute("SELECT id, text, time, repeat FROM reminders")
        rows = cursor.fetchall()
        for row in rows:
            active_reminders.append({"id": row[0], "text": row[1], "time": row[2], "repeat": bool(row[3])})
        update_ui()

    def update_ui():
        reminders_list_column.controls.clear()
        for r in active_reminders:
            reminders_list_column.controls.append(
                ft.Card(content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.ALARM),
                    title=ft.Text(r['text']),
                    subtitle=ft.Text(f"الموعد: {r['time']}"),
                    trailing=ft.IconButton(ft.Icons.DELETE, on_click=lambda e, rid=r['id']: delete_reminder(rid))
                ))
            )
        page.update()

    def add_reminder(e):
        if txt_input.value and tm_input.value:
            cursor = db_conn.cursor()
            cursor.execute("INSERT INTO reminders (text, time, repeat) VALUES (?, ?, ?)", 
                           (txt_input.value, tm_input.value, int(repeat_switch.value)))
            db_conn.commit()
            load_reminders()

    def delete_reminder(reminder_id):
        cursor = db_conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        db_conn.commit()
        load_reminders()

    def check_reminders():
        while True:
            now = datetime.datetime.now().strftime("%H:%M")
            for r in active_reminders[:]:
                if r['time'] == now:
                    speak_out(r['text'])
                    if not r['repeat']: delete_reminder(r['id'])
                    time.sleep(61)
            time.sleep(10)

    txt_input = ft.TextField(label="الجملة")
    tm_input = ft.TextField(label="الوقت (14:30)")
    repeat_switch = ft.Switch(label="تكرار يومي")
    reminders_list_column = ft.Column()

    page.add(
        ft.Text("مساعد عبد الله", size=30, weight="bold"),
        txt_input, tm_input, repeat_switch,
        ft.ElevatedButton("إضافة التنبيه", on_click=add_reminder),
        reminders_list_column
    )

    load_reminders()
    threading.Thread(target=check_reminders, daemon=True).start()

ft.app(target=main)
