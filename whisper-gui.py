import os
import sys
import threading
import time
import subprocess
import re
import shutil
import urllib.request
import ctypes
import gc

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import warnings

warnings.filterwarnings("ignore")

BASE_DIR = os.getcwd()
GITHUB_FFMPEG_URL = "https://raw.githubusercontent.com/acrilot/whisper-gui/refs/heads/main/install_ffmpeg.bat"

PATHS = {
    "faster_large": os.path.join(BASE_DIR, "faster_whisper_large_v3"),
    "faster_turbo": os.path.join(BASE_DIR, "faster_whisper_turbo"),
    "std_large":    os.path.join(BASE_DIR, "large-v3.pt"),
    "std_turbo":    os.path.join(BASE_DIR, "large-v3-turbo.pt"),
    "std_medium":   os.path.join(BASE_DIR, "medium.pt")
}

RAW_MODEL_OPTIONS = {
    "Faster Whisper - Large V3 (En İyi Kalite)": "faster_large",
    "Faster Whisper - Turbo (En Hızlı)": "faster_turbo",
    "Standart Whisper - Large V3": "std_large",
    "Standart Whisper - Turbo": "std_turbo",
    "Standart Whisper - Medium": "std_medium"
}

LANGUAGE_OPTIONS = {
    "Otomatik Algıla": None,
    "Türkçe": "tr",
    "İngilizce": "en",
    "Almanca": "de",
    "Fransızca": "fr",
    "İspanyolca": "es",
    "Çince": "zh",
    "Japonca": "ja"
}

FORMAT_OPTIONS = ["TXT", "PDF", "DOCX", "XML (Altyazı)"]
COMPUTE_OPTIONS = ["int8", "float16", "int8_float16", "float32"]

class TqdmYakalayici:
    def __init__(self, callback_func):
        self.callback = callback_func
        self.orijinal_stderr = sys.stderr
        self.buffer = ""

    def write(self, output):
        self.buffer += output
        match = re.search(r"(\d+)/(\d+)", self.buffer)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            if total > 0:
                yuzde = (current / total) * 100
                self.callback(yuzde)
            self.buffer = self.buffer[-20:]

    def flush(self):
        self.orijinal_stderr.flush()


class WhisperApp:
    def __init__(self, root):
        self.root = root
        self.ffmpeg_kontrol_et_ve_kur()

        self.root.title("Whisper Transkript Çıkarıcı")
        self.root.geometry("1100x900")
        self.root.state('zoomed')
        self.root.minsize(900, 700)
        self.root.configure(bg="#f0f0f0")
        self.root.protocol("WM_DELETE_WINDOW", self.uygulamayi_kapat)

        # Variables
        self.secilen_dosyalar = []
        self.secilen_dosya_gosterim = tk.StringVar()
        self.cikti_konumu = tk.StringVar()
        self.secilen_format = tk.StringVar(value=FORMAT_OPTIONS[0])
        self.secilen_model_gorunum = tk.StringVar()
        self.secilen_dil_adi = tk.StringVar(value="Otomatik Algıla")
        self.secilen_compute = tk.StringVar(value="int8")
        self.beam_size_val = tk.IntVar(value=5)

        self.kurulum_modu = tk.BooleanVar(value=False)
        self.tek_blok_modu = tk.BooleanVar(value=True)
        self.anti_loop_modu = tk.BooleanVar(value=True)
        self.zaman_damgasi_var = tk.BooleanVar(value=False)
        self.ceviri_modu = tk.BooleanVar(value=False)
        self.islem_durumu = tk.StringVar(value="Hazır")

        self.iptal_istendi = False
        self.model_display_map = {}
        self.yuklu_model = None
        self.yuklu_model_key = None

        self._model_lock = threading.Lock()
        self._current_temp_path = ""

        self.setup_styles()
        self.arayuz_olustur()
        self.modelleri_tara_ve_guncelle()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        self.colors = {
            'primary': '#2196F3',
            'primary_dark': '#1976D2',
            'success': '#4CAF50',
            'danger': '#F44336',
            'warning': '#FF9800',
            'bg_light': '#FAFAFA',
            'bg_white': '#FFFFFF',
            'text_dark': '#212121',
            'text_light': '#757575',
            'border': '#E0E0E0'
        }

        style.configure("Primary.TButton", background=self.colors['primary'], foreground="white",
            borderwidth=0, focuscolor='none', padding=(20, 12), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[('active', self.colors['primary_dark'])])

        style.configure("Danger.TButton", background=self.colors['danger'], foreground="white",
            borderwidth=0, focuscolor='none', padding=(20, 12), font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton", background=[('active', '#D32F2F')])

        style.configure("Secondary.TButton", background=self.colors['bg_white'], foreground=self.colors['text_dark'],
            borderwidth=1, relief="solid", focuscolor='none', padding=(15, 8), font=("Segoe UI", 9))

        style.configure("Card.TFrame", background=self.colors['bg_white'], relief="flat")
        style.configure("TLabelframe", background=self.colors['bg_white'], borderwidth=0)
        style.configure("TLabelframe.Label", background=self.colors['bg_white'],
            foreground=self.colors['text_dark'], font=("Segoe UI", 10, "bold"))

        style.configure("TLabel", background=self.colors['bg_white'], foreground=self.colors['text_dark'], font=("Segoe UI", 9))
        style.configure("TCheckbutton", background=self.colors['bg_white'], foreground=self.colors['text_dark'], font=("Segoe UI", 9))
        style.configure("TCombobox", fieldbackground="white", background="white", borderwidth=1)

    def ffmpeg_kontrol_et_ve_kur(self):
        if shutil.which("ffmpeg"):
            return
        root = tk.Tk()
        root.withdraw()
        cevap = messagebox.askyesno("FFmpeg Eksik",
            "Sisteminizde FFmpeg bulunamadı. Ses işleme için bu araç gereklidir.\n\n"
            "GitHub deposundan otomatik kurulum scriptini indirip kurmak ister misiniz?")
        root.destroy()
        if not cevap:
            messagebox.showwarning("Uyarı", "FFmpeg olmadan uygulama düzgün çalışmayabilir.")
            return
        try:
            script_adi = "ffmpeg_installer_temp.bat"
            urllib.request.urlretrieve(GITHUB_FFMPEG_URL, script_adi)
            subprocess.check_call([script_adi], shell=True)
            if os.path.exists(script_adi):
                os.remove(script_adi)
            messagebox.showinfo("Yeniden Başlatılıyor",
                "FFmpeg kuruldu. Değişikliklerin etkili olması için uygulama yeniden başlatılıyor.")
            subprocess.Popen([sys.executable] + sys.argv)
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Kurulum Hatası", f"Otomatik kurulum başarısız oldu:\n{e}")

    def on_blok_change(self):
        if self.tek_blok_modu.get():
            self.zaman_damgasi_var.set(False)

    def on_time_change(self):
        if self.zaman_damgasi_var.get():
            self.tek_blok_modu.set(False)

    def arayuz_olustur(self):
        self.create_header(self.root)
        main_body = tk.Frame(self.root, bg="#f0f0f0")
        main_body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        left_panel = tk.Frame(main_body, bg="#f0f0f0", width=900)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)
        right_panel = tk.Frame(main_body, bg="#f0f0f0")
        right_panel.pack(side="left", fill="both", expand=True)
        left_content = tk.Frame(left_panel, bg="#f0f0f0")
        left_content.pack(fill="both", expand=True)
        
        self.create_file_section(left_content)
        self.create_settings_section(left_content)
        self.create_progress_section(left_content)
        self.create_control_section(left_content)
        self.create_doc_section(left_content)
        self.create_log_section(right_panel)

    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=80)
        header_frame.pack(side="top", fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        title_container = tk.Frame(header_frame, bg=self.colors['primary'])
        title_container.pack(expand=True, fill="both", padx=20)
        title_label = tk.Label(title_container, text="🎙️ Whisper Transkript Çevirici",
            font=("Segoe UI", 20, "bold"), bg=self.colors['primary'], fg="white")
        title_label.pack(side="left", pady=20)
        subtitle_label = tk.Label(title_container, text="Ses ve video dosyalarınızı metne dönüştürün",
            font=("Segoe UI", 11), bg=self.colors['primary'], fg="#E3F2FD")
        subtitle_label.pack(side="right", pady=25)

    def create_file_section(self, parent):
        file_frame = ttk.LabelFrame(parent, text="📁 Dosya ve Format Seçimi (Toplu Seçim Yapılabilir)", padding=15, style="Card.TFrame")
        file_frame.pack(fill="x", pady=(0, 10))

        input_container = tk.Frame(file_frame, bg=self.colors['bg_white'])
        input_container.pack(fill="x", pady=(0, 10))
        tk.Label(input_container, text="Kaynak Dosya(lar):", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 5))
        input_row = tk.Frame(input_container, bg=self.colors['bg_white'])
        input_row.pack(fill="x")

        entry_input = tk.Entry(input_row, textvariable=self.secilen_dosya_gosterim, state="readonly",
            font=("Segoe UI", 9), relief="solid", borderwidth=1)
        entry_input.pack(side="left", fill="x", expand=True, ipady=8)
        btn_browse = ttk.Button(input_row, text="Dosya Seç", command=self.dosya_sec, style="Secondary.TButton")
        btn_browse.pack(side="right", padx=(10, 0))

        output_container = tk.Frame(file_frame, bg=self.colors['bg_white'])
        output_container.pack(fill="x")
        out_opts_row = tk.Frame(output_container, bg=self.colors['bg_white'])
        out_opts_row.pack(fill="x")

        format_frame = tk.Frame(out_opts_row, bg=self.colors['bg_white'])
        format_frame.pack(side="left", padx=(0, 10))
        tk.Label(format_frame, text="Çıktı Formatı:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_format = ttk.Combobox(format_frame, textvariable=self.secilen_format,
            values=FORMAT_OPTIONS, state="readonly", width=15, font=("Segoe UI", 9))
        self.combo_format.pack(fill="x", ipady=5)
        self.combo_format.bind("<<ComboboxSelected>>", self.format_degisti)

        path_frame = tk.Frame(out_opts_row, bg=self.colors['bg_white'])
        path_frame.pack(side="left", fill="x", expand=True)
        tk.Label(path_frame, text="Çıktı Yolu (Tek dosya ise düzenlenebilir):", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 5))
        path_inner_row = tk.Frame(path_frame, bg=self.colors['bg_white'])
        path_inner_row.pack(fill="x")
        self.entry_output = tk.Entry(path_inner_row, textvariable=self.cikti_konumu,
            font=("Segoe UI", 9), relief="solid", borderwidth=1)
        self.entry_output.pack(side="left", fill="x", expand=True, ipady=8)
        self.btn_save = ttk.Button(path_inner_row, text="Değiştir",
            command=self.kayit_yeri_sec, style="Secondary.TButton")
        self.btn_save.pack(side="right", padx=(10, 0))

    def create_settings_section(self, parent):
        settings_frame = ttk.LabelFrame(parent, text="⚙️ Ayarlar", padding=15, style="Card.TFrame")
        settings_frame.pack(fill="x", pady=(0, 10))

        selection_frame = tk.Frame(settings_frame, bg=self.colors['bg_white'])
        selection_frame.pack(fill="x", pady=(0, 10))

        model_frame = tk.Frame(selection_frame, bg=self.colors['bg_white'])
        model_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(model_frame, text="Model:", font=("Segoe UI", 9, "bold"), bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_model = ttk.Combobox(model_frame, textvariable=self.secilen_model_gorunum,
            state="readonly", font=("Segoe UI", 9))
        self.combo_model.pack(fill="x", ipady=5)
        self.combo_model.bind("<<ComboboxSelected>>", self.on_model_change)

        lang_frame = tk.Frame(selection_frame, bg=self.colors['bg_white'])
        lang_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(lang_frame, text="Dil:", font=("Segoe UI", 9, "bold"), bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_lang = ttk.Combobox(lang_frame, textvariable=self.secilen_dil_adi,
            values=list(LANGUAGE_OPTIONS.keys()), state="readonly", font=("Segoe UI", 9))
        self.combo_lang.pack(fill="x", ipady=5)

        adv_frame = tk.Frame(selection_frame, bg=self.colors['bg_white'])
        adv_frame.pack(side="left", fill="x", expand=True)
        tk.Label(adv_frame, text="İşlem Tipi (Compute):", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_compute = ttk.Combobox(adv_frame, textvariable=self.secilen_compute,
            values=COMPUTE_OPTIONS, state="readonly", font=("Segoe UI", 9), width=10)
        self.combo_compute.pack(side="left", fill="x", ipady=5, padx=(0, 10))
        tk.Label(adv_frame, text="Beam:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(side="left", anchor="center")
        self.spin_beam = ttk.Spinbox(adv_frame, from_=1, to=10, textvariable=self.beam_size_val,
            width=3, font=("Segoe UI", 9))
        self.spin_beam.pack(side="left", fill="x", ipady=5, padx=(5, 0))

        options_frame = tk.Frame(settings_frame, bg=self.colors['bg_white'])
        options_frame.pack(fill="x")
        tk.Label(options_frame, text="Seçenekler:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 8))
        checks_container = tk.Frame(options_frame, bg=self.colors['bg_white'])
        checks_container.pack(fill="x")

        chk_vad = ttk.Checkbutton(checks_container, text="🔄 Anti-Loop (VAD)", variable=self.anti_loop_modu)
        chk_vad.pack(side="left", padx=(0, 20))
        chk_blok = ttk.Checkbutton(checks_container, text="📄 Tek Blok Metin",
            variable=self.tek_blok_modu, command=self.on_blok_change)
        chk_blok.pack(side="left", padx=(0, 20))
        chk_time = ttk.Checkbutton(checks_container, text="🕐 Zaman Damgası",
            variable=self.zaman_damgasi_var, command=self.on_time_change)
        chk_time.pack(side="left", padx=(0, 20))
        chk_ceviri = ttk.Checkbutton(checks_container, text="🌐 İngilizce'ye Çevir", variable=self.ceviri_modu)
        chk_ceviri.pack(side="left", padx=(0, 20))
        chk_setup = ttk.Checkbutton(checks_container, text="🔧 Kurulum Modu", variable=self.kurulum_modu)
        chk_setup.pack(side="left")

    def create_control_section(self, parent):
        self.control_frame = tk.Frame(parent, bg="#f0f0f0")
        self.control_frame.pack(fill="x", pady=(0, 10))
        self.btn_baslat = ttk.Button(self.control_frame, text="▶ BAŞLAT",
            command=self.islem_baslat, style="Primary.TButton")
        self.btn_baslat.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.btn_iptal = ttk.Button(self.control_frame, text="⏹ DURDUR & KAYDET",
            command=self.iptal_et, style="Danger.TButton", state="disabled")
        self.btn_iptal.pack(side="left", fill="x", expand=True)

    def create_progress_section(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="📊 İlerleme", padding=15, style="Card.TFrame")
        progress_frame.pack(fill="x", pady=(0, 10))
        self.lbl_durum = tk.Label(progress_frame, textvariable=self.islem_durumu,
            font=("Segoe UI", 10, "bold"), bg=self.colors['bg_white'], fg=self.colors['primary'])
        self.lbl_durum.pack(anchor="w", pady=(0, 8))
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal",
            mode="determinate", length=400)
        self.progress.pack(fill="x")

    def create_doc_section(self, parent):
        doc_frame = ttk.LabelFrame(parent, text="📖 Kullanım Kılavuzu", padding=15, style="Card.TFrame")
        doc_frame.pack(fill="both", expand=True, pady=(0, 0))
        
        doc_container = tk.Frame(doc_frame, bg=self.colors['bg_white'])
        doc_container.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(doc_container)
        scrollbar.pack(side="right", fill="y")
        
        self.txt_doc = tk.Text(doc_container, font=("Segoe UI", 9), bg="#FAFAFA",
            fg=self.colors['text_dark'], relief="flat", yscrollcommand=scrollbar.set,
            wrap="word", height=6, padx=10, pady=10)
        self.txt_doc.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.txt_doc.yview)
        
        kilavuz_metni = (
            "TEKNİK DÖKÜMAN VE KULLANIM\n\n"
            "1. DOSYA SEÇİMİ: İşlenecek ses/video dosyalarını seçin. Çoklu seçim yapmak mümkündür.\n"
            "2. ÇIKTI FORMATI: TXT, PDF, DOCX veya XML (altyazı) seçilebilir. XML için zaman damgası otomatik olarak aktif edilir.\n"
            "3. MODEL SEÇİMİ:\n"
            "   - Faster Whisper: Optimize edilmiş, VRAM dostu model. İşlem tipi (Compute) seçimi aktiftir.\n"
            "   - Standart Whisper: Orijinal model. Compute ayarı devre dışıdır ve işlem bloklayıcı olduğu için çalışma esnasında durdurulamaz.\n"
            "4. PARAMETRELER:\n"
            "   - Compute Parametreleri.\n"
            "       > int8: Doğruluğu pek çok iş için yeterlidir ve en hızlı seçenektir.\n"
            "       > float16: Doğruluğu int8'e göre daha iyidir ancak int8'den daha yavaştır.\n"
            "       > float32: En yüksek doğruluk, en yavaş hız.\n"
            "   - Beam: Daha yüksek değerler doğruluğu artırır ancak hızı düşürür. Varsayılan değeri olan 5 çoğu iş için idealdir.\n"
            "   - Anti-Loop (VAD): Sessiz kısımları filtreler, tekrarlayan halüsinasyon hatalarını önler.\n"
            "5. ÇEVİRİ: 'İngilizce'ye Çevir' seçeneği aktifleştirildiğinde, model doğrudan çeviri modunda (Translate) çalışır."
        )
        self.txt_doc.insert(tk.END, kilavuz_metni)
        self.txt_doc.config(state=tk.DISABLED)

    def create_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="📝 İşlem Kayıtları", padding=15, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True)
        log_container = tk.Frame(log_frame, bg=self.colors['bg_white'])
        log_container.pack(fill="both", expand=True)
        scrollbar = tk.Scrollbar(log_container)
        scrollbar.pack(side="right", fill="y")
        self.txt_log = tk.Text(log_container, font=("Consolas", 9), bg="#FAFAFA",
            fg=self.colors['text_dark'], relief="flat", yscrollcommand=scrollbar.set,
            wrap="word", height=15, padx=10, pady=10)
        self.txt_log.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.txt_log.yview)

    def on_model_change(self, event=None):
        self.guncelle_cikti_yolu()
        secilen_gorunum = self.secilen_model_gorunum.get()
        if not secilen_gorunum:
            return
            
        model_key = self.model_display_map.get(secilen_gorunum, "")
        
        if "std_" in model_key:
            self.combo_compute.config(state="disabled")
            self.btn_iptal.pack_forget()
            self.btn_baslat.pack_configure(padx=0)
        else:
            self.combo_compute.config(state="readonly")
            self.btn_baslat.pack_forget()
            self.btn_iptal.pack_forget()
            self.btn_baslat.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_iptal.pack(side="left", fill="x", expand=True)

    def log_yaz(self, mesaj):
        """Thread-safe log writer"""
        self.root.after(0, self._log_yaz_safe, mesaj)

    def _log_yaz_safe(self, mesaj):
        self.txt_log.insert(tk.END, mesaj + "\n")
        self.txt_log.see(tk.END)

    def modelleri_tara_ve_guncelle(self):
        self.model_display_map = {}
        yeni_liste = []
        varsayilan_secim = ""
        for friendly_name, model_key in RAW_MODEL_OPTIONS.items():
            path = PATHS[model_key]
            durum_ikonu = "✓" if os.path.exists(path) else "⬇"
            display_text = f"{durum_ikonu} {friendly_name}"
            self.model_display_map[display_text] = model_key
            yeni_liste.append(display_text)
            if "Faster Whisper - Large" in friendly_name and os.path.exists(path):
                varsayilan_secim = display_text
        self.combo_model['values'] = yeni_liste
        if varsayilan_secim and varsayilan_secim in yeni_liste:
            self.combo_model.set(varsayilan_secim)
        elif yeni_liste:
            self.combo_model.current(0)
            
        self.on_model_change()

    def dosya_sec(self):
        dosyalar = filedialog.askopenfilenames(
            title="Ses veya Video Dosyası Seçin",
            filetypes=[("Medya Dosyaları", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.flac *.ogg *.webm *.opus"), ("Tümü", "*.*")]
        )
        if dosyalar:
            self.secilen_dosyalar = list(dosyalar)
            if len(self.secilen_dosyalar) == 1:
                self.secilen_dosya_gosterim.set(self.secilen_dosyalar[0])
                self.entry_output.config(state="normal")
                self.btn_save.config(state="normal")
                self.guncelle_cikti_yolu(self.secilen_dosyalar[0])
            else:
                self.secilen_dosya_gosterim.set(f"{len(self.secilen_dosyalar)} adet dosya seçildi (Toplu İşlem)")
                klasor = os.path.dirname(self.secilen_dosyalar[0])
                self.cikti_konumu.set(klasor + " (Toplu işlem dizini)")
                self.entry_output.config(state="disabled")
                self.btn_save.config(state="disabled")

    def format_degisti(self, event=None):
        if len(self.secilen_dosyalar) == 1:
            self.guncelle_cikti_yolu(self.secilen_dosyalar[0])

    def out_ismi_uret(self, input_dosya):
        klasor, isim = os.path.split(input_dosya)
        isim_kok = os.path.splitext(isim)[0]
        secilen_gorunum = self.secilen_model_gorunum.get()
        model_kodu = "whisper"
        if secilen_gorunum and self.model_display_map:
            ham_kod = self.model_display_map.get(secilen_gorunum, "")
            model_kodu = ham_kod.replace("_", "-")
        format_str = self.secilen_format.get()
        ext = ".txt"
        if "PDF" in format_str: ext = ".pdf"
        elif "DOCX" in format_str: ext = ".docx"
        elif "XML" in format_str: ext = ".xml"

        ceviri_ek = "_ceviri" if self.ceviri_modu.get() else ""
        yeni_isim = f"{isim_kok}_{model_kodu}{ceviri_ek}_transkript{ext}"
        return os.path.join(klasor, yeni_isim)

    def guncelle_cikti_yolu(self, input_dosya=None):
        if not input_dosya:
            if len(self.secilen_dosyalar) == 1:
                input_dosya = self.secilen_dosyalar[0]
            else:
                return
        self.cikti_konumu.set(self.out_ismi_uret(input_dosya))

    def kayit_yeri_sec(self):
        if len(self.secilen_dosyalar) > 1:
            messagebox.showinfo("Bilgi", "Toplu işlem modunda çıktı klasörü kaynak dosyaların bulunduğu klasördür.")
            return
        format_str = self.secilen_format.get()
        ext = ".txt"
        ftypes = [("Metin Dosyası", "*.txt")]
        if "PDF" in format_str:
            ext = ".pdf"
            ftypes = [("PDF Dosyası", "*.pdf")]
        elif "DOCX" in format_str:
            ext = ".docx"
            ftypes = [("Word Dosyası", "*.docx")]
        elif "XML" in format_str:
            ext = ".xml"
            ftypes = [("XML Altyazı", "*.xml")]

        dosya = filedialog.asksaveasfilename(title="Çıktı Dosyasını Kaydet",
            defaultextension=ext, filetypes=ftypes)
        if dosya:
            self.cikti_konumu.set(dosya)

    def progress_guncelle(self, yuzde):
        """Thread-safe progress update"""
        self.root.after(0, self._set_progress, yuzde)

    def _set_progress(self, yuzde):
        self.progress['value'] = yuzde
        self.islem_durumu.set(f"İşleniyor... %{yuzde:.1f}")

    def iptal_et(self):
        if messagebox.askyesno("Durdur", "İşlem durdurulsun ve kaydedilsin mi?"):
            self.iptal_istendi = True
            self.btn_iptal.config(state="disabled")

    def uygulamayi_kapat(self):
        if hasattr(self, 'btn_iptal') and str(self.btn_iptal['state']) == 'normal':
            cevap = messagebox.askyesno("Çıkış",
                "Şu anda devam eden bir transkript işlemi var.\nUygulamadan çıkmak istediğinize emin misiniz?")
            if not cevap:
                return
            self.iptal_istendi = True

        self.root.update()

        if hasattr(self, '_current_temp_path') and self._current_temp_path and os.path.exists(self._current_temp_path):
            try:
                os.remove(self._current_temp_path)
            except OSError:
                pass

        with self._model_lock:
            if hasattr(self, 'yuklu_model') and self.yuklu_model is not None:
                del self.yuklu_model
                self.yuklu_model = None
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
        self.root.destroy()
        os._exit(0)

    def islem_baslat(self):
        if not self.secilen_dosyalar:
            messagebox.showwarning("Uyarı", "Lütfen en az bir dosya seçin.")
            return
        
        params = {
            "kurulum_modu": self.kurulum_modu.get(),
            "secilen_model_gorunum": self.secilen_model_gorunum.get(),
            "secilen_dil_adi": self.secilen_dil_adi.get(),
            "secilen_compute": self.secilen_compute.get(),
            "beam_size_val": self.beam_size_val.get(),
            "anti_loop_modu": self.anti_loop_modu.get(),
            "zaman_damgasi_var": self.zaman_damgasi_var.get(),
            "tek_blok_modu": self.tek_blok_modu.get(),
            "ceviri_modu": self.ceviri_modu.get(),
            "secilen_format": self.secilen_format.get(),
            "secilen_dosyalar": self.secilen_dosyalar.copy(),
            "cikti_konumu": self.cikti_konumu.get()
        }

        self.btn_baslat.config(state="disabled")
        self.btn_iptal.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.iptal_istendi = False
        t = threading.Thread(target=self.worker_thread, args=(params,), daemon=True)
        t.start()

    def _format_timestamp(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"[{h:02}:{m:02}:{s:02}]"

    def xml_olustur(self, input_text):
        xml_output = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="tr">',
            '  <body>',
            '    <div>'
        ]
        lines = input_text.strip().split('\n')
        parsed_lines = []

        pattern = re.compile(r'\[(\d{2}):(\d{2}):(\d{2})\]\s*(.*)')

        for line in lines:
            match = pattern.match(line.strip())
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                text = match.group(4)
                total_seconds = (hours * 3600) + (minutes * 60) + seconds
                parsed_lines.append({'time': total_seconds, 'text': text})

        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"

        for i, current_line in enumerate(parsed_lines):
            start_sec = current_line['time']
            end_sec = parsed_lines[i + 1]['time'] if i < len(parsed_lines) - 1 else start_sec + 3.0
            safe_text = current_line['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_output.append(f'      <p begin="{format_time(start_sec)}" end="{format_time(end_sec)}">{safe_text}</p>')

        xml_output.extend(['    </div>', '  </body>', '</tt>'])
        return "\n".join(xml_output)

    def dosya_donustur(self, txt_yolu, hedef_yolu, format_tipi):
        try:
            def kutuphane_yukle_ve_al(paket_adi, import_adi):
                try:
                    __import__(import_adi)
                    return True
                except ImportError:
                    self.log_yaz(f">>> Uyarı: '{paket_adi}' eksik, otomatik yükleniyor...")
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.run([sys.executable, "-m", "pip", "install", paket_adi],
                            check=True, capture_output=True, startupinfo=startupinfo)
                        __import__(import_adi)
                        self.log_yaz(f"   -> '{paket_adi}' başarıyla kuruldu.")
                        return True
                    except subprocess.CalledProcessError:
                        self.log_yaz(f"!!! KRİTİK: '{paket_adi}' yüklenemedi.")
                        return False

            if "DOCX" in format_tipi and not kutuphane_yukle_ve_al("python-docx", "docx"):
                raise Exception("Gerekli kütüphane (python-docx) kurulamadı.")
            elif "PDF" in format_tipi and not kutuphane_yukle_ve_al("fpdf", "fpdf"):
                raise Exception("Gerekli kütüphane (fpdf) kurulamadı.")

            with open(txt_yolu, 'r', encoding='utf-8') as f:
                icerik = f.read()

            if "DOCX" in format_tipi:
                self.log_yaz(">>> Word (DOCX) oluşturuluyor...")
                from docx import Document
                doc = Document()
                doc.add_heading('Transkript', 0)
                for satir in icerik.split('\n'):
                    temiz_satir = satir.strip()
                    if temiz_satir:
                        doc.add_paragraph(temiz_satir)
                doc.save(hedef_yolu)

            elif "PDF" in format_tipi:
                self.log_yaz(">>> PDF oluşturuluyor...")
                from fpdf import FPDF
                
                font_paths = [
                    r"C:\Windows\Fonts\arial.ttf",
                    r"/Library/Fonts/Arial.ttf",
                    r"/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
                    r"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                ]
                mevcut_font = None
                for fp in font_paths:
                    if os.path.exists(fp):
                        mevcut_font = fp
                        break

                class PDF(FPDF):
                    def header(self):
                        if mevcut_font:
                            try:
                                self.add_font('CustomFont', '', mevcut_font, uni=True)
                                self.set_font('CustomFont', '', 10)
                            except:
                                self.set_font('Arial', '', 10)
                        else:
                            self.set_font('Arial', '', 10)
                        self.cell(0, 10, 'Transkript', 0, 1, 'C')

                pdf = PDF()
                pdf.add_page()
                
                if mevcut_font:
                    try:
                        pdf.add_font('CustomFont', '', mevcut_font, uni=True)
                        pdf.set_font("CustomFont", size=11)
                    except Exception as e:
                        self.log_yaz(f"! Uyarı: Font ayarlanamadı ({e}), standart font kullanılıyor.")
                        pdf.set_font("Arial", size=11)
                        icerik = icerik.encode('latin-1', 'replace').decode('latin-1')
                else:
                    self.log_yaz("! Uyarı: UTF-8 destekli font bulunamadı, standart font kullanılıyor (Türkçe karakterler bozulabilir).")
                    pdf.set_font("Arial", size=11)
                    icerik = icerik.encode('latin-1', 'replace').decode('latin-1')

                pdf.multi_cell(0, 8, icerik)
                pdf.output(hedef_yolu)

            elif "XML" in format_tipi:
                self.log_yaz(">>> XML (Subtitle) oluşturuluyor...")
                xml_icerik = self.xml_olustur(icerik)
                with open(hedef_yolu, "w", encoding="utf-8") as f_xml:
                    f_xml.write(xml_icerik)

            self.log_yaz(f"✓ Dönüştürme Başarılı: {os.path.basename(hedef_yolu)}")
            return True

        except Exception as e:
            self.log_yaz(f"!!! Dönüştürme Hatası: {e}")
            return False

    def arayuz_sifirla(self, tamamlandi_mi):
        """Thread-safe UI Reset"""
        self.progress.stop()
        if tamamlandi_mi:
            self.progress['value'] = 100
        self.btn_baslat.config(state="normal")
        self.btn_iptal.config(state="disabled")

    def worker_thread(self, params):
        original_stderr = sys.stderr
        genel_baslangic = time.time()

        try:
            if params["kurulum_modu"]:
                self.log_yaz(">>> KURULUM BAŞLADI...")
                libs = ["openai-whisper", "faster-whisper", "huggingface_hub", "fpdf", "python-docx"]
                for lib in libs:
                    self.log_yaz(f"   -> Kontrol: {lib}")
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", lib],
                            capture_output=True, text=True, check=True)
                    except subprocess.CalledProcessError as e:
                        raise Exception(f"{lib} kurulumu başarısız oldu. Detay: {e.stderr}")

                self.log_yaz("   -> Kontrol: PyTorch (CUDA)")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install",
                        "torch", "torchvision", "torchaudio",
                        "--index-url", "https://download.pytorch.org/whl/cu124"],
                        capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError:
                    raise Exception("PyTorch kurulumu başarısız oldu.")
                self.log_yaz(">>> Kurulum bitti.\n")

            gorunen_isim = params["secilen_model_gorunum"]
            model_key = self.model_display_map.get(gorunen_isim)
            if not model_key:
                raise ValueError(
                    f"Geçersiz model seçimi: '{gorunen_isim}'. Lütfen listeden bir model seçin.")
            hedef_model_yolu = PATHS[model_key]

            if not os.path.exists(hedef_model_yolu):
                self.log_yaz(f"\nİNDİRİLİYOR: {hedef_model_yolu}")
                self.root.after(0, self.islem_durumu.set, "Model İndiriliyor...")
                if "faster" in model_key:
                    from faster_whisper import download_model
                    repo_id = ("turbo" if "turbo" in model_key else "large-v3")
                    download_model(repo_id, output_dir=hedef_model_yolu)
                    self.log_yaz("İndirme tamamlandı!")
                    self.root.after(0, self.modelleri_tara_ve_guncelle)
                else:
                    import whisper
                    _model_name = model_key.replace("std_", "").replace("large", "large-v3")
                    url = whisper._MODELS[_model_name]
                    from tqdm import tqdm
                    try:
                        with tqdm(unit='B', unit_scale=True, miniters=1, desc=_model_name) as t:
                            def reporthook(blocknum, blocksize, totalsize):
                                t.total = totalsize
                                t.update(blocknum * blocksize - t.n)
                            urllib.request.urlretrieve(url, hedef_model_yolu, reporthook=reporthook)
                        self.log_yaz("İndirme tamamlandı!")
                    except Exception as e:
                        self.log_yaz(f"İndirme hatası: {e}")

            with self._model_lock:
                if self.yuklu_model_key != model_key:
                    if self.yuklu_model is not None:
                        self.log_yaz(">>> Önceki model VRAM'den temizleniyor...")
                        del self.yuklu_model
                        self.yuklu_model = None
                        gc.collect()
                        try:
                            import torch
                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                        except ImportError:
                            pass
                    self.yuklu_model_key = model_key
                    model_yuklenmeli = True
                else:
                    model_yuklenmeli = False
                    self.log_yaz(">>> Model VRAM'de zaten yüklü, doğrudan kullanılıyor...")

            if "faster" in model_key:
                from faster_whisper import WhisperModel
                if model_yuklenmeli:
                    self.root.after(0, self.islem_durumu.set, "Model Yükleniyor...")
                    loaded = WhisperModel(hedef_model_yolu, device="cuda",
                        compute_type=params["secilen_compute"], local_files_only=True)
                    with self._model_lock:
                        self.yuklu_model = loaded
            else:
                import whisper
                if model_yuklenmeli:
                    self.root.after(0, self.islem_durumu.set, "Model Yükleniyor...")
                    load_arg = (hedef_model_yolu if os.path.exists(hedef_model_yolu)
                        else model_key.replace("std_", "").replace("large", "large-v3"))
                    loaded = whisper.load_model(load_arg, device="cuda")
                    with self._model_lock:
                        self.yuklu_model = loaded

            toplam_dosya = len(params["secilen_dosyalar"])

            for index, dosya in enumerate(params["secilen_dosyalar"]):
                if self.iptal_istendi:
                    break

                self.root.after(0, self.progress_guncelle, 0)
                durum_metni = f"Dosya {index+1}/{toplam_dosya} Çıkarılıyor..." if toplam_dosya > 1 else "Çıkarılıyor..."
                self.root.after(0, self.islem_durumu.set, durum_metni)

                if toplam_dosya == 1:
                    nihai_cikti = params["cikti_konumu"]
                else:
                    nihai_cikti = self.out_ismi_uret(dosya)

                temp_txt_path = os.path.splitext(nihai_cikti)[0] + "_temp.txt"
                self._current_temp_path = temp_txt_path
                with open(temp_txt_path, "w", encoding="utf-8") as f:
                    pass

                hedef_dil_kodu = LANGUAGE_OPTIONS[params["secilen_dil_adi"]]
                secilen_format = params["secilen_format"]
                vad_aktif = params["anti_loop_modu"]
                zaman_damgasi_aktif = params["zaman_damgasi_var"]
                tek_blok_aktif = params["tek_blok_modu"]
                cevir_aktif = params["ceviri_modu"]
                gorev = "translate" if cevir_aktif else "transcribe"

                if "XML" in secilen_format and not zaman_damgasi_aktif:
                    zaman_damgasi_aktif = True

                self.log_yaz(f"\n{'='*50}")
                self.log_yaz(f"[{index+1}/{toplam_dosya}] İşlenen: {os.path.basename(dosya)}")
                self.log_yaz(f"Model: {model_key} | Compute: {params['secilen_compute']} | Görev: {gorev.upper()}")
                self.log_yaz(f"{'='*50}\n")

                baslangic = time.time()

                if "faster" in model_key:
                    transcribe_args = {
                        "beam_size": params["beam_size_val"],
                        "language": hedef_dil_kodu,
                        "task": gorev,
                        "condition_on_previous_text": not vad_aktif,
                        "vad_filter": vad_aktif,
                        "word_timestamps": False
                    }
                    if vad_aktif:
                        transcribe_args["vad_parameters"] = dict(min_silence_duration_ms=500)

                    if vad_aktif:
                        try:
                            transcribe_args["repetition_penalty"] = 1.1
                        except Exception as rp_err:
                            self.log_yaz(f"! Uyarı: repetition_penalty parametresi uygulanamadı: {rp_err}")

                    segments, info = self.yuklu_model.transcribe(dosya, **transcribe_args)
                    self.log_yaz(f"Algılanan Dil: {info.language.upper()}\n")

                    with open(temp_txt_path, "w", encoding="utf-8", buffering=1) as f:
                        for segment in segments:
                            if info.duration > 0:
                                self.progress_guncelle((segment.end / info.duration) * 100)

                            text = segment.text.strip()
                            if zaman_damgasi_aktif:
                                zaman = self._format_timestamp(segment.start)
                                satir = f"{zaman} {text}\n"
                            elif tek_blok_aktif:
                                satir = f"{text} "
                            else:
                                satir = f"{text}\n"

                            f.write(satir)
                            self.log_yaz(satir.strip())

                            if self.iptal_istendi:
                                break

                else:  # Standard Whisper
                    yakalayici = TqdmYakalayici(self.progress_guncelle)
                    sys.stderr = yakalayici
                    try:
                        result = self.yuklu_model.transcribe(
                            dosya, language=hedef_dil_kodu, task=gorev, verbose=False,
                            condition_on_previous_text=not vad_aktif, no_speech_threshold=0.6,
                            beam_size=params["beam_size_val"]
                        )

                        with open(temp_txt_path, "w", encoding="utf-8", buffering=1) as f:
                            for segment in result["segments"]:
                                text = segment["text"].strip()
                                if zaman_damgasi_aktif:
                                    zaman = self._format_timestamp(segment["start"])
                                    satir = f"{zaman} {text}\n"
                                elif tek_blok_aktif:
                                    satir = f"{text} "
                                else:
                                    satir = f"{text}\n"

                                f.write(satir)
                                self.log_yaz(text[:100] + "..." if tek_blok_aktif else satir.strip())
                    finally:
                        sys.stderr = original_stderr

                if "TXT" in secilen_format:
                    if os.path.exists(nihai_cikti):
                        os.remove(nihai_cikti)
                    os.rename(temp_txt_path, nihai_cikti)
                else:
                    if self.dosya_donustur(temp_txt_path, nihai_cikti, secilen_format):
                        if os.path.exists(temp_txt_path):
                            os.remove(temp_txt_path)
                    else:
                        nihai_cikti = temp_txt_path

                self._current_temp_path = ""

                sure = time.time() - baslangic
                self.log_yaz(f"\n✓ Dosya Süresi: {sure:.2f} saniye")

            if self.iptal_istendi:
                self.root.after(0, self.islem_durumu.set, "⚠ Durduruldu")
                self.root.after(0, lambda: self.arayuz_sifirla(False))
                self.log_yaz("\nİşlem kullanıcı tarafından durduruldu.")
            else:
                self.root.after(0, lambda: self.arayuz_sifirla(True))
                self.root.after(0, self.islem_durumu.set, "✓ Tamamlandı")
                toplam_gecen = time.time() - genel_baslangic
                self.log_yaz(f"\n{'='*50}\nTOPLAM SÜRE: {toplam_gecen:.2f} saniye\n{'='*50}")
                self.root.after(0, lambda s=toplam_gecen: messagebox.showinfo(
                    "Başarılı", f"Tüm işlemler tamamlandı!\nToplam Süre: {s:.2f} saniye"))

        except RuntimeError as re:
            err_msg = str(re).lower()
            if "memory" in err_msg or "cuda out of memory" in err_msg or "allocate" in err_msg:
                self.root.after(0, self.islem_durumu.set, "❌ Bellek Yetersiz (VRAM)")
                self.log_yaz("\nKRİTİK HATA: Ekran Kartı Belleği (VRAM) Tükendi!")

                with self._model_lock:
                    if hasattr(self, 'yuklu_model') and self.yuklu_model is not None:
                        del self.yuklu_model
                        self.yuklu_model = None
                        self.yuklu_model_key = None
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass

                self.root.after(0, lambda err=re: messagebox.showerror(
                    "Yetersiz Bellek",
                    f"VRAM yetersiz kaldı.\n'Compute' tipini int8 yapmayı deneyin.\n\nDetay:\n{str(err)}"))
            else:
                self.hata_yonetimi(re)

        except Exception as e:
            self.hata_yonetimi(e)

        finally:
            sys.stderr = original_stderr

            if self._current_temp_path and os.path.exists(self._current_temp_path):
                try:
                    os.remove(self._current_temp_path)
                    self.log_yaz(f"! Geçici dosya temizlendi: {os.path.basename(self._current_temp_path)}")
                except OSError:
                    pass
            self._current_temp_path = ""

            self.root.after(0, lambda: self.btn_baslat.config(state="normal"))
            self.root.after(0, lambda: self.btn_iptal.config(state="disabled"))

    def hata_yonetimi(self, e):
        self.root.after(0, self.islem_durumu.set, "❌ Hata!")
        err_msg = str(e).lower()
        
        if "no cuda-capable device" in err_msg or "cuda failed" in err_msg or "cublas" in err_msg:
            kullanici_mesaji = (
                "Sisteminizde gerekli donanımsal ivmelenmeyi sağlayacak bir NVIDIA ekran kartı (GPU) bulunamadı "
                "veya ekran kartı sürücüleriniz aktif değil.\n\n"
                "Uygulamanın çalışabilmesi için CUDA destekli bir NVIDIA ekran kartına sahip olduğunuzdan ve "
                "grafik sürücülerinizin güncel olduğundan emin olun."
            )
            self.log_yaz(f"\n{'='*58}\nDONANIM HATASI: NVIDIA GPU algılanamadı veya sürücü eksik.\n{'='*58}")
            self.root.after(0, lambda: messagebox.showerror("Ekran Kartı Bulunamadı", kullanici_mesaji))
        
        else:
            self.log_yaz(f"\n{'='*50}\nHATA: {str(e)}\n{'='*50}")
            self.root.after(0, lambda err=e: messagebox.showerror(
                "İşlem Hatası", f"Beklenmeyen bir hata oluştu:\n\n{str(err)}"))


if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()
