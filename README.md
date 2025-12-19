# 📡 OTDR Analysis Tool

**OTDR Analysis Tool**, `.sor` (OTDR trace) dosyalarını analiz etmek, olayları CSV olarak çıkarmak ve fiber izlerini görselleştirmek için geliştirilmiş bir Python aracıdır.

---

## 🚀 Özellikler

- 📂 `.sor` dosyalarını okuma ve analiz etme  
- 📊 OTDR trace grafiği oluşturma  
- 📑 Event listesini CSV olarak dışa aktarma  
- 📏 Tek yönlü (oneway) ve çift yönlü (twoway) mesafe hesaplama  
- 🖼️ PNG formatında görsel çıktı alma  

---

## 🧰 Gereksinimler

Python 3.8+ önerilir.

Gerekli kütüphaneleri yüklemek için:

```bash
pip install otdrparser
pip install matplotlib
```

## ⚙️ Kullanım
1️⃣ OTDR Trace + Event CSV + Grafik
python sor_analiz.py 1.sor --csv 1_events.csv --plot 1_trace.png

##  📈 Örnek çıktı:
<img width="960" height="720" alt="1_trace" src="https://github.com/user-attachments/assets/5553ca1e-024b-4e93-9821-891dd4825b63" />

---

2️⃣ Tek Yönlü Mesafe (One-way)
python sor_analiz.py 1.sor --distance oneway

<img width="994" height="268" alt="image" src="https://github.com/user-attachments/assets/95b24c6b-803f-4cb7-a34e-311edacca976" />

📏 Çıktı:

---

##  3️⃣ Çift Yönlü Mesafe (Two-way)
python sor_analiz.py 1.sor --distance twoway

<img width="978" height="258" alt="image" src="https://github.com/user-attachments/assets/d1989c80-74ac-4471-bfcb-7c112d467fea" />

📏 Çıktı:

---

##  📂 Çıktı Dosyaları
Dosya	Açıklama
*.csv	OTDR event listesi
*.png	OTDR trace grafiği
🧠 Kullanım Alanları

Fiber optik hat analizleri

Telekom altyapı testleri

Arıza tespiti ve mesafe ölçümü

OTDR veri inceleme ve raporlama

_____________________________________________________________


https://youtu.be/p_F_u3HpFXM

https://youtube.com/watch?v=0IGN_3g3UDw

## 💰 You can help me by Donating

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/handeveloper1)

## 📺 Check out my YouTube Channel

[![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@handeveloper1)


