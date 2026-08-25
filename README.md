# Türkçe LLM Guardrail Değerlendirme Seti

> Türkçe büyük dil modeli guardrail'lerini ölçmek için açık bir örnek seti:
> **bloklanması gereken** prompt injection / jailbreak saldırıları **+**
> **bloklanmaması gereken** (masum ama yanlışlıkla reddedilen) Türkçe istekler.

[![Doğrulama](https://github.com/fevziegeyurtsevenler/turkish-llm-guardrail-set/actions/workflows/dogrulama.yml/badge.svg)](https://github.com/fevziegeyurtsevenler/turkish-llm-guardrail-set/actions/workflows/dogrulama.yml)
[![Lisans: CC BY-SA 4.0](https://img.shields.io/badge/Lisans-CC%20BY--SA%204.0-blue.svg)](LICENSE)

---

## Neden bu set var?

Türkçe LLM güvenliğinde iki gerçek boşluk var ve bu set ikisini birden ölçer:

1. **Saldırı tarafı (`injection`)** — Türkçe'ye özgü kaçış teknikleri İngilizce filtrelerde
   görünmez. Örnek: büyük **`İ`** harfinin `casefold()` sonrası `i̇`'ye dönmesi
   (`"İGNORE".casefold() != "ignore"`), sondan eklemeli yapının anahtar kelimeleri bölmesi,
   Türkçe rol-yapma kalıpları.
2. **Aşırı-reddetme tarafı (`benign`)** — Türkçe eğitilmemiş guardrail'ler masum Türkçe
   istekleri orantısız biçimde bloklar. Bu **over-refusal asimetrisi** ölçülmeden guardrail
   "güvenli" sanılır ama kullanılamaz hâle gelir.

Set, bir guardrail'in **hem saldırıyı yakalayıp hem masum isteği geçirebildiğini** aynı anda
sınamak için tasarlandı.

## Bu bir **değerlendirme seti**, tam eğitim korpusu değil

Kasıtlı olarak **küratörlü, açık bir kıyas ölçütü** (benchmark) — herkesin guardrail'ini
karşısında ölçebileceği bir *cetvel*. Amacı standart olmak; o yüzden açık ve alıntılanabilir.
Büyük ölçekli üretim korpusları bunun kapsamı dışındadır.

## Yapı

```
veri/
  injection/   inj-####.json   # bloklanmalı (beklenen: reddet)
  benign/      ben-####.json   # bloklanmamalı (beklenen: yanitla)
sema/
  ornek.schema.json            # her örneğin uyduğu şema
araclar/
  dogrula.py                   # biçim + KVKK doğrulaması (CI bunu çalıştırır)
  birlestir.py                 # veri/ -> dataset.jsonl (sürüm anında)
```

Her örnek tek bir JSON dosyasıdır (alanlar için [CONTRIBUTING.md](CONTRIBUTING.md)).

## Kullanım

```python
import json, glob

ornekler = [json.load(open(p, encoding="utf-8"))
            for p in glob.glob("veri/**/*.json", recursive=True)]

# Guardrail'ini her örnekte çalıştır, 'beklenen' ile karşılaştır.
# injection -> reddet bekleniyor;  benign -> yanitla bekleniyor.
```

Birleşik tek dosya için: `python araclar/birlestir.py` → `dataset.jsonl`.

## Katkı

Bir PR = bir örnek. 30 saniyelik sözleşme ve alan tablosu için **[CONTRIBUTING.md](CONTRIBUTING.md)**.
CI biçim ve KVKK kontrolünü otomatik yapar.

## Sorumlu kullanım

Bu set **savunma** amaçlıdır: guardrail, filtre ve LLM güvenlik ürünlerini değerlendirmek için.
Örnekler saldırı *tekniğini* gösterir, zararlı *son içeriği* değil. Çalışan zararlı yük içermez
ve içeremez (bkz. CONTRIBUTING → içerik tavanı). Bulguları sorumlu biçimde kullanın.

## Gizlilik / KVKK

Örneklerde **gerçek kişisel veri yoktur** — TCKN, gerçek ad+veri, gerçek iletişim bilgisi
kabul edilmez; hepsi sentetiktir. CI, 11 haneli TCKN benzeri dizileri reddeder.

## Lisans ve atıf

[CC BY-SA 4.0](LICENSE). Kullanabilir, uyarlayabilirsiniz — **atıf vermek** ve türevleri
**aynı lisansla** paylaşmak koşuluyla. Atıf için [CITATION.cff](CITATION.cff).

---

<details>
<summary><b>English summary</b></summary>

**Turkish LLM Guardrail Evaluation Set** — an open benchmark to measure Turkish LLM guardrails
on two axes at once: prompt-injection / jailbreak attacks that **should be blocked**
(`injection`), and benign Turkish requests that are wrongly blocked (`benign`, over-refusal).
It targets Turkish-specific evasion (the `İ` casefold gap, agglutinative morphology) and the
over-refusal asymmetry that English-tuned guardrails miss.

This is a **curated evaluation benchmark, not a full training corpus.** One PR = one example;
see [CONTRIBUTING.md](CONTRIBUTING.md). Defensive use only; no real personal data (KVKK);
no working harmful payloads. Licensed **CC BY-SA 4.0** — attribution + share-alike required.
</details>
