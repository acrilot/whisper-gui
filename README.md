# Whisper GUI - Transkript Çıkarma Aracı

Bu proje, OpenAI'nin Whisper modellerini kullanarak ses ve video dosyalarını metne dönüştüren kullanıcı dostu bir masaüstü uygulamasıdır. Faster-Whisper ve standart Whisper kütüphanelerini destekler, NVIDIA CUDA hızlandırması ile çevrimdışı çalışır ve çıktıları TXT, PDF, DOCX veya XML formatında kaydeder.

<img width="1920" height="1001" alt="GUI_v8" src="https://github.com/user-attachments/assets/75b35a5b-e417-4d71-b5fe-2a48d429df5f" />

> [!WARNING]
> ### DIKKAT: YÜKSEK VERİ KULLANIMI VE GPU GEREKSİNİMİ
> * **Veri Kullanımı:** Bu uygulama ilk kurulumda PyTorch (CUDA destekli) ve yapay zeka modellerini indireceği için 4 GB ile 8 GB arasında internet verisi kullanabilir. Kurulumu kotasız bir bağlantıda yapmanız önerilir.
> * **Donanım:** Bu sürüm NVIDIA ekran kartı (GPU) gerektirir. Yalnızca işlemci (CPU) ile çalıştırılması desteklenmez.

---

## Özellikler

* **Toplu Dosya İşleme:** Birden fazla ses veya video dosyasını aynı anda seçerek hepsini sırayla işleyebilirsiniz.
* **Çoklu Format Desteği:** Çıktılarınızı `.txt`, `.pdf`, `.docx` (Word) veya `.xml` (altyazı) formatında alabilirsiniz.
* **Gelişmiş Modeller:**
  * Faster-Whisper: Optimize edilmiş, bellek dostu ve hızlı model. Compute tipi ve işlem esnasında durdurma özelliklerini destekler.
  * Standart Whisper: Orijinal OpenAI modelleri. Compute tipi seçimi devre dışıdır ve çalışma esnasında durdurulamaz.
* **İngilizce'ye Çeviri:** Herhangi bir dildeki kaydı doğrudan İngilizce metne dönüştürebilirsiniz.
* **Compute Tipi Seçimi:** `int8`, `float16`, `int8_float16` ve `float32` arasından seçim yaparak hız ile doğruluk dengesini kendiniz ayarlayabilirsiniz (yalnızca Faster-Whisper).
* **Beam Size Ayarı:** Transkripsiyon kalitesini ince ayarla kontrol etmek için beam boyutunu 1 ile 10 arasında belirleyebilirsiniz.
* **Model Önbelleği:** Yüklenen model, oturum boyunca bellekte tutulur. Aynı modelle ardışık işlemler yapıldığında model yeniden yüklenmez.
* **Durdur ve Kaydet:** Faster-Whisper ile işlem yaparken dilediğiniz an işlemi durdurabilir ve o ana kadar transkript edilmiş içeriği kaydedebilirsiniz.
* **Anti-Loop (VAD) Filtresi:** Sessiz anlarda yapay zekanın kendi kendine metin üretmesini (halüsinasyon) engeller.
* **Zaman Damgası:** Her cümlenin başına `[00:15]` formatında süre etiketi ekler.
* **Tek Blok Metin:** Çıktıyı tek bir paragraf olarak verir.
* **Otomatik Kurulum Modu:** Gerekli Python kütüphanelerini tek tıkla kurar.
* **FFmpeg Yönetimi:** Sistemde FFmpeg yoksa otomatik olarak algılar ve kurmasını teklif eder.

---

## Ön Gereksinimler

### 1. Python Kurulumu

Bu projenin en kararlı çalıştığı sürüm **Python 3.11.x** serisidir.

* [Python 3.11.9 İndirme Sayfası](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) adresinden 64-bit Windows yükleyicisini indirin.
* Kurulum ekranında en alttaki **"Add python.exe to PATH"** kutucuğunu mutlaka işaretleyin. Bu adım atlanırsa program çalışmaz.
* "Install Now" seçeneği ile kurulumu tamamlayın.

### 2. NVIDIA Sürücü Güncellemesi

NVIDIA ekran kartınızın sürücülerinin güncel olduğundan emin olun. Güncel sürücüler [NVIDIA resmi sitesinden](https://www.nvidia.com/drivers) edinilebilir.

---

## Kurulum ve İlk Çalıştırma

### Adım 1: Uygulamayı Başlatın

Klasör içindeki `whisper_gui.pyw` dosyasına çift tıklayın. `.pyw` uzantısı, uygulamanın arka planda konsol penceresi açmadan çalışmasını sağlar.

> **Not:** Sisteminizde FFmpeg eksikse, uygulama açılışta sizi bilgilendirecek ve onayınız halinde otomatik olarak indirip kuracaktır.

### Adım 2: Kütüphanelerin Kurulumu

Uygulama ilk açıldığında gerekli yapay zeka kütüphaneleri henüz yüklü değildir.

1. Ayarlar bölümündeki **"Kurulum Modu"** kutucuğunu işaretleyin.
2. Kaynak dosya seçmeniz gerekmez; herhangi bir dosya seçebilir ya da bu adımı atlayabilirsiniz.
3. **"BAŞLAT"** butonuna basın.
4. Sağdaki log ekranında `Kontrol: openai-whisper`, `Kontrol: PyTorch` gibi bildirimler görünecektir. Bu işlem internet hızınıza bağlı olarak 10-30 dakika sürebilir.
5. Log ekranında `>>> Kurulum bitti.` mesajını gördükten sonra programı kapatıp yeniden açın.

---

## Kullanım Kılavuzu

### Dosya Seçimi

* **Kaynak Dosya(lar):** "Dosya Seç" butonuna tıklayarak bir veya birden fazla ses/video dosyası seçin. Birden fazla dosya seçildiğinde toplu işlem modu devreye girer ve çıktılar otomatik olarak kaynak dosyaların bulunduğu klasöre kaydedilir.
* **Çıktı Formatı:** TXT, DOCX, PDF veya XML formatını seçin.
* **Çıktı Yolu:** Tek dosya modunda çıktı yolu düzenlenebilir ve "Değiştir" butonu ile farklı bir konum belirlenebilir.

### Model Ayarları

* **Model:** İhtiyacınıza uygun modeli seçin (aşağıdaki tabloya bakınız). Model listesinde yanında `✓` simgesi olanlar bilgisayarınızda zaten indirilidir; `⬇` simgesi olanlar ise ilk kullanımda indirilecektir.
* **Dil:** "Otomatik Algıla" seçeneği çoğu durumda en iyi sonucu verir. Konuşma dili belliyse listeden seçmek işlemi hafifçe hızlandırabilir.
* **Compute Tipi:** Yalnızca Faster-Whisper modelleri için geçerlidir. Hız-doğruluk dengesini belirler (bkz. Parametreler).
* **Beam:** Transkripsiyon kalitesini etkiler. Varsayılan değer olan `5` çoğu iş için uygundur.

### Seçenekler

* **Anti-Loop (VAD):** (Önerilen: Açık) Sessiz kısımları filtreler ve yapay zekanın bu anlarda metin üretmesini engeller.
* **Tek Blok Metin:** Çıktıyı paragraf sonu olmaksızın tek bir blok halinde verir. Zaman Damgası ile birlikte kullanılamaz.
* **Zaman Damgası:** Her konuşma segmentinin başına süre etiketi ekler. Tek Blok Metin ile birlikte kullanılamaz. XML formatı seçildiğinde otomatik olarak etkinleşir.
* **İngilizce'ye Çevir:** Model, transkripsiyon yerine çeviri modunda çalışır ve çıktıyı doğrudan İngilizce olarak üretir.
* **Kurulum Modu:** Eksik Python kütüphanelerini tespit edip kurar. Yalnızca ilk kurulum için kullanılır.

### Başlatma ve Durdurma

* **BAŞLAT** butonuna basın ve log ekranından ilerlemeyi takip edin. İşlem tamamlandığında dosya(lar) belirlenen konuma kaydedilir.
* **DURDUR & KAYDET** butonu yalnızca Faster-Whisper modelleri kullanılırken etkindir. Butona basıldığında işlem durdurulur ve o ana kadar tamamlanan içerik dosyaya yazılır.

---

## Model Performans Tablosu

| Model | Hız | Doğruluk | Tahmini VRAM | Önerilen Kullanım |
|---|---|---|---|---|
| Faster Whisper - Large V3 | Hızlı | Mükemmel | ~4 GB | Önerilen. Yüksek doğruluk ve makul hız. |
| Faster Whisper - Turbo | Çok Hızlı | İyi | ~2 GB | Uzun kayıtlar ve hızlı sonuç gerektiren durumlar. |
| Standart Whisper - Large V3 | Çok Yavaş | Mükemmel | ~6-8 GB | En yüksek akademik doğruluk gerektiren işler. |
| Standart Whisper - Turbo | Yavaş | İyi | ~4 GB | Standart model tercih edildiğinde daha hızlı alternatif. |
| Standart Whisper - Medium | Yavaş | Orta | ~2-3 GB | Eski veya sınırlı donanımlar için alternatif. |

Günlük kullanım için **Faster Whisper - Large V3** veya **Faster Whisper - Turbo** önerilir.

---

## Parametreler

### Compute Tipi (Yalnızca Faster-Whisper)

| Compute Tipi | Hız | Doğruluk | Bellek Kullanımı |
|---|---|---|---|
| `int8` | En hızlı | Yeterli | En düşük |
| `int8_float16` | Hızlı | İyi | Düşük |
| `float16` | Orta | Daha iyi | Orta |
| `float32` | En yavaş | En yüksek | En yüksek |

VRAM yetersizliği durumunda `int8` veya `int8_float16` tercih edilmesi önerilir.

### Beam Size

Beam değerinin artırılması daha fazla olasılığı değerlendirerek transkripsiyon doğruluğunu artırır, ancak işlem süresini de uzatır. Varsayılan değer olan `5`, doğruluk ve hız açısından çoğu iş için idealdir.

---

## Sıkça Sorulan Sorular

**S: PDF çıktısında Türkçe karakterler bozuk görünüyor mu?**

C: Hayır. Uygulama, PDF oluştururken sistemdeki "Arial" fontunu kullanır. Türkçe karakterler (ğ, ş, ı, ö, ü, ç) sorunsuz görüntülenir.

**S: Toplu işlem modunda çıktı dosyaları nereye kaydedilir?**

C: Toplu işlem modunda her çıktı dosyası, ilgili kaynak dosyasının bulunduğu klasöre kaydedilir. Çıktı ismi otomatik olarak `[kaynak_dosya_adı]_[model]_transkript.[uzantı]` biçiminde oluşturulur.

**S: Program "Yanıt Vermiyor" uyarısı veriyor.**

C: Büyük dosyalar işlenirken veya model indirilirken arayüz zaman zaman tepki vermeyebilir; ancak arka planda çalışmaya devam eder. Log ekranını takip edin.

**S: "GPU Bulunamadı" hatası alıyorum.**

C: Bilgisayarınızda NVIDIA ekran kartı olduğundan ve CUDA desteklediğinden emin olun. Sürücülerinizin güncel olması gerekir.

**S: Kurulum sırasında hata aldım.**

C: Genellikle internet bağlantısı kesintisinden kaynaklanır. Bağlantınızı kontrol edip "Kurulum Modu" ile işlemi yeniden başlatın.

---

## Desteklenen Dosya Formatları

Giriş olarak şu formatlar desteklenmektedir: `.mp3`, `.wav`, `.m4a`, `.mp4`, `.mkv`, `.flac`, `.ogg`, `.webm`, `.opus`

---

## Lisans

Bu proje açık kaynaklıdır ve eğitim/kişisel kullanım amacıyla geliştirilmiştir. [OpenAI Whisper](https://github.com/openai/whisper) ve [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) lisanslarına tabidir.
