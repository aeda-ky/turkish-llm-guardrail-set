#!/usr/bin/env python3
"""veri/ altındaki tekil örnekleri tek bir dataset.jsonl dosyasında birleştirir.

Küratör sürüm/yayın anında çalıştırır. Üretilen dataset.jsonl commit EDİLMEZ
(bkz. .gitignore) — kaynağın tek doğruluğu veri/ klasörüdür, PR'lar burada çakışmaz.
"""
import json
from collections import Counter
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "veri"
CIKTI = KOK / "dataset.jsonl"


def main():
    kayitlar = []
    for yol in sorted(VERI.rglob("*.json")):
        kayitlar.append(json.loads(yol.read_text(encoding="utf-8")))
    kayitlar.sort(key=lambda k: k.get("id", ""))

    with CIKTI.open("w", encoding="utf-8") as f:
        for k in kayitlar:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")

    et = Counter(k.get("etiket") for k in kayitlar)
    kat = Counter(k.get("kategori") for k in kayitlar)
    print(f"{len(kayitlar)} örnek -> {CIKTI.relative_to(KOK)}")
    print(f"  etiket: {dict(et)}")
    print("  kategori:")
    for k, n in sorted(kat.items(), key=lambda x: -x[1]):
        print(f"    {n:3d}  {k}")


if __name__ == "__main__":
    main()
