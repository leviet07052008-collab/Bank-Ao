import telebot
import requests
import sqlite3
import random

BOT_TOKEN = 'TOKEN_CUA_BAN'
API_URL = 'http://localhost:4000'
MSB_STK = 'STK_MSB_THAT_CUA_BAN'

bot = telebot.TeleBot(BOT_TOKEN)
conn = sqlite3.connect('bank_ao.db', check_same_thread=False)
c = conn.cursor()

def generate_stk_ao():
    while True:
        stk = '9704' + ''.join([str(random.randint(0, 9)) for _ in range(10)])
        c.execute("SELECT stk_ao FROM users WHERE stk_ao=?", (stk,))
        if not c.fetchone():
            return stk

def get_balance(uid):
    c.execute("SELECT balance FROM users WHERE uid=?", (uid,))
    row = c.fetchone()
    return row[0] if row else 0

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    c.execute("SELECT full_name, stk_ao, balance FROM users WHERE uid=?", (uid,))
    row = c.fetchone()
    if row:
        bot.reply_to(message, f"🏦 BANK ẢO\n"
                              f"👤 Chủ TK: {row[0]}\n"
                              f"💳 STK ảo: {row[1]}\n"
                              f"💰 Số dư: {row[2]:,} VND\n\n"
                              f"📌 /naptien <số tiền>\n"
                              f"📌 /sodu\n"
                              f"📌 /chuyentien <stk_ảo> <số tiền>\n"
                              f"📌 /ruttien <số tiền> <stk_thật> <bank>\n"
                              f"📌 /lsgd")
    else:
        bot.reply_to(message, f"🏦 CHÀO MỪNG ĐẾN BANK ẢO\n"
                              f"Bạn chưa có tài khoản.\n"
                              f"Gõ /dangky <Họ và tên> để tạo tài khoản.\n"
                              f"Ví dụ: /dangky Nguyễn Văn A")

@bot.message_handler(commands=['dangky'])
def dangky(message):
    uid = message.from_user.id
    full_name = message.text.replace('/dangky', '').strip()
    if not full_name:
        bot.reply_to(message, "Cú pháp: /dangky Nguyễn Văn A")
        return
    c.execute("SELECT stk_ao FROM users WHERE uid=?", (uid,))
    if c.fetchone():
        bot.reply_to(message, "✅ Bạn đã có tài khoản rồi. Gõ /start để xem.")
        return
    stk_ao = generate_stk_ao()
    c.execute("INSERT INTO users(uid, full_name, stk_ao, balance) VALUES(?,?,?,0)",
              (uid, full_name, stk_ao))
    conn.commit()
    bot.reply_to(message, f"🎉 ĐĂNG KÝ THÀNH CÔNG!\n\n"
                          f"👤 Chủ TK: {full_name}\n"
                          f"💳 STK ảo: {stk_ao}\n"
                          f"🏦 Ngân hàng: MSB Ảo\n"
                          f"💰 Số dư: 0 VND\n\n"
                          f"📌 NẠP TIỀN:\n"
                          f"CK vào STK THẬT: {MSB_STK}\n"
                          f"KHÔNG CẦN GHI NỘI DUNG\n"
                          f"Sau đó gõ: /naptien <số tiền>\n\n"
                          f"📌 CHUYỂN NỘI BỘ:\n"
                          f"/chuyentien <stk_ảo_nhận> <số tiền>\n\n"
                          f"📌 RÚT TIỀN:\n"
                          f"/ruttien <số tiền> <stk_thật> <bank>")

@bot.message_handler(commands=['naptien'])
def naptien(message):
    uid = message.from_user.id
    try:
        amount = int(message.text.split()[1])
        if amount < 10000:
            bot.reply_to(message, "❌ Tối thiểu 10,000 VND")
            return
        c.execute("SELECT stk_ao FROM users WHERE uid=?", (uid,))
        row = c.fetchone()
        if not row:
            bot.reply_to(message, "❌ Chưa đăng ký. Gõ /dangky <Họ tên>")
            return
        stk_ao = row[0]
        r = requests.get(f"{API_URL}/check?key=kami&t={amount}&stk={MSB_STK}")
        data = r.json()
        if data.get('status') == 2:
            c.execute("UPDATE users SET balance = balance + ? WHERE uid=?", (amount, uid))
            c.execute("INSERT INTO history(uid,type,amount,note) VALUES(?,?,?,?)",
                      (uid, 'nap', amount, f'CK vào STK {MSB_STK}'))
            conn.commit()
            bot.reply_to(message, f"✅ Nạp thành công {amount:,} VND\n"
                                  f"💰 Số dư: {get_balance(uid):,} VND")
        else:
            bot.reply_to(message, f"❌ Chưa thấy CK.\n"
                                  f"CK vào STK: {MSB_STK}\n"
                                  f"Số tiền: {amount:,} VND\n"
                                  f"KHÔNG CẦN GHI NỘI DUNG")
    except Exception as e:
        bot.reply_to(message, f"Lỗi: {e}\nCú pháp: /naptien 100000")

@bot.message_handler(commands=['sodu'])
def sodu(message):
    uid = message.from_user.id
    c.execute("SELECT full_name, stk_ao, balance FROM users WHERE uid=?", (uid,))
    row = c.fetchone()
    if not row:
        bot.reply_to(message, "❌ Chưa đăng ký. Gõ /dangky <Họ tên>")
        return
    bot.reply_to(message, f"👤 {row[0]}\n"
                          f"💳 STK ảo: {row[1]}\n"
                          f"💰 Số dư: {row[2]:,} VND")

@bot.message_handler(commands=['chuyentien'])
def chuyentien(message):
    uid = message.from_user.id
    try:
        parts = message.text.split()
        stk_nhan = parts[1]
        amount = int(parts[2])
        c.execute("SELECT uid, full_name FROM users WHERE stk_ao=?", (stk_nhan,))
        row = c.fetchone()
        if not row:
            bot.reply_to(message, "❌ STK ảo không tồn tại")
            return
        uid_nhan, ten_nhan = row
        if uid == uid_nhan:
            bot.reply_to(message, "❌ Không thể tự chuyển cho mình")
            return
        balance = get_balance(uid)
        if balance < amount:
            bot.reply_to(message, f"❌ Số dư không đủ: {balance:,} VND")
            return
        c.execute("UPDATE users SET balance = balance - ? WHERE uid=?", (amount, uid))
        c.execute("UPDATE users SET balance = balance + ? WHERE uid=?", (amount, uid_nhan))
        c.execute("INSERT INTO history(uid,type,amount,note) VALUES(?,?,?,?)",
                  (uid, 'chuyen_di', amount, f'Đến STK {stk_nhan} - {ten_nhan}'))
        c.execute("INSERT INTO history(uid,type,amount,note) VALUES(?,?,?,?)",
                  (uid_nhan, 'chuyen_den', amount, f'Từ STK {stk_nhan}'))
        conn.commit()
        bot.reply_to(message, f"✅ Đã chuyển {amount:,} VND\n"
                              f"👤 Người nhận: {ten_nhan}\n"
                              f"💳 STK: {stk_nhan}\n"
                              f"💰 Số dư còn: {get_balance(uid):,} VND")
    except Exception as e:
        bot.reply_to(message, f"Lỗi: {e}\nCú pháp: /chuyentien 9704123456789 50000")

@bot.message_handler(commands=['ruttien'])
def ruttien(message):
    uid = message.from_user.id
    try:
        parts = message.text.split()
        amount = int(parts[1])
        stk_nhan = parts[2]
        bank_nhan = parts[3]
        balance = get_balance(uid)
        if balance < amount:
            bot.reply_to(message, f"❌ Số dư không đủ: {balance:,} VND")
            return
        if amount < 50000:
            bot.reply_to(message, "❌ Tối thiểu 50,000 VND")
            return
        bot.reply_to(message, "⏳ Đang xử lý chuyển khoản...")
        result = chuyen_khoan_msb(stk_nhan, bank_nhan, amount, f"RUT_{uid}")
        if result:
            c.execute("UPDATE users SET balance = balance - ? WHERE uid=?", (amount, uid))
            c.execute("INSERT INTO history(uid,type,amount,note) VALUES(?,?,?,?)",
                      (uid, 'rut', amount, f'CK đến {stk_nhan} {bank_nhan}'))
            conn.commit()
            bot.reply_to(message, f"✅ Đã chuyển {amount:,} VND đến {stk_nhan}\n"
                                  f"💰 Số dư còn: {get_balance(uid):,} VND")
        else:
            bot.reply_to(message, "❌ Lỗi chuyển khoản")
    except Exception as e:
        bot.reply_to(message, f"Lỗi: {e}\nCú pháp: /ruttien 100000 123456789 VCB")

@bot.message_handler(commands=['lsgd'])
def lsgd(message):
    uid = message.from_user.id
    c.execute("SELECT type, amount, note, created_at FROM history WHERE uid=? ORDER BY id DESC LIMIT 10", (uid,))
    rows = c.fetchall()
    if not rows:
        bot.reply_to(message, "📭 Chưa có giao dịch nào")
        return
    text = "📋 LỊCH SỬ GIAO DỊCH (10 gần nhất)\n\n"
    for r in rows:
        text += f"🔹 {r[0].upper()}: {r[1]:,} VND\n"
        text += f"   📝 {r[2]}\n"
        text += f"   🕐 {r[3]}\n\n"
    bot.reply_to(message, text)

def chuyen_khoan_msb(stk_nhan, bank_nhan, amount, note):
    print(f"[CHUYEN KHOAN] {amount:,} VND -> {stk_nhan} ({bank_nhan}) | {note}")
    otp = input("Nhap OTP: ")
    print(f"OTP: {otp}")
    return True

if __name__ == "__main__":
    print("Bot dang chay...")
    bot.polling(none_stop=True)