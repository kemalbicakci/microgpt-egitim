# MicroGPT — Sıfırdan GPT Öğretimi

> *"The most atomic way to train and run inference for a GPT in pure, dependency-free Python."*
> — [@karpathy](https://github.com/karpathy)

Bu repo, Karpathy'nin `microgpt.py` dosyasını temel alarak sıfırdan bir GPT'nin nasıl çalıştığını görsel ve animasyonlarla öğretmek için hazırlanmıştır.

---

## İçindekiler

| Dosya | Açıklama |
|---|---|
| `microgpt_animated.py` | Animasyonlu öğretim versiyonu — eğitim sırasında GIF'ler üretir |
| `create_presentation_tr.py` | Türkçe PowerPoint sunumunu oluşturur |
| `create_presentation.py` | İngilizce PowerPoint sunumunu oluşturur |
| `draw_architecture.py` | Mimari diyagramını çizer (`architecture_tr.png`) |
| `insert_arch_slide.py` | Mimari slaytını PPTX'e ekler |
| `microgpt_aciklamali.pptx` | Türkçe sunum (21 slayt) |
| `microgpt_explained.pptx` | İngilizce sunum (20 slayt) |
| `input.txt` | ~32.000 İngilizce isim (eğitim verisi) |

---

## Üretilen Görseller

| Görsel | Ne Gösteriyor |
|---|---|
| `training_curves_animated.gif` | Kayıp ve öğrenme hızı adım adım |
| `attention_animated.gif` | Dikkat ısı haritasının eğitim boyunca değişimi |
| `weight_dist_animated.gif` | Ağırlık dağılımının gürültüden anlama dönüşümü |
| `embedding_pca_animated.gif` | Token gömmelerinin 2D PCA'da kümelenmesi |
| `generation_animated.gif` | Harf harf isim üretimi ve olasılık çubukları |
| `architecture_tr.png` | GPT mimarisinin tam diyagramı (Türkçe) |
| `hyperparams.png` | Hiperparametre tablosu |
| `initial_weights.png` / `final_weights.png` | Başlangıç ve son ağırlık matrisleri |

---

## Nasıl Çalıştırılır

### 1. Bağımlılıkları kur

```bash
pip install matplotlib python-pptx
```

### 2. Modeli eğit ve animasyonları üret

```bash
python microgpt_animated.py
```

`input.txt` yoksa otomatik indirilir. Eğitim ~1000 adım sürer, bitince 5 GIF ve birkaç PNG üretilir.

### 3. Sunumları oluştur

```bash
# Türkçe
python draw_architecture.py
python create_presentation_tr.py
python insert_arch_slide.py

# İngilizce
python create_presentation.py
```

---

## Modelin Öğrendikleri

```
num docs: 32033
vocab size: 27
num params: 7.237

step 1000 / 1000 | loss 1.8742

sample  1: emma
sample  2: avani
sample  3: lior
...
```

---

## Sununun İçeriği (Türkçe — 21 Slayt)

1. Başlık
2. Büyük Resim
3. Veri Seti & Tokenizer
4. Autograd (Otomatik Türev)
5. Hiperparametreler
6. Model Ağırlıkları
7. Transformer Mimarisi (metin)
8. **Genel Mimari Diyagramı**
9. Dikkat Mekanizması — Q, K, V
10. Dikkat Isı Haritası (animasyonlu)
11. Eğitim Döngüsü
12. Adam Optimizörü
13. Eğitim Eğrileri (animasyonlu)
14. Ağırlık Dağılımı (animasyonlu)
15. Başlangıç / Son Ağırlıklar
16. Gömme Uzayı PCA (animasyonlu)
17. Son Parametre Dağılımı
18. Çıkarım — İsim Üretme
19. Üretim Animasyonu
20. Temel Denklemler
21. Özet

---

## Temel Kavramlar

| Kavram | Kısa Açıklama |
|---|---|
| **Tokenizer** | Harfleri tam sayılara çevirir |
| **Embedding** | Her token için öğrenilmiş vektör |
| **Autograd** | Elle türev almadan gradyan hesabı |
| **Self-Attention** | Her token geçmiştekilere bakarak bilgi toplar |
| **Residual Connection** | Katmanları atlayan kısa yol — eğitimi kararlı kılar |
| **Adam** | Her ağırlık için ayrı adım boyutu ayarlayan optimizör |
| **Temperature** | Üretimde rastgelelik kontrolü |
| **Cross-Entropy Loss** | Modelin ne kadar şaşırdığının ölçüsü |

---

## Kaynak

- Orijinal kod: [karpathy/microgpt.py](https://gist.github.com/karpathy/b9ada699ceeeb10ee0f6cd2c43cc0494)
- İsim veri seti: [karpathy/makemore](https://github.com/karpathy/makemore)
