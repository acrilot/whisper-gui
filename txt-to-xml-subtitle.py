import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def convert_text_to_xml(input_text):
    # XML Başlık Kısmı
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

    # Zamanlama ve XML oluşturma döngüsü
    for i in range(len(parsed_lines)):
        current_line = parsed_lines[i]
        start_sec = current_line['time']
        
        # Bitiş süresi hesaplama (bir sonraki satırın başı veya +3 sn)
        if i < len(parsed_lines) - 1:
            end_sec = parsed_lines[i+1]['time']
        else:
            end_sec = start_sec + 3.0 

        # Saniyeyi HH:MM:SS.mmm formatına çevir
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02}:{m:02}:{s:02}.{ms:03}"

        # Özel karakter temizliği
        safe_text = current_line['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        p_tag = f'      <p begin="{format_time(start_sec)}" end="{format_time(end_sec)}">{safe_text}</p>'
        xml_output.append(p_tag)

    # Kapanış
    xml_output.append('    </div>')
    xml_output.append('  </body>')
    xml_output.append('</tt>')

    return "\n".join(xml_output)

def main():
    # Ana pencereyi gizle (Sadece dosya seçici görünsün diye)
    root = tk.Tk()
    root.withdraw()

    # 1. ADIM: Girdi Dosyasını Seç
    file_path = filedialog.askopenfilename(
        title="Dönüştürülecek Metin Dosyasını Seç",
        filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
    )

    if not file_path:
        print("Dosya seçilmedi, işlem iptal.")
        return

    try:
        # Dosyayı Oku (UTF-8 desteği ile)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Dönüştürme işlemini yap
        xml_content = convert_text_to_xml(content)

        # 2. ADIM: Kaydedilecek Yeri Seç
        # Varsayılan dosya ismini input ismiyle aynı yap ama uzantıyı xml yap
        base_name = os.path.splitext(file_path)[0]
        save_path = filedialog.asksaveasfilename(
            title="XML Dosyasını Kaydet",
            initialfile=f"{base_name}.xml",
            defaultextension=".xml",
            filetypes=[("XML Dosyaları", "*.xml")]
        )

        if save_path:
            # Dosyayı Yaz
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            # Başarılı mesajı göster
            messagebox.showinfo("Başarılı", f"Dosya başarıyla dönüştürüldü:\n{save_path}")
        else:
            print("Kaydetme işlemi iptal edildi.")

    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    main()
