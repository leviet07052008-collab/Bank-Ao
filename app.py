from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time, os
import requests
import pytesseract
from PIL import Image
import capcha
import random

# ============================================================
# SUA 3 DONG NAY
# ============================================================
taikhoan = "SĐT_MSB_CỦA_BẠN"
matkahu = "MẬT_KHẨU_MSB_CỦA_BẠN"
STK_MSB = "STK_MSB_CỦA_BẠN"

token = None
chutaikhoan = None
stkbank = None
cookie = None
loog = False
bodanglogin = False

from flask import Flask, request, jsonify
app = Flask(__name__)

def checkGd(cokiee, tokenno):
    global token, bodanglogin
    url = 'https://ebank.msb.com.vn/IBSRetail/history/byAccount.do'
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': cokiee,
        'Host': 'ebank.msb.com.vn',
        'Origin': 'https://ebank.msb.com.vn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    payload = {
        'queryType': 0,
        'acctNo': STK_MSB,
        'page': 1,
        'tokenNo': str(tokenno),
        'lang': 'vi_VN'
    }
    response = requests.post(url, headers=headers, data=payload)
    print(f"Check GD status: {response.status_code}")
    if response.status_code != 200:
        bodanglogin = True
        login()
        bodanglogin = False
        return None
    return response.json()

def login():
    global token, chutaikhoan, stkbank, cookie
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get("https://ebank.msb.com.vn/IBSRetail/")
        time.sleep(10)
        log = True
        while log:
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, 'img#safecode')
                rand_int = random.randint(1, 10000)
                img_element.screenshot(f'data/{rand_int}img.png')
                capchap = capcha.img(f'data/{rand_int}img.png')
                if len(capchap) < 4:
                    capchap = capchap + capchap[2]
                print(f"Giai captcha: {capchap}")
                def nhapdulieu_byname(name, duliue):
                    input_element = driver.find_element(By.NAME, name)
                    input_element.clear()
                    input_element.send_keys(duliue)
                nhapdulieu_byname("_userName", taikhoan)
                nhapdulieu_byname("_passwordS", matkahu)
                nhapdulieu_byname("_verifyCode", capchap)
                login_button = driver.find_element(By.ID, "loginBtn")
                login_button.click()
                time.sleep(2)
                try:
                    login = driver.find_element(By.ID, "loginBtn")
                    print("Dang nhap that bai, thu lai...")
                except NoSuchElementException:
                    print("Dang nhap MSB thanh cong")
                    log = False
            except Exception as e:
                print("Loi captcha, thu lai:", e)
                continue
        time.sleep(10)
        js_code = "return tokenService.get();"
        token = driver.execute_script(js_code)
        cookies = driver.get_cookies()
        cookie = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        element = driver.find_element(By.CLASS_NAME, 'msb-bank-nummber')
        if element:
            bank_number = element.text.strip()
            stkbank = bank_number.replace('-', '')
        element = driver.find_element(By.CLASS_NAME, 'msb-main-user-name')
        if element:
            chutaikhoan = element.text.split()
        driver.close()
        driver.quit()
    except Exception as e:
        print(f"Loi login: {str(e)}")

@app.errorhandler(404)
def page_not_found(e):
    return "404", 404

@app.route('/api')
def api_index():
    return "hihi"

@app.route('/check')
def check_moi():
    key = request.args.get('key')
    sotin = request.args.get('t')
    stk_nhan = request.args.get('stk', STK_MSB)
    if key != "kami" or sotin == None:
        return jsonify({'error': 'Thieu tham so: key, t'}), 401
    if bodanglogin == True:
        return jsonify({'error': 'Dang login lai', 'msg': 'Cho login lai'}), 503
    dulieugd = checkGd(cookie, token)
    if dulieugd == None:
        return jsonify({'error': 'Dang login lai', 'msg': 'Cho login lai'}), 503
    status_code = 0
    sotientrve = 0
    msgz = "Chua co giao dich"
    gd_id = None
    for item in dulieugd.get("data", {}).get("history", []):
        amount = item.get("amount", 0)
        remark = str(item.get("remark", ""))
        if int(sotin) <= int(amount):
            status_code = 2
            sotientrve = int(sotin)
            msgz = "Thanh toan thanh cong"
            gd_id = remark.split('-')[1] if '-' in remark else None
            break
        else:
            status_code = 3
            sotientrve = int(amount)
            msgz = "Chuyen thieu tien"
            gd_id = remark.split('-')[1] if '-' in remark else None
            break
    response = jsonify({
        'status': status_code,
        'so_tien': sotientrve,
        'stk_nhan': stk_nhan,
        'gd_id': gd_id,
        'msg': msgz
    })
    response.status_code = 200
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

if __name__ == "__main__":
    if loog == False:
        login()
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Xin chao {chutaikhoan}\nSTK: {stkbank}\nToken: {token}")
        loog = True
    app.run(debug=False, port=4000, host='0.0.0.0')