import sys
import os
import subprocess
import hashlib
import requests
import base64
import threading
import psutil
import time
from PIL import Image
import google.generativeai as genai
CONFIG_FILE = "activation_config.txt"
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLineEdit, QLabel, QScrollArea, 
                             QGridLayout, QFrame,QInputDialog, QMessageBox,QDialog, QPushButton, QTextEdit, QFileDialog, QTextBrowser) # <--- ဒီအဆုံးက QPushButton ပါဖို့လိုပါတယ်

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont



# =====================================================================
# 🔑 အစ်ကို့ရဲ့ Gemini API Key ၄ ခုကို ဒီအောက်က မျက်တောင်အဖွင့်အပိတ်ထဲမှာ ထည့်ပေးပါ
GEMINI_KEYS = [
    "AQ.Ab8RN6LFWn53XOQV7SubZYxrbr4hkzpOYRBSZMYTF4Nt44u9xQ", # Board IC 1
    "AQ.Ab8RN6KuTZBJD7mcC_flVBcvo27cqG9El9g4qHLDrTlD9n5UDQ", # Board IC 1 Sec
    "AQ.Ab8RN6IqbizYfZxi0vqRKUs4iJ4SsiQoZA-UAp7os7f7DtF1pQ", # Board IC 2
    "AQ.Ab8RN6LbqJYHvjoOOSh7S5soQ8RMhLnjsFeupoMo5S2Rerr_zQ"  # Board IC 2 Sec
]
KEY_INDEX = 0  # အလှည့်ကျ သုံးဖို့အတွက် Counter (ပြင်စရာမလိုပါ)



# --- လျှို့ဝှက်ချက်များကို နံရံမှာကပ်ပြီး သတ်မှတ်ခြင်း ---
T_PART1 = "ODU5ODU5NDQ2MDpBQUVubENC"
T_PART2 = "c2xoc25XYzRZZ3d2ejRKeDZSSXREZzV4RGR4VQ=="
C_PART1 = "NTc3OTM2"
C_PART2 = "NzI1NA=="

def get_secret(p1, p2):
    try:
        full_data = p1 + p2
        return base64.b64decode(full_data).decode("utf-8")
    except:
        return ""

REAL_TOKEN = get_secret(T_PART1, T_PART2)
REAL_CHATID = get_secret(C_PART1, C_PART2)

# --- Activation System Class ---
class KKZActivation:
    @staticmethod
    def get_hwid():
        try:
            # PowerShell UUID ဆွဲထုတ်နည်း
            ps_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            cmd = f'{ps_path} "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            uuid = subprocess.check_output(cmd, shell=True, text=True).strip()
            return uuid
        except Exception:
            try:
                reg_cmd = r'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography" /v MachineGuid'
                out = subprocess.check_output(reg_cmd, shell=True, text=True)
                return out.split()[-1] 
            except Exception:
                return "Unknown_HWID"

    @staticmethod
    def check_activation(user_hwid, input_key):
        salt = "KKZ_SECRET_2026"
        correct_key = hashlib.sha256((user_hwid + salt).encode()).hexdigest().upper()[:16]
        return input_key.strip() == correct_key



def check_illegal_tools():
    # Cracker တွေ သုံးလေ့ရှိတဲ့ Software စာရင်း
    illegal_tools = [
        "x64dbg.exe", "x32dbg.exe", "wireshark.exe", 
        "processhacker.exe", "cheatengine-x86_64.exe", 
        "ollydbg.exe", "dnspy.exe", "de4dot.exe",
        "pyinstxtractor.exe", "pycdc.exe", "uncompyle6.exe", "decompyle3.exe"
    ]
    
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() in illegal_tools:
                # မိသွားရင် Noti ပြပြီး ပိတ်လိုက်မယ်
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "Security Alert", f"Unauthorized tool detected: {proc.info['name']}\nPlease close it and restart.")
                
                # အစ်ကို့ဆီ Noti လှမ်းပို့ချင်ရင် ဒီမှာ bot function ခေါ်လို့ရပါတယ်
                # send_to_telegram(hwid, f"🚨 Crack Tool Detected: {proc.info['name']}")
                
                os._exit(0) # Tool ကို အတင်းအကျပ် ပိတ်ပစ်ခြင်း
    except:
        pass


def check_remote_ban(user_hwid):
    try:
        # Link မှန်မမှန် ပြန်စစ်ပေးပါ (Raw link ဖြစ်ရပါမယ်)
        github_url = "https://raw.githubusercontent.com/kaungkhant9231/my-tool-security/refs/heads/main/banned_hwids.txt"
        
        raw_url = "https://raw.githubusercontent.com/kaungkhant9231/my-tool-security/main/banned_hwids.txt"
        cache_killer_url = f"{raw_url}?v={int(time.time())}"  


       # Cache ကို ကျော်ဖို့အတွက် Link အနောက်မှာ random parameter လေး ထည့်လိုက်ပါမယ်
        
        response = requests.get(f"{github_url}?v={time.time()}", timeout=5)
        
        if response.status_code == 200:
            # GitHub ထဲက စာရင်းကို အကုန်လုံး စာလုံးအသေးပြောင်းပြီး List လုပ်မယ်
            banned_list = [line.strip().lower() for line in response.text.splitlines() if line.strip()]
            
            # စစ်မည့် HWID ကိုလည်း စာလုံးအသေးပြောင်းမယ်
            current_hwid = user_hwid.strip().lower()
            
            print(f"Checking HWID: {current_hwid}") # Debug လုပ်ဖို့ (EXE ထုတ်ရင် ပြန်ဖြုတ်ပါ)
            
            if current_hwid in banned_list:
                from PyQt6.QtWidgets import QMessageBox
                import sys
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Security Access Denied")
                msg.setText("သင့်စက်ကို အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။")
                msg.setInformativeText(f"HWID: {user_hwid}\nကျေးဇူးပြု၍ Admin ကို ဆက်သွယ်ပါ။ Telegram - @kaungkhant9231 ")
                msg.exec()
                sys.exit()
    except Exception as e:
        print(f"Error: {e}") # ဘာမှားနေလဲ သိရအောင်
        pass



# --- Telegram ဆီ စာပို့မည့် Function ---
def send_to_telegram(hwid, license_key):
    def background_log():
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report = (
                "🚀 **Tool Activated!**\n\n"
                f"👤 **HWID:** `{hwid}`\n"
                f"🔑 **Key:** `{license_key}`\n"
                f"⏰ **Time:** {current_time}\n"
                "------------------------"
            )
            url = f"https://api.telegram.org/bot{REAL_TOKEN}/sendMessage"
            payload = {"chat_id": REAL_CHATID, "text": report, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=5)
        except:
            pass

    threading.Thread(target=background_log, daemon=True).start()



def send_startup_alert(hwid):
    def background_task():
        try:
            import os
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pc_name = os.environ.get('COMPUTERNAME', 'Unknown PC')
            
            report = (
                "⚠️ **Tool Startup Alert!**\n"
                f"👤 **PC Name:** `{pc_name}`\n"
                f"🆔 **HWID:** `{hwid}`\n"
                f"⏰ **Time:** {current_time}\n"
                "------------------------"
            )
            url = f"https://api.telegram.org/bot{REAL_TOKEN}/sendMessage"
            payload = {"chat_id": REAL_CHATID, "text": report, "parse_mode": "Markdown"}
            requests.post(url, data=payload, timeout=5)
        except:
            pass
    
    # Tool အလုပ်လုပ်တာ နှေးမသွားအောင် နောက်ကွယ်ကနေ ပို့ခိုင်းတာပါ
    threading.Thread(target=background_task, daemon=True).start()

# --- ဒီနေရာကနေစပြီး ICCard Class ကို ဆက်ရေးပါ ---






    @staticmethod
    def get_hwid():
        import subprocess
        try:
            # PowerShell လမ်းကြောင်းကို တိုက်ရိုက်ညွှန်းပြီး UUID ဆွဲထုတ်နည်း
            ps_path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            cmd = f'{ps_path} "(Get-CimInstance Win32_ComputerSystemProduct).UUID"'
            
            uuid = subprocess.check_output(cmd, shell=True, text=True).strip()
            return uuid
        except Exception:
            try:
                # PowerShell မရရင် Registry ထဲက Machine ID ကို ယူမယ်
                reg_cmd = r'reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography" /v MachineGuid'
                out = subprocess.check_output(reg_cmd, shell=True, text=True)
                return out.split()[-1] 
            except Exception:
                return "Unknown_HWID"



    @staticmethod
    def check_activation(user_hwid, input_key):
        import hashlib
        salt = "KKZ_SECRET_2026"  # အစ်ကို့ Generator နဲ့ တူရမယ့် Salt
        correct_key = hashlib.sha256((user_hwid + salt).encode()).hexdigest().upper()[:16]
        return input_key.strip() == correct_key
# -----------------------------------------------




class ICCard(QFrame):
    def __init__(self, ic_name, group_name, index):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
            }
            QFrame:hover { 
                border: 1px solid #3b82f6; 
                background-color: #f8fafc;
            }
        """)
        layout = QVBoxLayout(self)
        
        idx_label = QLabel(f"NO. {index}")
        idx_label.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold;")
        
        name_label = QLabel(ic_name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #0f172a;")
        name_label.setWordWrap(True)
        
        group_badge = QLabel(group_name)
        group_badge.setStyleSheet("""
            background-color: #dbeafe;
            color: #1e40af;
            font-size: 10px;
            font-weight: bold;
            padding: 4px;
            border-radius: 4px;
        """)
        group_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(idx_label)
        layout.addWidget(name_label)
        layout.addSpacing(8)
        layout.addWidget(group_badge)

# --- 🤖 Gemini AI Form အသစ် ---
class KKZAIForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KKZ Check With AI Assistant")
        self.resize(450, 600)
        self.setStyleSheet("QDialog { background-color: #f8fafc; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        ai_title = QLabel("🤖 KKZ AI IC Assistant")
        ai_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        ai_title.setStyleSheet("color: #1e3a8a;")
        layout.addWidget(ai_title)
        
        # Chat History Area
        self.ai_chat_area = QTextEdit()
        self.ai_chat_area.setReadOnly(True)
        self.ai_chat_area.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px; padding: 8px;")
        layout.addWidget(self.ai_chat_area)
        
        # Image Preview Label
        self.img_preview = QLabel("ပုံတင်ထားခြင်းမရှိပါ")
        self.img_preview.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.img_preview)
        self.selected_image_path = None
        
        # AI Input Box
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("IC code သို့မဟုတ် ပြဿနာများကို ရိုက်မေးပါ...")
        self.ai_input.setStyleSheet("padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; background-color: white;")
        self.ai_input.returnPressed.connect(self.ask_gemini)
        layout.addWidget(self.ai_input)
        
        # Buttons Layout
        btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("📷 Upload Image")
        self.upload_btn.setStyleSheet("background-color: #64748b; color: white; padding: 8px; font-weight: bold; border-radius: 6px;")
        self.upload_btn.clicked.connect(self.select_image)
        
        self.ask_btn = QPushButton("🚀 Ask AI")
        self.ask_btn.setStyleSheet("background-color: #2563eb; color: white; padding: 8px; font-weight: bold; border-radius: 6px;")
        self.ask_btn.clicked.connect(self.ask_gemini)
        
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.ask_btn)
        layout.addLayout(btn_layout)

    def select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open IC Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.selected_image_path = file_path
            from PyQt6.QtGui import QPixmap
            pixmap = QPixmap(file_path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.img_preview.setPixmap(pixmap)

    def show_ai_coming_soon(self):
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("KKZ AI Assistant")
        msg.setText("✨ AI Assistant Feature is Coming Soon!")
        msg.setInformativeText("နည်းပညာပိုင်းဆိုင်ရာ မြှင့်တင်မှုများ ပြုလုပ်နေဆဲဖြစ်ပါသဖြင့် နောက် Update ဗားရှင်းတွင် စုံလင်စွာ ထည့်သွင်းပေးသွားပါမည်ဗျာ။")
        msg.setStyleSheet("""
            QMessageBox { background-color: #f8fafc; }
            QLabel { font-size: 13px; color: #1e293b; font-family: 'Segoe UI', Pyidaungsu; }
            QPushButton { background-color: #8b5cf6; color: white; font-weight: bold; border-radius: 5px; padding: 5px 15px; }
        """)
        msg.exec()
        threading.Thread(target=ai_thread, daemon=True).start()
            
    # ⚠️ Class အဖွင့်စာကြောင်း ရှိနေဖို့ အရမ်းအရေးကြီးပါတယ်ဗျာ
class KKZMobileTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KK Board-Number Check List - IC FINDER PRO  V2.0 ")
        self.resize(1000, 800)
        self.setStyleSheet("QMainWindow { background-color: #f1f5f9; }")
        
        # 🔗 GitHub Cloud URL (Direct Raw Link ပုံစံအမှန်သို့ ပြောင်းလဲထားပါသည်)
        self.JSON_RAW_URL = "https://raw.githubusercontent.com/kaungkhant9231/my-tool-security/main/ic_data.json"
        
        # 🌐 Web ပေါ်ကနေ ဒေတာကို RAM ပေါ် တိုက်ရိုက်ဆွဲတင်ပြီး self.all_data ထဲ တန်းသိမ်းမည်
        self.all_data = self.fetch_ic_data_from_web()
        
        # 🏛️ မူရင်း UI ဆောက်တဲ့ လိုင်း
        self.init_ui()

    def fetch_ic_data_from_web(self):
        """ Local မှာ ဖိုင်လုံးဝမဆောက်ဘဲ GitHub Web ပေါ်ကနေ JSON ကို တိုက်ရိုက်ဖတ်မည့် Function """
        print("🌐 Fetching IC Database directly from GitHub Web...")
        try:
            import requests
            import json
            
            response = requests.get(self.JSON_RAW_URL, timeout=10)
            if response.status_code == 200:
                # 💡 ဒေတာရလာပြီးမှ JSON စစ်စစ် ဟုတ်မဟုတ် သပ်သပ် ထပ်စစ်မယ်ဗျာ
                try:
                    ic_list = json.loads(response.text)
                    print("✅ IC Database Loaded Successfully from Web!")
                    return ic_list
                except json.JSONDecodeError as json_err:
                    print(f"❌ JSON Decode Error (ရလာတဲ့စာသားက JSON မဟုတ်ပါ) - {json_err}")
                    print("⚠️ Response Content Preview:", response.text[:100]) # အစပိုင်း ဘာစာသားတွေ ပါလဲ ကြည့်ရန်
                    return []
            else:
                print(f"⚠️ Server Response Error: Status {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Connection Error (အင်တာနက် သို့မဟုတ် VPN မရှိပါ) - {e}")
            return []
      







    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setup_kkz_header(main_layout) # ဒါလေး တစ်ကြောင်းပဲ ထည့်ရမှာပါ
        
        # Header Section
        header = QLabel("Tool can make mistakes.")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("IC Name သို့မဟုတ် Group Name ဖြင့် ရှာဖွေပါ...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                font-size: 16px;
                border: 2px solid #cbd5e1;
                border-radius: 12px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #3b82f6; }
        """)
        self.search_bar.textChanged.connect(self.update_results)
        main_layout.addWidget(self.search_bar)

        # Scroll Area for Grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(15)
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

        self.update_results()

    def update_results(self):
        # Clear previous cards
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        search_text = self.search_bar.text().lower().strip()
        
        filtered_data = [
            item for item in self.all_data 
            if search_text in item['ic'].lower() or search_text in item['group'].lower()
        ]

        # Display filtered results
        for idx, item in enumerate(filtered_data):
            card = ICCard(item['ic'], item['group'], idx + 1)
            # 3 cards per row
            self.grid.addWidget(card, idx // 3, idx % 3)

    def open_ai_form(self):
        self.hide() # မူရင်း Form ကို ခေတ္တဖျောက်မယ်
        self.ai_window = KKZAIForm(self)
        self.ai_window.exec() # AI Dialog Form ကို ဖွင့်မယ်
        self.show() # AI Form ပိတ်သွားရင် မူရင်း Form ကို ပြန်ပြပေးမယ်


    def setup_kkz_header(self, layout):
        import webbrowser
          # Header Layout အသစ်လုပ်ခြင်း
        header_layout = QHBoxLayout()
    
          # ဘယ်ဘက်: Title + Dev Name
        title_vbox = QVBoxLayout()
        header_text = QLabel("KK Board Number Check lists")
        header_text.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b;")
        dev_text = QLabel("Developed by Kaung Khant")
        dev_text.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
        title_vbox.addWidget(header_text)
        title_vbox.addWidget(dev_text)
        header_layout.addLayout(title_vbox)
    
        header_layout.addStretch()
 
        # ညာဘက်အခြမ်း: ခလုတ် ၃ ခုလုံးကို ဒေါင်လိုက်အောက်ဆင်းစီရန် layout တစ်ခု ထပ်ဆောက်ခြင်း
        btn_vbox = QVBoxLayout()
        btn_vbox.setSpacing(6) # ခလုတ်တစ်ခုနဲ့တစ်ခု ကြားအကွာအဝေး

        # 🔄 ၁။ Check Update Button
        update_btn = QPushButton("🔄 Check Update")
        update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        update_btn.setStyleSheet("background-color: #ea580c; color: white; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 11px;")
        update_btn.clicked.connect(self.check_for_updates)
        btn_vbox.addWidget(update_btn)

        # 🤖 ၂။ Ask with AI Button
        ai_btn = QPushButton("🤖 Ask with AI")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 11px;")
        
        # 💡 import မလိုဘဲ PyQt6 ရဲ့ QMessageBox ကို တိုက်ရိုက် ခေါ်သုံးပြီး ပေါ့ပ်အပ် ပြလိုက်တာပါ
        ai_btn.clicked.connect(lambda: globals().get('QMessageBox', None) and globals()['QMessageBox'].information(
            None, 
            "KKZ AI Assistant", 
            "✨ AI Assistant Feature is Coming Soon!\n\nနည်းပညာပိုင်းဆိုင်ရာ မြှင့်တင်မှုများ ပြုလုပ်နေဆဲဖြစ်ပါသဖြင့် နောက် Update ဗားရှင်းတွင် စုံလင်စွာ ထည့်သွင်းပေးသွားပါမည်ဗျာ။"
        ) or __import__('PyQt6.QtWidgets', fromlist=['QMessageBox']).QMessageBox.information(
            None, 
            "KKZ AI Assistant", 
            "✨ AI Assistant Feature is Coming Soon!\n\nနည်းပညာပိုင်းဆိုင်ရာ မြှင့်တင်မှုများ ပြုလုပ်နေဆဲဖြစ်ပါသဖြင့် နောက် Update ဗားရှင်းတွင် စုံလင်စွာ ထည့်သွင်းပေးသွားပါမည်ဗျာ။"
        ))
        
        btn_vbox.addWidget(ai_btn)

        # ✈️ ၃။ Telegram Button
        tg_btn = QPushButton(" Join Telegram Channel")
        tg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tg_btn.setStyleSheet("background-color: #0088cc; color: white; font-weight: bold; border-radius: 6px; padding: 6px 12px; font-size: 11px;")
        tg_btn.clicked.connect(lambda: webbrowser.open("https://t.me/kaungkhant9737"))
        btn_vbox.addWidget(tg_btn)




        # 📌 ==================== [NEW: GITHUB ANNOUNCEMENT NOTI BOX] ====================
        self.noti_box = QFrame()
        self.noti_box.setFixedWidth(175)  # ညာဘက်အခြမ်း ခလုတ်တွေနဲ့ အနံညီအောင် ညှိထားခြင်း
        self.noti_box.setFixedHeight(110)
        self.noti_box.setStyleSheet("""
            QFrame {
                background-color: #fffbeb; 
                border: 1px solid #fef3c7; 
                border-radius: 8px;
            }
        """)
        noti_layout = QVBoxLayout(self.noti_box)
        noti_layout.setContentsMargins(6, 4, 6, 4)
        
        noti_title = QLabel("📢 Announcement NOTI")
        noti_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        noti_title.setStyleSheet("color: #b45309; border: none;") # Frame ဘောင်စတိုင် မပတ်အောင် border:none ခံရပါတယ်
        noti_layout.addWidget(noti_title)
        
        # 📋 User က Copy ကူးနိုင်ရန်နှင့် Link နှိပ်နိုင်ရန် QTextBrowser ပြောင်းသုံးခြင်း
        self.noti_text = QTextBrowser()
        self.noti_text.setOpenExternalLinks(True)  # Link ပါလာရင် Browser မှာ တန်းပွင့်စေရန်
        self.noti_text.setFont(QFont("Segoe UI", 9))
        self.noti_text.setStyleSheet("""
            QTextBrowser {
                color: #78350f;
                background-color: transparent;
                border: none;
            }
        """)
        # စာသားမလာခင် ခေတ္တပြထားမည့်စာ
        self.noti_text.setText("Loading announcement...") 
        noti_layout.addWidget(self.noti_text)
        
        btn_vbox.addWidget(self.noti_box)

        # 🌐 GitHub Raw Link ကနေ စာသားလှမ်းဆွဲမည့် Thread Function
        def fetch_announcement():
            try:
                raw_url = "https://raw.githubusercontent.com/kaungkhant9231/my-tool-security/refs/heads/main/announcementnoti.txt"
                # Cache မငြိအောင် time parameter ထည့်ပြီး လှမ်းခေါ်ခြင်း
                response = requests.get(f"{raw_url}?v={int(time.time())}", timeout=5)
                if response.status_code == 200:
                    # ရလာတဲ့ စာသားထဲမှာ Link တွေပါရင် အလိုအလျောက် နှိပ်လို့ရအောင် Format ပြောင်းပေးခြင်း
                    text_content = response.text.strip()
                    
                    # UI Thread ဘက်ကို စာသားပြန်တင်ပေးခြင်း
                    from PyQt6.QtCore import QMetaObject, Q_ARG
                    QMetaObject.invokeMethod(self.noti_text, "setText", 
                                           Qt.ConnectionType.QueuedConnection, 
                                           Q_ARG(str, text_content))
                else:
                    self.noti_text.setText("Failed to load NOTI.")
            except:
                self.noti_text.setText("Connection error.")

        # Tool ကြီး တုံ့ခိုင်းမသွားအောင် နောက်ကွယ် Thread ကနေ လှမ်းဖတ်ခိုင်းခြင်း
        threading.Thread(target=fetch_announcement, daemon=True).start()
        # =========================================================================
    
        # ခလုတ် Layout တစ်ခုလုံးကို header_layout ထဲ ထည့်ပေးလိုက်ခြင်း
        header_layout.addLayout(btn_vbox)

        layout.addLayout(header_layout)
        layout.addSpacing(15)

    def check_for_updates(self):
        """ Update စစ်ဆေးပေးမယ့် Function """
        from PyQt6.QtWidgets import QMessageBox # အပေါ်မှာ import မလုပ်ရသေးရင် သုံးနိုင်အောင်လို့ပါ
        
        print("Checking for updates...") 
        
        # လောလောဆယ် Custom Pop-up Alert လေးပြပေးထားပါမယ်
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Update Checker")
        msg.setText("Your KK Board Tool is up to date!")
        msg.setInformativeText("Version: v2.0.0 (Latest)")
        msg.setStyleSheet("font-size: 13px;")
        msg.exec()

    def ask_with_ai(self):
        """ AI နဲ့ စကားပြော/မေးမြန်းနိုင်မယ့် Function """
        from PyQt6.QtWidgets import QMessageBox
        
        print("Opening AI Assistant...")
        
        # လောလောဆယ် ခလုတ်နှိပ်ရင် အလုပ်လုပ်ကြောင်း အသိပေးချက်ပြပေးထားပါမယ်
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("KKZ AI Assistant")
        msg.setText("AI Assistant Feature is coming soon!")
        msg.setInformativeText("ဒီနေရာမှာ Local Gemini (သို့) OpenAI APIs တွေနဲ့ ချိတ်ဆက်ဖို့ ပြင်ဆင်နေပါတယ်ဗျာ။")
        msg.setStyleSheet("font-size: 13px;")
        msg.exec()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    hwid = KKZActivation.get_hwid()


    # ၁။ Crack tool တွေ ဖွင့်ထားလား အရင်စစ်မယ်
    check_illegal_tools()
    
    # ၂။ HWID ယူမယ်၊ Ban စစ်မယ်၊ Activation ဆက်သွားမယ်
    hwid = KKZActivation.get_hwid()
    check_remote_ban(hwid)
    
    # --- Activation Dialog ဆောက်ခြင်း ---
    activation_dialog = QDialog()
    activation_dialog.setWindowTitle("KKZ Mobile Tool Activation")
    activation_dialog.setFixedWidth(450)
    layout = QVBoxLayout(activation_dialog)

    # HWID ပြတဲ့အပိုင်း
    layout.addWidget(QLabel("Your Hardware ID (HWID):"))
    hwid_edit = QLineEdit(hwid)
    hwid_edit.setReadOnly(True)
    hwid_edit.setStyleSheet("padding: 8px; background-color: #f1f5f9; font-weight: bold;")
    layout.addWidget(hwid_edit)

    layout.addSpacing(10)

    # License Key ထည့်တဲ့အပိုင်း
    layout.addWidget(QLabel("Enter License Key:"))
    key_input = QLineEdit()
    
    # --- သိမ်းထားတဲ့ Key ရှိရင် အလိုအလျောက် ပြန်ဖတ်ပေးမည့်အပိုင်း ---
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_key = f.read().strip()
                key_input.setText(saved_key)
        except:
            pass
            
    key_input.setPlaceholderText("Paste your license key here...")
    key_input.setStyleSheet("padding: 8px;")
    layout.addWidget(key_input)

    layout.addSpacing(15)

    # ခလုတ်များ
    btn_layout = QHBoxLayout()
    activate_btn = QPushButton("Activate Tool")
    activate_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px;")
    
    exit_btn = QPushButton("Exit")
    exit_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 10px;")
    
    btn_layout.addWidget(activate_btn)
    btn_layout.addWidget(exit_btn)
    layout.addLayout(btn_layout)

    # ခလုတ်နှိပ်ရင် အလုပ်လုပ်မည့် logic
    def on_activate():
        entered_key = key_input.text().strip()
        if KKZActivation.check_activation(hwid, entered_key):
            # အောင်မြင်ရင် Key ကို ဖိုင်ထဲ သိမ်းထားလိုက်မယ်
            try:
                with open(CONFIG_FILE, "w") as f:
                    f.write(entered_key)
            except:
                pass
                
            send_to_telegram(hwid, entered_key)
            activation_dialog.accept()
        else:
            QMessageBox.critical(activation_dialog, "Error", "Invalid License Key!")

    activate_btn.clicked.connect(on_activate)
    exit_btn.clicked.connect(activation_dialog.reject)

    # ပွင့်လာမည့်ပုံစံ
    if activation_dialog.exec() == QDialog.DialogCode.Accepted:
        window = KKZMobileTool()
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()
