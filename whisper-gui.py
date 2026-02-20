import os
import sys
import threading
import time
import subprocess
import re
import shutil
import urllib.request
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# SETTINGS AND FILE PATHS
# ============================================================================
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
    "Çince": "cn",
    "Japonca": "ja"
}

FORMAT_OPTIONS = ["PDF", "DOCX", "XML (Altyazı)", "TXT"]

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
        self.secilen_dosya = tk.StringVar()
        self.cikti_konumu = tk.StringVar()
        self.secilen_format = tk.StringVar(value=FORMAT_OPTIONS[0]) 
        self.secilen_model_gorunum = tk.StringVar()
        self.secilen_dil_adi = tk.StringVar(value="Otomatik Algıla")
        
        self.kurulum_modu = tk.BooleanVar(value=False)
        self.tek_blok_modu = tk.BooleanVar(value=True)
        self.anti_loop_modu = tk.BooleanVar(value=True) 
        self.zaman_damgasi_var = tk.BooleanVar(value=False)
        self.islem_durumu = tk.StringVar(value="Hazır")
        self.iptal_istendi = False
        self.model_display_map = {}

        self.yuklu_model = None
        self.yuklu_model_key = None

        self.setup_styles()
        self.arayuz_olustur()
        self.modelleri_tara_ve_guncelle()

    def setup_styles(self):
        """Configure modern styles for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color scheme
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
        
        # Button styles
        style.configure("Primary.TButton", 
            background=self.colors['primary'],
            foreground="white",
            borderwidth=0,
            focuscolor='none',
            padding=(20, 12),
            font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton",
            background=[('active', self.colors['primary_dark'])])
        
        style.configure("Danger.TButton", 
            background=self.colors['danger'],
            foreground="white",
            borderwidth=0,
            focuscolor='none',
            padding=(20, 12),
            font=("Segoe UI", 10, "bold"))
        style.map("Danger.TButton",
            background=[('active', '#D32F2F')])
        
        style.configure("Secondary.TButton",
            background=self.colors['bg_white'],
            foreground=self.colors['text_dark'],
            borderwidth=1,
            relief="solid",
            focuscolor='none',
            padding=(15, 8),
            font=("Segoe UI", 9))
        
        # Frame styles
        style.configure("Card.TFrame", background=self.colors['bg_white'], relief="flat")
        style.configure("TLabelframe", background=self.colors['bg_white'], borderwidth=0)
        style.configure("TLabelframe.Label", background=self.colors['bg_white'], 
            foreground=self.colors['text_dark'], font=("Segoe UI", 10, "bold"))
        
        # Other widgets
        style.configure("TLabel", background=self.colors['bg_white'], 
            foreground=self.colors['text_dark'], font=("Segoe UI", 9))
        style.configure("TCheckbutton", background=self.colors['bg_white'],
            foreground=self.colors['text_dark'], font=("Segoe UI", 9))
        style.configure("TCombobox", fieldbackground="white", 
            background="white", borderwidth=1)

    def ffmpeg_kontrol_et_ve_kur(self):
        """Check and install FFmpeg if needed"""
        if shutil.which("ffmpeg"):
            return

        root = tk.Tk()
        root.withdraw()
        cevap = messagebox.askyesno(
            "FFmpeg Eksik", 
            "Sisteminizde FFmpeg bulunamadı. Ses işleme için bu araç gereklidir.\n\n"
            "GitHub deposundan otomatik kurulum scriptini indirip kurmak ister misiniz?"
        )
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
            os.execl(sys.executable, sys.executable, *sys.argv)

        except Exception as e:
            messagebox.showerror("Kurulum Hatası", f"Otomatik kurulum başarısız oldu:\n{e}")

    def on_blok_change(self):
        """Tek blok seçildiğinde zaman damgasını kapat"""
        if self.tek_blok_modu.get():
            self.zaman_damgasi_var.set(False)

    def on_time_change(self):
        """Zaman damgası seçildiğinde tek blok modunu kapat"""
        if self.zaman_damgasi_var.get():
            self.tek_blok_modu.set(False)

    def arayuz_olustur(self):
        """Modern Split Layout Interface"""
        self.create_header(self.root)
        
        main_body = tk.Frame(self.root, bg="#f0f0f0")
        main_body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- SOL PANEL ---
        left_panel = tk.Frame(main_body, bg="#f0f0f0", width=900)
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        # --- SAĞ PANEL ---
        right_panel = tk.Frame(main_body, bg="#f0f0f0")
        right_panel.pack(side="left", fill="both", expand=True)

        # SOL İÇERİK
        left_content = tk.Frame(left_panel, bg="#f0f0f0")
        left_content.pack(side="top", fill="x")
        
        self.create_file_section(left_content)
        self.create_settings_section(left_content)
        self.create_progress_section(left_content)
        self.create_control_section(left_content)

        # SAĞ PANEL İÇERİĞİ (Loglar)
        self.create_log_section(right_panel)

    def create_header(self, parent):
        """Create header section"""
        header_frame = tk.Frame(parent, bg=self.colors['primary'], height=80)
        header_frame.pack(side="top", fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_container = tk.Frame(header_frame, bg=self.colors['primary'])
        title_container.pack(expand=True, fill="both", padx=20)

        title_label = tk.Label(title_container, 
            text="🎙️ Whisper Transkript Çevirici",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['primary'],
            fg="white")
        title_label.pack(side="left", pady=20)
        
        subtitle_label = tk.Label(title_container,
            text="Ses ve video dosyalarınızı metne dönüştürün",
            font=("Segoe UI", 11),
            bg=self.colors['primary'],
            fg="#E3F2FD")
        subtitle_label.pack(side="right", pady=25)

    def create_file_section(self, parent):
        """Create file selection section"""
        file_frame = ttk.LabelFrame(parent, text="📁 Dosya ve Format Seçimi", padding=15, style="Card.TFrame")
        file_frame.pack(fill="x", pady=(0, 10))
        
        input_container = tk.Frame(file_frame, bg=self.colors['bg_white'])
        input_container.pack(fill="x", pady=(0, 10))
        
        tk.Label(input_container, text="Kaynak Dosya:", 
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white'],
            fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 5))
        
        input_row = tk.Frame(input_container, bg=self.colors['bg_white'])
        input_row.pack(fill="x")
        
        entry_input = tk.Entry(input_row, textvariable=self.secilen_dosya,
            font=("Segoe UI", 9), relief="solid", borderwidth=1)
        entry_input.pack(side="left", fill="x", expand=True, ipady=8)
        
        btn_browse = ttk.Button(input_row, text="Dosya Seç", 
            command=self.dosya_sec, style="Secondary.TButton")
        btn_browse.pack(side="right", padx=(10, 0))
        
        output_container = tk.Frame(file_frame, bg=self.colors['bg_white'])
        output_container.pack(fill="x")
        
        out_opts_row = tk.Frame(output_container, bg=self.colors['bg_white'])
        out_opts_row.pack(fill="x")

        # Format Selection
        format_frame = tk.Frame(out_opts_row, bg=self.colors['bg_white'])
        format_frame.pack(side="left", padx=(0, 10))
        
        tk.Label(format_frame, text="Çıktı Formatı:", 
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
            
        self.combo_format = ttk.Combobox(format_frame, 
            textvariable=self.secilen_format,
            values=FORMAT_OPTIONS,
            state="readonly", width=20, font=("Segoe UI", 9))
        self.combo_format.pack(fill="x", ipady=5)
        self.combo_format.bind("<<ComboboxSelected>>", self.format_degisti)

        # File Path
        path_frame = tk.Frame(out_opts_row, bg=self.colors['bg_white'])
        path_frame.pack(side="left", fill="x", expand=True)

        tk.Label(path_frame, text="Çıktı Yolu:", 
            font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white'],
            fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 5))
        
        path_inner_row = tk.Frame(path_frame, bg=self.colors['bg_white'])
        path_inner_row.pack(fill="x")
        
        entry_output = tk.Entry(path_inner_row, textvariable=self.cikti_konumu,
            font=("Segoe UI", 9), relief="solid", borderwidth=1)
        entry_output.pack(side="left", fill="x", expand=True, ipady=8)
        
        btn_save = ttk.Button(path_inner_row, text="Değiştir",
            command=self.kayit_yeri_sec, style="Secondary.TButton")
        btn_save.pack(side="right", padx=(10, 0))

    def create_settings_section(self, parent):
        """Create settings section"""
        settings_frame = ttk.LabelFrame(parent, text="⚙️ Ayarlar", padding=15, style="Card.TFrame")
        settings_frame.pack(fill="x", pady=(0, 10))
        
        selection_frame = tk.Frame(settings_frame, bg=self.colors['bg_white'])
        selection_frame.pack(fill="x", pady=(0, 10))
        
        # Model selection
        model_frame = tk.Frame(selection_frame, bg=self.colors['bg_white'])
        model_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        tk.Label(model_frame, text="Model:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_model = ttk.Combobox(model_frame, 
            textvariable=self.secilen_model_gorunum,
            state="readonly", font=("Segoe UI", 9))
        self.combo_model.pack(fill="x", ipady=5)
        
        self.combo_model.bind("<<ComboboxSelected>>", lambda e: self.guncelle_cikti_yolu())
        
        # Language selection
        lang_frame = tk.Frame(selection_frame, bg=self.colors['bg_white'])
        lang_frame.pack(side="left", fill="x", expand=True)
        
        tk.Label(lang_frame, text="Dil:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 5))
        self.combo_lang = ttk.Combobox(lang_frame,
            textvariable=self.secilen_dil_adi,
            values=list(LANGUAGE_OPTIONS.keys()),
            state="readonly", font=("Segoe UI", 9))
        self.combo_lang.pack(fill="x", ipady=5)
        
        # Options checkboxes
        options_frame = tk.Frame(settings_frame, bg=self.colors['bg_white'])
        options_frame.pack(fill="x")
        
        tk.Label(options_frame, text="Seçenekler:", font=("Segoe UI", 9, "bold"),
            bg=self.colors['bg_white']).pack(anchor="w", pady=(0, 8))
        
        checks_container = tk.Frame(options_frame, bg=self.colors['bg_white'])
        checks_container.pack(fill="x")
        
        chk_vad = ttk.Checkbutton(checks_container, 
            text="🔄 Anti-Loop (VAD)",
            variable=self.anti_loop_modu)
        chk_vad.pack(side="left", padx=(0, 20))

        chk_blok = ttk.Checkbutton(checks_container,
            text="📄 Tek Blok Metin",
            variable=self.tek_blok_modu,
            command=self.on_blok_change)
        chk_blok.pack(side="left", padx=(0, 20))
        
        chk_time = ttk.Checkbutton(checks_container,
            text="🕐 Zaman Damgası",
            variable=self.zaman_damgasi_var,
            command=self.on_time_change)
        chk_time.pack(side="left", padx=(0, 20))
        
        chk_setup = ttk.Checkbutton(checks_container,
            text="🔧 İlk Kullanım (Kurulum)",
            variable=self.kurulum_modu)
        chk_setup.pack(side="left")

    def create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = tk.Frame(parent, bg="#f0f0f0")
        control_frame.pack(fill="x", pady=(0, 10))
        
        self.btn_baslat = ttk.Button(control_frame, 
            text="▶ BAŞLAT",
            command=self.islem_baslat,
            style="Primary.TButton")
        self.btn_baslat.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_iptal = ttk.Button(control_frame,
            text="⏹ DURDUR & KAYDET",
            command=self.iptal_et,
            style="Danger.TButton",
            state="disabled")
        self.btn_iptal.pack(side="left", fill="x", expand=True)

    def create_progress_section(self, parent):
        """Create progress section"""
        progress_frame = ttk.LabelFrame(parent, text="📊 İlerleme", 
            padding=15, style="Card.TFrame")
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.lbl_durum = tk.Label(progress_frame,
            textvariable=self.islem_durumu,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg_white'],
            fg=self.colors['primary'])
        self.lbl_durum.pack(anchor="w", pady=(0, 8))
        
        self.progress = ttk.Progressbar(progress_frame,
            orient="horizontal",
            mode="determinate",
            length=400)
        self.progress.pack(fill="x")

    def create_log_section(self, parent):
        """Create log section"""
        log_frame = ttk.LabelFrame(parent, text="📝 İşlem Kayıtları",
            padding=15, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True)
        
        log_container = tk.Frame(log_frame, bg=self.colors['bg_white'])
        log_container.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(log_container)
        scrollbar.pack(side="right", fill="y")
        
        self.txt_log = tk.Text(log_container,
            font=("Consolas", 9),
            bg="#FAFAFA",
            fg=self.colors['text_dark'],
            relief="flat",
            yscrollcommand=scrollbar.set,
            wrap="word",
            height=15,
            padx=10,
            pady=10)
        self.txt_log.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.txt_log.yview)

    def log_yaz(self, mesaj):
        """Write message to log"""
        self.txt_log.insert(tk.END, mesaj + "\n")
        self.txt_log.see(tk.END)

    def modelleri_tara_ve_guncelle(self):
        """Scan and update available models"""
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

    def dosya_sec(self):
        """Select input file"""
        dosya = filedialog.askopenfilename(
            title="Ses veya Video Dosyası Seçin",
            filetypes=[
                ("Medya Dosyaları", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.flac *.ogg *.webm *.opus"),
                ("Tümü", "*.*")
            ])
        if dosya:
            self.secilen_dosya.set(dosya)
            self.guncelle_cikti_yolu(dosya)

    def format_degisti(self, event=None):
        """Handle format change"""
        dosya = self.secilen_dosya.get()
        if dosya:
            self.guncelle_cikti_yolu(dosya)

    def guncelle_cikti_yolu(self, input_dosya=None):
        """Update output path based on format AND model"""
        if input_dosya is None:
            input_dosya = self.secilen_dosya.get()
            
        if not input_dosya:
            return

        klasor, isim = os.path.split(input_dosya)
        isim_kok = os.path.splitext(isim)[0]
        
        # Seçili modelin kısa kodunu bul (örn: faster_large)
        secilen_gorunum = self.secilen_model_gorunum.get()
        model_kodu = "whisper" # Varsayılan
        
        if secilen_gorunum and self.model_display_map:
            ham_kod = self.model_display_map.get(secilen_gorunum, "")
            model_kodu = ham_kod.replace("_", "-")

        format_str = self.secilen_format.get()
        ext = ".txt"
        if "PDF" in format_str: ext = ".pdf"
        elif "DOCX" in format_str: ext = ".docx"
        elif "XML" in format_str: ext = ".xml"
        
        # DosyaAdi_ModelAdi_transkript.uzanti
        yeni_isim = f"{isim_kok}_{model_kodu}_transkript{ext}"
        self.cikti_konumu.set(os.path.join(klasor, yeni_isim))

    def kayit_yeri_sec(self):
        """Select output file"""
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

        dosya = filedialog.asksaveasfilename(
            title="Çıktı Dosyasını Kaydet",
            defaultextension=ext,
            filetypes=ftypes)
        if dosya:
            self.cikti_konumu.set(dosya)

    def progress_guncelle(self, yuzde):
        """Update progress bar"""
        self.progress['value'] = yuzde
        self.islem_durumu.set(f"İşleniyor... %{yuzde:.1f}")
        self.root.update_idletasks()

    def iptal_et(self):
        """Cancel operation"""
        if messagebox.askyesno("Durdur", "İşlem durdurulsun ve kaydedilsin mi?"):
            self.iptal_istendi = True
            self.btn_iptal.config(state="disabled")

    def uygulamayi_kapat(self):
        """Uygulama kapatılırken thread'leri ve VRAM'i güvenle temizle"""
        if hasattr(self, 'btn_iptal') and str(self.btn_iptal['state']) == 'normal':
            cevap = messagebox.askyesno(
                "Çıkış", 
                "Şu anda devam eden bir transkript işlemi var.\nUygulamadan çıkmak istediğinize emin misiniz?"
            )
            if not cevap:
                return
            
            self.iptal_istendi = True

        self.log_yaz(">>> Uygulama kapatılıyor, bellek temizleniyor...")
        self.root.update()

        if hasattr(self, 'yuklu_model') and self.yuklu_model is not None:
            del self.yuklu_model
            self.yuklu_model = None
            import gc
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
        """Start transcription process"""
        if not self.secilen_dosya.get():
            messagebox.showwarning("Uyarı", "Lütfen bir dosya seçin.")
            return
        
        self.btn_baslat.config(state="disabled")
        self.btn_iptal.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.iptal_istendi = False
        
        t = threading.Thread(target=self.worker_thread, daemon=True)
        t.start()

    def xml_olustur(self, input_text):
        xml_output = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<tt xmlns="http://www.w3.org/ns/ttml" xml:lang="tr">',
            '  <body>',
            '    <div>'
        ]

        lines = input_text.strip().split('\n')
        parsed_lines = []

        # Regex: [dakika:saniye] Metin
        pattern = re.compile(r'\[(\d{2}):(\d{2})\]\s*(.*)')

        for line in lines:
            match = pattern.match(line.strip())
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                text = match.group(3)
                total_seconds = (minutes * 60) + seconds
                parsed_lines.append({'time': total_seconds, 'text': text})

        for i in range(len(parsed_lines)):
            current_line = parsed_lines[i]
            start_sec = current_line['time']
            
            if i < len(parsed_lines) - 1:
                end_sec = parsed_lines[i+1]['time']
            else:
                end_sec = start_sec + 3.0 

            def format_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds - int(seconds)) * 1000)
                return f"{h:02}:{m:02}:{s:02}.{ms:03}"

            safe_text = current_line['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            p_tag = f'      <p begin="{format_time(start_sec)}" end="{format_time(end_sec)}">{safe_text}</p>'
            xml_output.append(p_tag)

        xml_output.append('    </div>')
        xml_output.append('  </body>')
        xml_output.append('</tt>')

        return "\n".join(xml_output)

    def dosya_donustur(self, txt_yolu, hedef_yolu, format_tipi):
        """Convert txt to requested format safely with robust auto-install check"""
        try:
            # --- YARDIMCI FONKSİYON: GÜVENLİ YÜKLEME ---
            def kutuphane_yukle_ve_al(paket_adi, import_adi):
                try:
                    __import__(import_adi)
                    return True
                except ImportError:
                    self.log_yaz(f">>> Uyarı: '{paket_adi}' eksik, otomatik yükleniyor...")
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", paket_adi],
                            check=True,
                            capture_output=True,
                            startupinfo=startupinfo
                        )
                        __import__(import_adi)
                        self.log_yaz(f"   -> '{paket_adi}' başarıyla kuruldu.")
                        return True
                    except subprocess.CalledProcessError:
                        self.log_yaz(f"!!! KRİTİK: '{paket_adi}' yüklenemedi (Non-zero exit).")
                        return False
            # -------------------------------------------

            # 1. GEREKLİLİK KONTROLLERİ
            if "DOCX" in format_tipi:
                if not kutuphane_yukle_ve_al("python-docx", "docx"):
                    raise Exception("Gerekli kütüphane (python-docx) kurulamadığı için işlem iptal edildi.")

            elif "PDF" in format_tipi:
                if not kutuphane_yukle_ve_al("fpdf", "fpdf"):
                    raise Exception("Gerekli kütüphane (fpdf) kurulamadığı için işlem iptal edildi.")
            
            # 2. DOSYA OKUMA
            with open(txt_yolu, 'r', encoding='utf-8') as f:
                icerik = f.read()

            # 3. DÖNÜŞTÜRME İŞLEMİ
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
                
                class PDF(FPDF):
                    def header(self):
                        try:
                            self.add_font('Arial', '', r'C:\Windows\Fonts\arial.ttf', uni=True)
                            self.set_font('Arial', '', 10)
                        except:
                            self.set_font('Arial', '', 10)
                        self.cell(0, 10, 'Transkript', 0, 1, 'C')

                pdf = PDF()
                pdf.add_page()
                try:
                    pdf.add_font('Arial', '', r'C:\Windows\Fonts\arial.ttf', uni=True)
                    pdf.set_font("Arial", size=11)
                except:
                    self.log_yaz("! Uyarı: Arial fontu bulunamadı, standart font kullanılıyor.")
                    pdf.set_font("Arial", size=11)
                
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
            self.log_yaz("! Dosya TXT formatında bırakıldı.")
            return False

    def worker_thread(self):
        """Worker thread for transcription"""
        original_stderr = sys.stderr
        temp_txt_path = ""
        
        try:
            # Setup mode
            if self.kurulum_modu.get():
                self.log_yaz(">>> KURULUM BAŞLADI...")
                libs = ["openai-whisper", "faster-whisper", "huggingface_hub", "fpdf", "python-docx"]
                
                for lib in libs:
                    self.log_yaz(f"   -> Kontrol: {lib}")
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "pip", "install", lib], 
                            capture_output=True, text=True, check=True
                        )
                    except subprocess.CalledProcessError as e:
                        self.log_yaz(f"!!! HATA: {lib} kurulamadı!")
                        self.log_yaz(f"Hata Detayı: {e.stderr}")
                        raise Exception(f"{lib} kurulumu başarısız oldu.")

                self.log_yaz("   -> Kontrol: PyTorch (CUDA)")
                try:
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", 
                        "torch", "torchvision", "torchaudio", 
                        "--index-url", "https://download.pytorch.org/whl/cu124"
                    ], capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    self.log_yaz("!!! HATA: PyTorch kurulamadı!")
                    raise Exception("PyTorch kurulumu başarısız oldu.")

                self.log_yaz(">>> Kurulum bitti.\n")

            # Model preparation
            gorunen_isim = self.secilen_model_gorunum.get()
            model_key = self.model_display_map[gorunen_isim]
            hedef_model_yolu = PATHS[model_key]
            
            if not os.path.exists(hedef_model_yolu):
                self.log_yaz(f"\nİNDİRİLİYOR: {hedef_model_yolu}")
                self.islem_durumu.set("Model İndiriliyor...")
                
                if "faster" in model_key:
                    from faster_whisper import download_model
                    repo_id = ("turbo" if "turbo" in model_key else "large-v3")
                    download_model(repo_id, output_dir=hedef_model_yolu)
                    self.log_yaz("İndirme tamamlandı!")
                    self.root.after(0, self.modelleri_tara_ve_guncelle)
                else:
                    self.log_yaz(f"Standart model indiriliyor: {model_key}...")
                    import whisper
                    _model_name = model_key.replace("std_", "").replace("large", "large-v3")
                    url = whisper._MODELS[_model_name]
                    import urllib.request
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

            # Transcription Variables
            hedef_dil_kodu = LANGUAGE_OPTIONS[self.secilen_dil_adi.get()]
            dosya = self.secilen_dosya.get()
            nihai_cikti = self.cikti_konumu.get()
            secilen_format = self.secilen_format.get()
            
            temp_txt_path = os.path.splitext(nihai_cikti)[0] + "_temp.txt"
            
            vad_aktif = self.anti_loop_modu.get()
            zaman_damgasi_aktif = self.zaman_damgasi_var.get()
            tek_blok_aktif = self.tek_blok_modu.get()

            if "XML" in secilen_format:
                if not zaman_damgasi_aktif:
                    zaman_damgasi_aktif = True
                    self.log_yaz("! XML formatı seçildiği için zaman damgaları otomatik aktifleştirildi.")
            # -------------------------------------------

            self.log_yaz(f"\n{'='*50}")
            self.log_yaz(f"Dosya: {os.path.basename(dosya)}")
            self.log_yaz(f"Model: {model_key}")
            self.log_yaz(f"Format: {secilen_format}")
            self.log_yaz(f"{'='*50}\n")
            
            baslangic = time.time()

            # --- VRAM KONTROLÜ VE MODEL YÜKLEME YÖNETİMİ ---
            if self.yuklu_model_key != model_key:
                if self.yuklu_model is not None:
                    self.log_yaz(">>> Önceki model VRAM'den temizleniyor...")
                    del self.yuklu_model
                    self.yuklu_model = None
                    import gc
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
            # -----------------------------------------------

            # Döngü başlamadan önce temp dosyasını temizle/oluştur
            open(temp_txt_path, "w", encoding="utf-8").close()
            
            # --- WHISPER İŞLEMLERİ ---
            if "faster" in model_key:
                from faster_whisper import WhisperModel
                if model_yuklenmeli:
                    self.islem_durumu.set("Model Yükleniyor...")
                    self.yuklu_model = WhisperModel(hedef_model_yolu, device="cuda", 
                        compute_type="int8", local_files_only=True)
                
                self.islem_durumu.set("Çıkarılıyor...")
                
                transcribe_args = {
                    "beam_size": 5,
                    "language": hedef_dil_kodu,
                    "condition_on_previous_text": not vad_aktif,
                    "vad_filter": vad_aktif,
                    "vad_parameters": dict(min_silence_duration_ms=500) if vad_aktif else None,
                    "word_timestamps": False
                }
                if vad_aktif:
                    try: transcribe_args["repetition_penalty"] = 1.1
                    except: pass

                segments, info = self.yuklu_model.transcribe(dosya, **transcribe_args)
                self.log_yaz(f"Algılanan Dil: {info.language.upper()}\n")
                
                # --- HİBRİT I/O: RAM Buffer ---
                toplu_metin = []
                segment_limiti = 50

                for segment in segments:
                    if info.duration > 0:
                        yuzde = (segment.end / info.duration) * 100
                        self.progress_guncelle(yuzde)
                    
                    text = segment.text.strip()
                    
                    if zaman_damgasi_aktif:
                        zaman = f"[{int(segment.start//60):02}:{int(segment.start%60):02}]"
                        satir = f"{zaman} {text}\n"
                    elif tek_blok_aktif:
                        satir = f"{text} "
                    else:
                        satir = f"{text}\n"
                    
                    toplu_metin.append(satir)
                    self.root.after(0, self.log_yaz, satir.strip())

                    # Buffer dolduğunda diske ekle ("a" modu) ve RAM'i boşalt
                    if len(toplu_metin) >= segment_limiti:
                        with open(temp_txt_path, "a", encoding="utf-8") as f:
                            f.writelines(toplu_metin)
                        toplu_metin.clear()

                    # İptal edildiyse döngüden çık
                    if self.iptal_istendi:
                        break

                # Döngü bittikten SONRA (iptal veya normal bitiş) RAM'de kalan son parçaları yaz
                if toplu_metin:
                    with open(temp_txt_path, "a", encoding="utf-8") as f:
                        f.writelines(toplu_metin)
                    toplu_metin.clear()

            else: # Standard Whisper
                import whisper
                if model_yuklenmeli:
                    self.islem_durumu.set("Model Yükleniyor...")
                    load_arg = (hedef_model_yolu if os.path.exists(hedef_model_yolu) 
                        else model_key.replace("std_","").replace("large","large-v3"))
                    self.yuklu_model = whisper.load_model(load_arg, device="cuda")
                self.islem_durumu.set("Çıkarılıyor...")
                
                yakalayici = TqdmYakalayici(self.progress_guncelle)
                sys.stderr = yakalayici
                try:
                    result = self.yuklu_model.transcribe(
                        dosya, language=hedef_dil_kodu, verbose=False, 
                        condition_on_previous_text=not vad_aktif, no_speech_threshold=0.6
                    )
                    
                    if not self.iptal_istendi:
                        # --- HİBRİT I/O: RAM Buffer ---
                        toplu_metin = []
                        segment_limiti = 50
                        
                        for i, segment in enumerate(result["segments"]):
                            text = segment["text"].strip()
                            
                            if zaman_damgasi_aktif:
                                start = segment["start"]
                                zaman = f"[{int(start//60):02}:{int(start%60):02}]"
                                satir = f"{zaman} {text}\n"
                            elif tek_blok_aktif:
                                satir = f"{text} "
                            else:
                                satir = f"{text}\n"
                                
                            toplu_metin.append(satir)
                            self.root.after(0, self.log_yaz, text[:100] + "..." if tek_blok_aktif else satir.strip())

                            # Buffer dolduğunda diske ekle ("a" modu) ve RAM'i boşalt
                            if len(toplu_metin) >= segment_limiti:
                                with open(temp_txt_path, "a", encoding="utf-8") as f:
                                    f.writelines(toplu_metin)
                                toplu_metin.clear()
                                
                        # Kalan son parçaları yaz
                        if toplu_metin:
                            with open(temp_txt_path, "a", encoding="utf-8") as f:
                                f.writelines(toplu_metin)
                            toplu_metin.clear()

                finally:
                    sys.stderr = original_stderr

            sure = time.time() - baslangic

            # --- DÖNÜŞTÜRME VE TEMİZLİK ---
            islem_basarili = True
            
            # Arayüzü sıfırlayacak yardımcı fonksiyon (Thread-Safe)
            def arayuz_sifirla(tamamlandi_mi):
                self.progress.stop()
                if tamamlandi_mi:
                    self.progress['value'] = 100
                self.btn_baslat.config(state="normal")
                self.btn_iptal.config(state="disabled")

            # Dönüştürme işlemini iptal veya başarı fark etmeksizin uygula
            if "TXT" in secilen_format:
                if os.path.exists(nihai_cikti): os.remove(nihai_cikti)
                os.rename(temp_txt_path, nihai_cikti)
            else:
                if self.dosya_donustur(temp_txt_path, nihai_cikti, secilen_format):
                    if os.path.exists(temp_txt_path):
                        os.remove(temp_txt_path) 
                else:
                    islem_basarili = False
                    self.log_yaz("! Dönüştürme başarısız olduğu için TXT dosyası korundu.")
                    nihai_cikti = temp_txt_path

            # Sonuç bildirimi (İptal veya Başarılı)
            if self.iptal_istendi:
                self.root.after(0, self.islem_durumu.set, "⚠ Durduruldu")
                self.root.after(0, arayuz_sifirla, False)
                
                self.log_yaz(f"\n{'='*50}")
                self.log_yaz("İşlem kullanıcı tarafından durduruldu.")
                self.log_yaz(f"Kısmi Kayıt: {os.path.basename(nihai_cikti)}")
                self.log_yaz(f"{'='*50}")
                
                self.root.after(0, lambda final_path=nihai_cikti: messagebox.showinfo(
                    "Bilgi", f"İşlem durduruldu.\n\nKısmi kayıt oluşturuldu:\n{os.path.basename(final_path)}"
                ))
            else:
                self.root.after(0, arayuz_sifirla, True)
                self.root.after(0, self.islem_durumu.set, "✓ Tamamlandı")
                
                self.log_yaz(f"\n{'='*50}")
                self.log_yaz(f"Toplam Süre: {sure:.2f} saniye")
                self.log_yaz(f"{'='*50}")

                self.root.after(0, lambda final_path=nihai_cikti, s=sure: messagebox.showinfo(
                    "Başarılı", f"İşlem tamamlandı!\n\nDosya: {os.path.basename(final_path)}\nSüre: {s:.2f} saniye"
                ))

        except RuntimeError as re:
            sys.stderr = original_stderr
            err_msg = str(re).lower()
            
            # OOM (Out of Memory) Tespiti
            if "memory" in err_msg or "cuda out of memory" in err_msg or "allocate" in err_msg:
                self.root.after(0, self.islem_durumu.set, "❌ Bellek Yetersiz (VRAM)")
                self.log_yaz(f"\n{'='*50}")
                self.log_yaz("KRİTİK HATA: Ekran Kartı Belleği (VRAM) Tükendi!")
                self.log_yaz("Çözüm Önerileri:")
                self.log_yaz("1. Daha küçük bir model seçin (Örn: Turbo veya Medium).")
                self.log_yaz("2. Arka planda GPU kullanan diğer programları kapatın.")
                self.log_yaz(f"{'='*50}\n")
                
                # Agresif VRAM Temizliği
                if hasattr(self, 'yuklu_model') and self.yuklu_model is not None:
                    del self.yuklu_model
                    self.yuklu_model = None
                    self.yuklu_model_key = None  # Key sıfırlanır, böylece sonraki denemede model temiz bir şekilde baştan yüklenir
                
                import gc
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
                
                self.root.after(0, lambda err=re: messagebox.showerror(
                    "Yetersiz Bellek (VRAM)", 
                    f"Seçilen model için ekran kartı belleği yetersiz kaldı.\nLütfen 'Turbo' modelini seçerek tekrar deneyin.\n\nDetay:\n{str(err)}"
                ))
            else:
                # Bellek hatası dışındaki RuntimeError istisnalarını genel exception bloğuna aktar
                self.hata_yonetimi(re)

        except Exception as e:
            sys.stderr = original_stderr
            self.hata_yonetimi(e)

        finally:
            # Hata olsun veya olmasın UI butonlarını eski haline getir
            self.root.after(0, lambda: self.btn_baslat.config(state="normal"))
            self.root.after(0, lambda: self.btn_iptal.config(state="disabled"))

    def hata_yonetimi(self, e):
        """Genel hata durumlarında log ve arayüz güncellemelerini thread-safe olarak yapar."""
        self.root.after(0, self.islem_durumu.set, "❌ Hata!")
        self.log_yaz(f"\n{'='*50}")
        self.log_yaz(f"HATA: {str(e)}")
        self.log_yaz(f"{'='*50}")
        self.root.after(0, lambda err=e: messagebox.showerror("İşlem Hatası", f"Beklenmeyen bir hata oluştu:\n\n{str(err)}"))

if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()
