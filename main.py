import flet as ft
import datetime
import time
import threading
from gtts import gTTS
import os
import sqlite3
import sys

# تحديد مسار تخزين البيانات على الموبايل
def get_db_path():
    if getattr(sys, 'frozen', False): # إذا كان التطبيق محول لبرنامج
        data_dir = os.path.dirname(sys.executable)
    else:
        data_dir = os.path.abspath(".")
    
    # في حالة الأندرويد، Flet بتوفر مسارات خاصة، بس للتبسيط هنخليه في نفس فولدر التطبيق
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
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.scroll = ft.ScrollMode.ADAPTIVE

    # إضافة عنصر الصوت للصفحة
    audio_player = ft.Audio(src="", autoplay=False)
    page.overlay.append(audio_player)

    active_reminders = []

    def speak_out(text):
        try:
            tts = gTTS(text=text, lang='ar')
            filename = f"temp_voice_{int(time.time())}.mp3"
            # حفظ الملف في مكان مؤقت مسموح به
            temp_path = os.path.join(os.path.abspath("."), filename)
            tts.save(temp_path)
            
            # تشغيل الصوت عبر Flet Audio
            audio_player.src = temp_path
            audio_player.update()
            audio_player.play()
            
        except Exception as e:
            print(f"Error: {e}")

    def load_reminders():
        active_reminders.clear()
        cursor = db_conn.cursor()
        cursor.execute("SELECT id, text, time, repeat FROM reminders")
        rows = cursor.fetchall()
        for row in rows:
            active_reminders.append({
                "id": row[0], "text": row[1], "time": row[2], "repeat": bool(row[3])
            })
        update_ui()

    def update_ui():
        reminders_list_column.controls.clear()
        for r in active_reminders:
            reminders_list_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.ALARM, color=ft.Colors.BLUE),
                            title=ft.Text(r['text'], weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"الموعد: {r['time']} {'(يومياً)' if r['repeat'] else ''}"),
                            trailing=ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, rid=r['id']: delete_reminder(rid)
                            ),
                        ),
                        padding=10,
                    )
                )
            )
        page.update()

    def add_reminder(e):
        if txt_input.value and tm_input.value:
            try:
                datetime.datetime.strptime(tm_input.value, "%H:%M")
                cursor = db_conn.cursor()
                cursor.execute("INSERT INTO reminders (text, time, repeat) VALUES (?, ?, ?)", 
                               (txt_input.value, tm_input.value, int(repeat_switch.value)))
                db_conn.commit()
                load_reminders()
                txt_input.value = ""
                tm_input.value = ""
                page.update()
            except:
                pass

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
                    if not r['repeat']:
                        delete_reminder(r['id'])
                    time.sleep(61)
            time.sleep(10)

    txt_input = ft.TextField(label="الجملة", border_radius=10)
    tm_input = ft.TextField(label="الوقت (14:30)", border_radius=10)
    repeat_switch = ft.Switch(label="تكرار يومي", value=False)
    reminders_list_column = ft.Column(spacing=10)

    page.add(
        ft.Text("مساعد عبد الله الصوتي", size=25, weight=ft.FontWeight.BOLD),
        ft.Column([txt_input, tm_input, repeat_switch, ft.FilledButton("إضافة", on_click=add_reminder)]),
        ft.Text("التنبيهات:", size=20),
        reminders_list_column
    )

    load_reminders()
    threading.Thread(target=check_reminders, daemon=True).start()

if __name__ == "__main__":
    ft.app(target=main)