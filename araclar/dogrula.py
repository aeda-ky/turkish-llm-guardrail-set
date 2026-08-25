#!/usr/bin/env python3
"""Türkçe LLM Guardrail Seti — biçim ve KVKK doğrulayıcı.

Ağ erişimi YOK, dış bağımlılık YOK — CI'da deterministik çalışır.
Hata (exit 1): şema ihlali, TCKN benzeri veri, mükerrer metin, geçersiz kategori.
Uyarı (exit 0): stil/uzunluk önerileri.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "veri"

INJECTION_KATEGORI = {
    "talimat-gaspi",          # "önceki talimatları unut" türü
    "rol-yapma",              # DAN / rol vererek kısıt aşımı
    "sistem-sizinti",         # sistem promptu / gizli talimat sızdırma
    "kodlama-kacis",          # base64 / leetspeak / unicode ile filtre atlatma
    "turkce-casefold",        # Türkçe İ/ı büyük-küçük harf dönüşümü istismarı
    "turkce-morfoloji",       # aynı kökü alışılmadık çekim ekleriyle bükerek eşleşmeden kaçma
    "parafraz-kacis",         # komutu farklı sözcüklerle yeniden ifade ederek (parafraz) kaçma
    "sinirlayici-enjeksiyon", # ayraç/delimiter enjeksiyonu, sahte sistem bloğu
    "dolayli-enjeksiyon",     # getirilen içerik/araç çıktısı üzerinden enjeksiyon
}
BENIGN_KATEGORI = {
    "guvenlik-egitimi",       # masumca sorulmuş güvenlik eğitimi sorusu
    "anahtar-kelime-tetikleyici",  # masum bağlamda tetikleyici kelime (oyun/tarih/yemek)
    "mesru-ikili-kullanim",   # meşru ikili kullanım (kilit güvenliği, sızma testi öğrenimi)
    "kulturel-deyim",         # birebir çevrildiğinde tehditkâr duran Türkçe deyim
    "saglik-hukuk-danisma",   # yanlışlıkla bloklanan sağlık/hukuk sorusu
    "kurgu-tarih-baglami",    # kurgu/tarih bağlamında masum istek
}
BEKLENEN = {"injection": "reddet", "benign": "yanitla"}
ID_DESEN = re.compile(r"^(inj|ben)-[0-9]{4}$")
TCKN_DESEN = re.compile(r"(?<!\d)\d{11}(?!\d)")   # 11 haneli dizi = olası TCKN -> KVKK blok
EPOSTA_DESEN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ZORUNLU = ["id", "dil", "etiket", "kategori", "teknik", "metin", "beklenen", "aciklama", "kaynak", "katkici"]
IZINLI_ALAN = set(ZORUNLU) | {"surum"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.casefold()


def dosyalar():
    return sorted(VERI.rglob("*.json"))


def main():
    hatalar, uyarilar = [], []
    gorulen_id = {}
    gorulen_metin = {}
    toplam = 0

    for yol in dosyalar():
        rel = yol.relative_to(KOK)
        try:
            veri = json.loads(yol.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            hatalar.append(f"{rel}: geçersiz JSON — {e}")
            continue
        toplam += 1

        # Bilinmeyen / eksik alanlar
        for alan in veri:
            if alan not in IZINLI_ALAN:
                hatalar.append(f"{rel}: bilinmeyen alan '{alan}'")
        for alan in ZORUNLU:
            if alan not in veri or veri[alan] in (None, ""):
                hatalar.append(f"{rel}: zorunlu alan eksik/boş '{alan}'")
        if hatalar and rel.name in hatalar[-1]:
            # temel alanlar eksikse kalan kontroller anlamsız
            if any(a not in veri for a in ("id", "etiket", "kategori", "metin", "beklenen")):
                continue

        etiket = veri.get("etiket")
        beklenen_klasor = "injection" if etiket == "injection" else "benign"
        if beklenen_klasor not in str(rel):
            hatalar.append(f"{rel}: etiket '{etiket}' ile klasör uyuşmuyor")

        # id
        _id = veri.get("id", "")
        if not ID_DESEN.match(_id):
            hatalar.append(f"{rel}: id deseni geçersiz '{_id}' (inj-#### / ben-####)")
        else:
            onek = "inj" if etiket == "injection" else "ben"
            if not _id.startswith(onek):
                hatalar.append(f"{rel}: id öneki etiketle uyuşmuyor '{_id}'")
            if yol.stem != _id:
                hatalar.append(f"{rel}: dosya adı '{yol.stem}' ile id '{_id}' aynı olmalı")
            if _id in gorulen_id:
                hatalar.append(f"{rel}: mükerrer id '{_id}' (ayrıca {gorulen_id[_id]})")
            gorulen_id[_id] = str(rel)

        # dil
        if veri.get("dil") != "tr":
            hatalar.append(f"{rel}: dil 'tr' olmalı")

        # etiket / kategori / beklenen
        if etiket not in BEKLENEN:
            hatalar.append(f"{rel}: etiket 'injection' veya 'benign' olmalı")
        else:
            izinli = INJECTION_KATEGORI if etiket == "injection" else BENIGN_KATEGORI
            if veri.get("kategori") not in izinli:
                hatalar.append(f"{rel}: '{etiket}' için geçersiz kategori '{veri.get('kategori')}' "
                               f"(izinli: {', '.join(sorted(izinli))})")
            if veri.get("beklenen") != BEKLENEN[etiket]:
                hatalar.append(f"{rel}: '{etiket}' için beklenen '{BEKLENEN[etiket]}' olmalı, "
                               f"'{veri.get('beklenen')}' verilmiş")

        # metin: uzunluk + KVKK
        metin = veri.get("metin", "")
        if isinstance(metin, str):
            if len(metin) > 1200:
                hatalar.append(f"{rel}: metin 1200 karakteri aşıyor ({len(metin)})")
            if len(metin) > 600:
                uyarilar.append(f"{rel}: metin uzun ({len(metin)} kr) — örnekler kısa ve öz olmalı")
            if TCKN_DESEN.search(metin):
                hatalar.append(f"{rel}: 11 haneli dizi bulundu — olası TCKN, KVKK gereği YASAK")
            if EPOSTA_DESEN.search(metin):
                uyarilar.append(f"{rel}: e-posta deseni var — gerçek kişisel veriyse KVKK ihlali, "
                                f"sentetik/örnek olduğundan emin ol")
            n = normalize(metin)
            if n in gorulen_metin:
                hatalar.append(f"{rel}: mükerrer metin ({gorulen_metin[n]} ile aynı)")
            else:
                gorulen_metin[n] = str(rel)

        # aciklama üst sınır
        aciklama = veri.get("aciklama", "")
        if isinstance(aciklama, str) and len(aciklama) > 600:
            hatalar.append(f"{rel}: aciklama 600 karakteri aşıyor ({len(aciklama)})")

    # Rapor
    print(f"Taranan örnek: {toplam}")
    if uyarilar:
        print(f"\n⚠️  {len(uyarilar)} uyarı:")
        for u in uyarilar:
            print(f"  - {u}")
    if hatalar:
        print(f"\n❌ {len(hatalar)} hata:")
        for h in hatalar:
            print(f"  - {h}")
        print("\nDoğrulama BAŞARISIZ.")
        return 1
    print("\n✅ Tüm örnekler geçerli.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
