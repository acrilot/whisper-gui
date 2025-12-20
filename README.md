# Whisper GUI - Transkript Çıkarma Aracı
Bu proje, OpenAI'nin Whisper modellerini kullanarak ses ve video dosyalarını metne dönüştüren (transkript çıkaran) kullanıcı dostu bir masaüstü uygulamasıdır. Faster-Whisper ve standart Whisper kütüphanelerini destekler, NVIDIA CUDA hızlandırması ile kısa sürede ve çevrimdışı olarak çeviri yapar ve çıktıları TXT, PDF veya DOCX formatında kaydeder.

<img width="1920" height="1001" alt="GUI_v8" src="https://github.com/user-attachments/assets/1b942cc6-6ccc-42bd-85b8-46b32d243c36" />

> [!WARNING]
> ### ⚠️ DİKKAT: YÜKSEK VERİ KULLANIMI VE GPU GEREKSİNİMİ
>  * Veri Kullanımı: Bu uygulama ilk kurulumda PyTorch (CUDA destekli) ve Yapay Zeka modellerini indireceği için 4GB - 8GB arasında internet verisi kullanabilir. Lütfen kurulumu kotasız bir internet bağlantısında yapınız.
>  * Donanım: Bu sürüm NVIDIA Ekran Kartı (GPU) gerektirir. Sadece işlemci (CPU) ile çalıştırılması önerilmez ve kod yapısı gereği CUDA çekirdeklerini arar.

## Özellikler
 * Çoklu Format Desteği: Çıktılarınızı .txt, .pdf, .docx (Word) veya .xml (Altyazı) olarak alabilirsiniz.
 * Gelişmiş Modeller:
   * Faster-Whisper: Optimize edilmiş, çok daha hızlı ve bellek dostu.
   * Standart Whisper: Orijinal OpenAI modelleri.
 * Otomatik Kurulum Modu: Python kütüphanelerini ve gereksinimleri tek tıkla kurar.
 * FFmpeg Yönetimi: Sistemde FFmpeg yoksa otomatik algılar ve indirir.
 * Anti-Loop (VAD) Filtresi: Sessiz anlarda yapay zekanın takılmasını (halüsinasyon görmesini) engeller.
 * Zaman Damgası: İsteğe bağlı olarak her cümlenin başına [00:15] formatında süre ekler.
 * Tek Blok Metin: Çıktıyı tek bir paragraf halinde verir.
 * Kullanıcı Dostu Arayüz: Modern ve basit arayüz tasarımı.

## Ön Gereksinimler (Kurulumdan Önce)
Uygulamanın çalışması için bilgisayarınızda Python yüklü olmalıdır.
1. Python Kurulumu (Önemli!)
Bu projenin en stabil çalıştığı sürüm Python 3.11.x serisidir.
 * İndirme: Python 3.11.9 [İndirme Sayfası](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) adresine gidin.
 * Windows Installer (64-bit) seçeneğini indirin.
 * ⚠️ KRİTİK ADIM: Kurulum ekranı açıldığında en alttaki "Add python.exe to PATH" kutucuğunu MUTLAKA İŞARETLEYİN. Bu işaretlenmezse program çalışmaz.
 * "Install Now" diyerek kurulumu tamamlayın.
2. Sürücü Güncellemesi
NVIDIA ekran kartınızın sürücülerinin güncel olduğundan emin olun.

## Kurulum ve İlk Çalıştırma
Projeyi bilgisayarınıza indirdikten sonra (ZIP olarak veya git clone ile), aşağıdaki adımları izleyin:
Adım 1: Uygulamayı Başlatın
Klasör içindeki whisper-gui.py dosyasına çift tıklayın.
Adım 2: Kütüphanelerin Kurulumu
Uygulama ilk açıldığında gerekli yapay zeka kütüphaneleri (PyTorch, Whisper vb.) henüz yüklü değildir.
 * Arayüzdeki "Ayarlar" bölümünde bulunan "🔧 İlk Kullanım (Kurulum)" kutucuğunu işaretleyin.
 * Herhangi bir ses dosyası seçmenize gerek yoktur (veya rastgele bir dosya seçebilirsiniz).
 * "▶ BAŞLAT" butonuna basın.
 * Log Ekranını Takip Edin: Alt kısımdaki siyah ekranda "Kontrol: openai-whisper", "Kontrol: PyTorch" gibi yazılar göreceksiniz. Bu işlem internet hızınıza bağlı olarak 10-30 dakika sürebilir.
 * Log ekranında ">>> Kurulum bitti." yazısını gördüğünüzde programı kapatıp tekrar açabilirsiniz.
> Not: Eğer sisteminizde FFmpeg eksikse, program açılışta size soracak ve onaylarsanız otomatik olarak indirip kuracaktır.

## Kullanım Kılavuzu
Kurulum tamamlandıktan sonra transkript almak çok basittir:
 * Dosya Seçimi:
   * Kaynak Dosya: "Dosya Seç" butonuna basarak ses veya video dosyanızı seçin.
   * Çıktı Formatı: Listeden TXT, DOCX veya PDF formatını seçin.
 * Model Ayarları:
   * Model: İhtiyacınıza uygun modeli seçin (Aşağıdaki tabloya bakınız).
   * Dil: "Otomatik Algıla" genelde en iyi sonucu verir, ancak dil belliyse (örneğin Türkçe) listeden seçmek işlemi hafifçe hızlandırabilir.
 * Seçenekler:
   * Anti-Loop (VAD): (Önerilen: Açık) Video/ses dosyasındaki sessiz kısımları atlar. Bu, yapay zekanın sessizlikte kendi kendine yazı uydurmasını engeller.
   * Zaman Damgası: Çıktı dosyasına konuşma sürelerini ekler.
 * Başlat:
   * Butona basın ve arkanıza yaslanın. İlerleme çubuğu ve log ekranı size durumu bildirecektir.
   * İşlem bitince dosya, kaynak dosyanızın olduğu klasöre kaydedilir.

### Model Performans Tablosu
Hangi modeli seçmelisiniz? İşte karşılaştırma tablosu:
| Model Adı | Hız | Doğruluk (Kalite) | VRAM Kullanımı | Kullanım Alanı |
|---|---|---|---|---|
| Faster Whisper - Turbo | 🚀 Çok Hızlı | ⭐⭐⭐ İyi | Düşük (~2GB) | Uzun toplantılar, hızlı sonuç gereken durumlar. |
| Faster Whisper - Large V3 | ⚡ Hızlı | ⭐⭐⭐⭐⭐ Mükemmel | Orta (~4GB) | Önerilen. Yüksek doğruluk ve makul hız. |
| Standart Whisper - Medium | 🐢 Yavaş | ⭐⭐⭐ Orta | Düşük | Daha eski donanımlar için alternatif. |
| Standart Whisper - Large V3 | 🐌 Çok Yavaş | ⭐⭐⭐⭐⭐ Mükemmel | Yüksek (~6-8GB) | En yüksek akademik doğruluk gerektiren işler. |
 * Öneri: Günlük kullanım için Faster Whisper - Large V3 veya Turbo modelleri en iyi performansı sunar.

### Sıkça Sorulan Sorular (SSS)
S: PDF çıktısında Türkçe karakterler bozuk görünüyor mu?

C: Hayır. Uygulama, PDF oluştururken Windows sisteminizdeki "Arial" fontunu kullanacak şekilde ayarlanmıştır. Türkçe karakterler (ğ, ş, ı, ö, ç) sorunsuz görüntülenir.


S: Program "Yanıt Vermiyor" diyor ve donuyor.

C: Büyük dosyalar indirilirken veya işlenirken arayüz bazen tepki vermeyebilir, ancak arka planda çalışmaya devam eder. Log ekranını takip edin.


S: "GPU Bulunamadı" hatası alıyorum.

C: Bilgisayarınızda NVIDIA ekran kartı olduğundan ve CUDA desteklediğinden emin olun. Ayrıca sürücülerinizin güncel olması gerekir.


S: Kurulum sırasında hata aldım (Non-zero exit).

C: Genellikle internet bağlantısı kopukluğundan kaynaklanır. İnternetinizi kontrol edin ve "İlk Kullanım" modunda tekrar başlatın.

### Lisans
Bu proje açık kaynaklıdır ve eğitim/kişisel kullanım amaçlı geliştirilmiştir. OpenAI Whisper ve Faster-Whisper lisanslarına tabidir.
