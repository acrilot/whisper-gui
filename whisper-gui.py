import os
import sys
import threading
import time
import subprocess
import re
import shutil
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import warnings

# Gereksiz uyarıları gizle
warnings.filterwarnings("ignore")

# ============================================================================
# AYARLAR VE DOSYA YOLLARI
# ============================================================================
BASE_DIR = os.getcwd()

# KULLANICI GITHUB AYARI (BURAYI DÜZENLE)
# FFmpeg kurulumunu yapan .bat dosyanın "Raw" linkini buraya yapıştır.
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

# --- TQDM YAKALAYICI ---
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
        
        # 1. Başlangıçta FFmpeg Kontrolü
        self.ffmpeg_kontrol_et_ve_kur()

        self.root.title("Whisper GUI")
        self.root.geometry("1000x800")
        
        # Değişkenler
        self.secilen_dosya = tk.StringVar()
        self.cikti_konumu = tk.StringVar()
        self.secilen_model_gorunum = tk.StringVar()
        self.secilen_dil_adi = tk.StringVar(value="Otomatik Algıla")
        
        self.kurulum_modu = tk.BooleanVar(value=False)
        self.anti_loop_modu = tk.BooleanVar(value=True) 
        
        # YENİ: Zaman Damgası Seçeneği (Varsayılan: Seçili)
        self.zaman_damgasi_var = tk.BooleanVar(value=True)

        self.islem_durumu = tk.StringVar(value="Hazır")
        self.iptal_istendi = False
        self.model_display_map = {} 

        self.arayuz_olustur()
        self.modelleri_tara_ve_guncelle()

    def ffmpeg_kontrol_et_ve_kur(self):
        """
        Sistemde FFmpeg var mı bakar. Yoksa Github'dan scripti çeker, kurar ve restart atar.
        """
        if shutil.which("ffmpeg"):
            print("FFmpeg sistemde yüklü.")
            return

        # FFmpeg yoksa kullanıcıya sor
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
            print(">>> FFmpeg Kurulum Scripti İndiriliyor...")
            script_adi = "ffmpeg_installer_temp.bat"
            
            # Scripti indir
            urllib.request.urlretrieve(GITHUB_FFMPEG_URL, script_adi)
            
            print(">>> Kurulum Başlatılıyor (Lütfen bekleyin)...")
            # Batch scripti çalıştır (shell=True ile yeni pencerede açabilir veya gizli çalıştırabilirsin)
            subprocess.check_call([script_adi], shell=True)
            
            print(">>> Kurulum Tamamlandı. Geçici dosya siliniyor...")
            if os.path.exists(script_adi):
                os.remove(script_adi)
            
            messagebox.showinfo("Yeniden Başlatılıyor", "FFmpeg kuruldu. Değişikliklerin etkili olması için uygulama yeniden başlatılıyor.")
            
            # Uygulamayı Restart Et (Yeni PATH'i görmesi için)
            os.execl(sys.executable, sys.executable, *sys.argv)

        except Exception as e:
            messagebox.showerror("Kurulum Hatası", f"Otomatik kurulum başarısız oldu:\n{e}")
            # Yine de devam etsin mi? Kullanıcıya kalmış.

    def arayuz_olustur(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#e1e1e1")
        style.configure("Accent.TButton", background="#2f80ed", foreground="white", font=("Segoe UI", 10, "bold"))
        style.configure("Cancel.TButton", background="#d9534f", foreground="white", font=("Segoe UI", 10, "bold"))
        
        # --- ÜST PANEL ---
        frame_top = ttk.LabelFrame(self.root, text="Model ve Dil Ayarları", padding=15)
        frame_top.pack(fill="x", padx=15, pady=10)

        # Satır 1: Model ve Dil
        ttk.Label(frame_top, text="Model:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_model = ttk.Combobox(frame_top, textvariable=self.secilen_model_gorunum, state="readonly", width=50)
        self.combo_model.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(frame_top, text="Dil:").grid(row=0, column=2, sticky="w", padx=15)
        self.combo_lang = ttk.Combobox(frame_top, textvariable=self.secilen_dil_adi, values=list(LANGUAGE_OPTIONS.keys()), state="readonly", width=15)
        self.combo_lang.grid(row=0, column=3, sticky="w", padx=5)

        # Satır 2: Checkboxlar
        frame_checks = ttk.Frame(frame_top)
        frame_checks.grid(row=1, column=0, columnspan=4, sticky="w", pady=(10, 0))

        # Anti-Loop
        chk_loop = ttk.Checkbutton(frame_checks, text="Anti-Loop (VAD)", variable=self.anti_loop_modu)
        chk_loop.pack(side="left", padx=5)

        # YENİ: Zaman Damgası
        chk_time = ttk.Checkbutton(frame_checks, text="Zaman Damgası Ekle", variable=self.zaman_damgasi_var)
        chk_time.pack(side="left", padx=15)

        # Onarım Modu
        chk_setup = ttk.Checkbutton(frame_checks, text="İlk Kullanım", variable=self.kurulum_modu)
        chk_setup.pack(side="left", padx=15)
        
        # --- ORTA PANEL ---
        frame_mid = ttk.LabelFrame(self.root, text="Dosya İşlemleri", padding=15)
        frame_mid.pack(fill="x", padx=15, pady=5)

        ttk.Label(frame_mid, text="Dosya:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_mid, textvariable=self.secilen_dosya, width=70).grid(row=0, column=1, padx=5)
        ttk.Button(frame_mid, text="Seç", command=self.dosya_sec).grid(row=0, column=2, padx=5)

        ttk.Label(frame_mid, text="Kayıt:").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(frame_mid, textvariable=self.cikti_konumu, width=70).grid(row=1, column=1, padx=5, pady=10)
        ttk.Button(frame_mid, text="Değiştir", command=self.kayit_yeri_sec).grid(row=1, column=2, padx=5, pady=10)

        # --- ALT PANEL ---
        frame_bottom = ttk.Frame(self.root, padding=15)
        frame_bottom.pack(fill="both", expand=True, padx=15)

        btn_frame = ttk.Frame(frame_bottom)
        btn_frame.pack(fill="x", pady=5)

        self.btn_baslat = ttk.Button(btn_frame, text="BAŞLAT", command=self.islem_baslat, style="Accent.TButton")
        self.btn_baslat.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_iptal = ttk.Button(btn_frame, text="DURDUR & KAYDET", command=self.iptal_et, style="Cancel.TButton", state="disabled")
        self.btn_iptal.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.progress = ttk.Progressbar(frame_bottom, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", pady=10)
        
        self.lbl_durum = ttk.Label(frame_bottom, textvariable=self.islem_durumu, font=("Segoe UI", 9, "bold"), foreground="#555")
        self.lbl_durum.pack(anchor="w")

        self.txt_log = tk.Text(frame_bottom, height=12, font=("Consolas", 9), bg="#f8f9fa", borderwidth=1, relief="solid")
        self.txt_log.pack(fill="both", expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_bottom, orient="vertical", command=self.txt_log.yview)
        scrollbar.pack(side="right", fill="y")
        self.txt_log.configure(yscrollcommand=scrollbar.set)

    def log_yaz(self, mesaj):
        self.txt_log.insert(tk.END, mesaj + "\n")
        self.txt_log.see(tk.END)

    def modelleri_tara_ve_guncelle(self):
        self.model_display_map = {}
        yeni_liste = []
        varsayilan_secim = ""

        for friendly_name, model_key in RAW_MODEL_OPTIONS.items():
            path = PATHS[model_key]
            durum_ikonu = "HAZIR" if os.path.exists(path) else "İNDİRİLECEK"
            display_text = f"{friendly_name} [{durum_ikonu}]"
            
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
        dosya = filedialog.askopenfilename(filetypes=[("Medya", "*.mp3 *.wav *.m4a *.mp4 *.mkv *.flac *.ogg *.webm *.opus"), ("Tümü", "*.*")])
        if dosya:
            self.secilen_dosya.set(dosya)
            klasor, isim = os.path.split(dosya)
            isim_kok = os.path.splitext(isim)[0]
            self.cikti_konumu.set(os.path.join(klasor, f"{isim_kok}_transkript.txt"))

    def kayit_yeri_sec(self):
        dosya = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Metin Dosyası", "*.txt")])
        if dosya:
            self.cikti_konumu.set(dosya)

    def progress_guncelle(self, yuzde):
        self.progress['value'] = yuzde
        self.islem_durumu.set(f"İşleniyor... %{yuzde:.1f}")
        self.root.update_idletasks()

    def iptal_et(self):
        if messagebox.askyesno("Durdur", "İşlem durdurulsun ve kaydedilsin mi?"):
            self.iptal_istendi = True
            self.btn_iptal.config(state="disabled")

    def islem_baslat(self):
        if not self.secilen_dosya.get():
            messagebox.showwarning("Uyarı", "Dosya seçilmedi.")
            return
        
        self.btn_baslat.config(state="disabled")
        self.btn_iptal.config(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.progress['value'] = 0
        self.iptal_istendi = False
        
        t = threading.Thread(target=self.worker_thread)
        t.start()

    def worker_thread(self):
        original_stderr = sys.stderr
        
        try:
            # 1. ONARIM MODU
            if self.kurulum_modu.get():
                self.log_yaz(">>> KURULUM BAŞLADI...")
                libs = ["openai-whisper", "faster-whisper", "huggingface_hub"]
                for lib in libs:
                    self.log_yaz(f"   -> Kontrol: {lib}")
                    subprocess.run([sys.executable, "-m", "pip", "install", lib, "--upgrade"], capture_output=True)

                self.log_yaz("   -> Kontrol: PyTorch (CUDA)")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "torch", "torchvision", "torchaudio", 
                    "--index-url", "https://download.pytorch.org/whl/cu121", 
                    "--upgrade"
                ], capture_output=True)
                self.log_yaz(">>> Kurulum bitti.")

            # 2. MODEL HAZIRLIĞI
            gorunen_isim = self.secilen_model_gorunum.get()
            model_key = self.model_display_map[gorunen_isim]
            hedef_model_yolu = PATHS[model_key]
            
            if not os.path.exists(hedef_model_yolu):
                self.log_yaz(f"\nİNDİRİLİYOR: {hedef_model_yolu}")
                self.islem_durumu.set("Model İndiriliyor...")
                
                if "faster" in model_key:
                    from faster_whisper import download_model
                    repo_id = "deepdml/faster-whisper-large-v3-turbo-ct2" if "turbo" in model_key else "deepdml/faster-whisper-large-v3-ct2"
                    download_model(repo_id, output_dir=hedef_model_yolu)
                    self.log_yaz("İndirme tamamlandı!")
                    self.root.after(0, self.modelleri_tara_ve_guncelle)
                else:
                    self.log_yaz("Standart model önbelleğe indirilecek...")

            # 3. TRANSKRİPT
            hedef_dil_kodu = LANGUAGE_OPTIONS[self.secilen_dil_adi.get()]
            dosya = self.secilen_dosya.get()
            cikti = self.cikti_konumu.get()
            vad_aktif = self.anti_loop_modu.get()
            zaman_damgasi_aktif = self.zaman_damgasi_var.get() # YENİ

            self.log_yaz(f"Dosya: {os.path.basename(dosya)}")
            self.log_yaz(f"Model: {model_key}")
            self.log_yaz(f"Zaman Damgası: {'AÇIK' if zaman_damgasi_aktif else 'KAPALI'}")
            
            baslangic = time.time()

            # --- FASTER WHISPER BLOĞU ---
            if "faster" in model_key:
                from faster_whisper import WhisperModel
                self.islem_durumu.set("Model Yükleniyor...")
                model = WhisperModel(hedef_model_yolu, device="cuda", compute_type="int8", local_files_only=True)
                
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

                segments, info = model.transcribe(dosya, **transcribe_args)
                self.log_yaz(f"Dil: {info.language.upper()}")
                
                with open(cikti, "w", encoding="utf-8") as f:
                    for segment in segments:
                        if self.iptal_istendi:
                            self.log_yaz("\n!!! DURDURULDU !!!")
                            break
                        
                        if info.duration > 0:
                            yuzde = (segment.end / info.duration) * 100
                            self.progress_guncelle(yuzde)
                        
                        text = segment.text.strip()
                        
                        # ZAMAN DAMGASI KONTROLÜ
                        if zaman_damgasi_aktif:
                            zaman = f"[{int(segment.start//60):02}:{int(segment.start%60):02}]"
                            satir = f"{zaman} {text}"
                        else:
                            satir = text
                        
                        f.write(satir + "\n")
                        self.root.after(0, self.log_yaz, satir)

            # --- STANDART WHISPER BLOĞU ---
            else:
                import whisper
                self.islem_durumu.set("Model Yükleniyor...")
                
                # Standart model ismi (path yoksa ismi kullan)
                load_arg = hedef_model_yolu if os.path.exists(hedef_model_yolu) else model_key.replace("std_","").replace("large","large-v3")
                model = whisper.load_model(load_arg, device="cuda")
                self.islem_durumu.set("Çıkarılıyor...")
                
                yakalayici = TqdmYakalayici(self.progress_guncelle)
                sys.stderr = yakalayici
                try:
                    result = model.transcribe(
                        dosya, 
                        language=hedef_dil_kodu, 
                        verbose=False, 
                        condition_on_previous_text=not vad_aktif, 
                        no_speech_threshold=0.6
                    )
                    
                    if not self.iptal_istendi:
                        with open(cikti, "w", encoding="utf-8") as f:
                            # ZAMAN DAMGASI KONTROLÜ (STANDART MODEL İÇİN)
                            if zaman_damgasi_aktif:
                                # Standart modelde zaman damgası için 'segments' içinde dönmeliyiz
                                for segment in result["segments"]:
                                    start = segment["start"]
                                    text = segment["text"].strip()
                                    zaman = f"[{int(start//60):02}:{int(start%60):02}]"
                                    f.write(f"{zaman} {text}\n")
                            else:
                                # Sadece metin isteniyorsa raw text yeterli
                                f.write(result["text"])
                                
                        self.log_yaz("Dosya kaydedildi.")
                finally:
                    sys.stderr = original_stderr

            self.progress.stop()
            self.btn_baslat.config(state="normal")
            self.btn_iptal.config(state="disabled")
            
            if self.iptal_istendi:
                self.islem_durumu.set("Durduruldu.")
                messagebox.showinfo("Bilgi", f"Kısmi kayıt:\n{cikti}")
            else:
                self.islem_durumu.set("Tamamlandı.")
                self.progress['value'] = 100
                messagebox.showinfo("Başarılı", "İşlem tamamlandı.")

        except Exception as e:
            sys.stderr = original_stderr
            self.islem_durumu.set("Hata!")
            self.log_yaz(f"\nHATA: {str(e)}")
            self.btn_baslat.config(state="normal")
            self.btn_iptal.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = WhisperApp(root)
    root.mainloop()
