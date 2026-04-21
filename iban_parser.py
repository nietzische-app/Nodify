"""IBAN ayrıştırıcı ve doğrulayıcı.

Kullanım:
    python iban_parser.py                  # etkileşimli, IBAN sorar
    python iban_parser.py TR12...          # argüman olarak tek IBAN
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass


# ISO 13616 - ülke başına IBAN uzunlukları.
IBAN_LENGTHS: dict[str, int] = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BR": 29, "BY": 28, "CH": 21, "CR": 22, "CY": 28,
    "CZ": 24, "DE": 22, "DK": 18, "DO": 28, "EE": 20, "EG": 29, "ES": 24,
    "FI": 18, "FO": 18, "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18,
    "GR": 27, "GT": 28, "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IQ": 23,
    "IS": 26, "IT": 27, "JO": 30, "KW": 30, "KZ": 20, "LB": 28, "LC": 32,
    "LI": 21, "LT": 20, "LU": 20, "LV": 21, "LY": 25, "MC": 27, "MD": 24,
    "ME": 22, "MK": 19, "MR": 27, "MT": 31, "MU": 30, "NL": 18, "NO": 15,
    "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29, "RO": 24, "RS": 22,
    "SA": 24, "SC": 31, "SE": 24, "SI": 19, "SK": 24, "SM": 27, "ST": 25,
    "SV": 28, "TL": 23, "TN": 24, "TR": 26, "UA": 29, "VA": 22, "VG": 24,
    "XK": 20,
}


# Türkiye Cumhuriyet Merkez Bankası EFT kodları (yaygın bankalar).
TR_BANK_CODES: dict[str, str] = {
    "00001": "Türkiye Cumhuriyet Merkez Bankası",
    "00004": "İller Bankası",
    "00010": "T.C. Ziraat Bankası",
    "00012": "Türkiye Halk Bankası",
    "00015": "Türkiye Vakıflar Bankası",
    "00016": "Türkiye Sınai Kalkınma Bankası",
    "00017": "Türkiye Kalkınma ve Yatırım Bankası",
    "00029": "Birleşik Fon Bankası",
    "00032": "Türk Ekonomi Bankası (TEB)",
    "00046": "Akbank",
    "00059": "Şekerbank",
    "00062": "Türkiye Garanti Bankası (Garanti BBVA)",
    "00064": "Türkiye İş Bankası",
    "00067": "Yapı ve Kredi Bankası",
    "00092": "Denizbank",
    "00094": "Citibank",
    "00096": "Turkish Bank",
    "00098": "Arap Türk Bankası",
    "00099": "Société Générale",
    "00100": "HSBC Bank",
    "00103": "Fibabanka",
    "00108": "Odea Bank",
    "00109": "Bank of China Turkey",
    "00111": "QNB Finansbank",
    "00115": "Deutsche Bank",
    "00121": "Alternatifbank",
    "00123": "HSBC Bank",
    "00124": "Alternatifbank",
    "00125": "Burgan Bank",
    "00134": "ICBC Turkey Bank",
    "00135": "Rabobank",
    "00137": "Intesa Sanpaolo",
    "00138": "Standard Chartered Yatırım Bankası",
    "00139": "Turkland Bank (T-Bank)",
    "00143": "MUFG Bank Turkey",
    "00146": "Golden Global Yatırım Bankası",
    "00147": "DenizBank",
    "00148": "Vakıf Katılım Bankası",
    "00203": "Albaraka Türk Katılım Bankası",
    "00205": "Kuveyt Türk Katılım Bankası",
    "00206": "Türkiye Finans Katılım Bankası",
    "00209": "Ziraat Katılım Bankası",
    "00210": "Türkiye Emlak Katılım Bankası",
    "00211": "Hayat Finans Katılım Bankası",
    "00212": "TOM Katılım Bankası",
}


# Ülkeye göre BBAN içindeki alanların (başlangıç, bitiş) konumları.
# Konumlar IBAN üzerindeki 0-tabanlı karakter indeksleridir.
# Değer yoksa o ülke IBAN'ı o alanı ayrı bir parça olarak içermez.
COUNTRY_STRUCTURE: dict[str, dict[str, tuple[int, int]]] = {
    "TR": {"bank": (4, 9), "account": (10, 26)},
    "GB": {"bank": (4, 8), "branch": (8, 14), "account": (14, 22)},
    "DE": {"bank": (4, 12), "account": (12, 22)},
    "FR": {"bank": (4, 9), "branch": (9, 14), "account": (14, 25)},
    "ES": {"bank": (4, 8), "branch": (8, 12), "account": (14, 24)},
    "IT": {"bank": (5, 10), "branch": (10, 15), "account": (15, 27)},
    "NL": {"bank": (4, 8), "account": (8, 18)},
    "BE": {"bank": (4, 7), "account": (7, 14)},
    "CH": {"bank": (4, 9), "account": (9, 21)},
    "AT": {"bank": (4, 9), "account": (9, 20)},
    "PT": {"bank": (4, 8), "branch": (8, 12), "account": (12, 23)},
    "GR": {"bank": (4, 7), "branch": (7, 11), "account": (11, 27)},
    "PL": {"branch": (4, 12), "account": (12, 28)},
    "RO": {"bank": (4, 8), "account": (8, 24)},
    "IE": {"bank": (4, 8), "branch": (8, 14), "account": (14, 22)},
    "SE": {"bank": (4, 7), "account": (7, 24)},
    "NO": {"bank": (4, 8), "account": (8, 15)},
    "DK": {"bank": (4, 8), "account": (8, 18)},
    "FI": {"bank": (4, 10), "account": (10, 18)},
}


@dataclass
class IbanResult:
    raw: str
    normalized: str
    valid: bool
    country: str | None = None
    check_digits: str | None = None
    bank_code: str | None = None
    bank_name: str | None = None
    branch_code: str | None = None
    account: str | None = None
    error: str | None = None

    def format(self) -> str:
        lines = [f"IBAN          : {self.pretty()}"]
        lines.append(f"Geçerli mi?   : {'✓ Evet' if self.valid else '✗ Hayır'}")
        if self.error:
            lines.append(f"Hata          : {self.error}")
        if self.country:
            lines.append(f"Ülke kodu     : {self.country}")
        if self.check_digits:
            lines.append(f"Kontrol rakam.: {self.check_digits}")
        if self.bank_code:
            lines.append(f"Banka kodu    : {self.bank_code}")
        if self.bank_name:
            lines.append(f"Banka adı     : {self.bank_name}")
        if self.branch_code:
            lines.append(f"Şube kodu     : {self.branch_code}")
        if self.account:
            lines.append(f"Hesap numarası: {self.account}")
        if self.country == "TR" and self.valid and not self.branch_code:
            lines.append(
                "Not           : Türkiye IBAN yapısı şube/şehir bilgisini "
                "içermez; bu bilgi bankadan öğrenilebilir."
            )
        return "\n".join(lines)

    def pretty(self) -> str:
        return " ".join(
            self.normalized[i : i + 4] for i in range(0, len(self.normalized), 4)
        )


def normalize(iban: str) -> str:
    """Boşlukları temizler ve harfleri büyütür."""
    return re.sub(r"\s+", "", iban).upper()


def mod97(iban: str) -> int:
    """ISO 7064 mod-97 kontrolü. Geçerli IBAN'da sonuç 1 olur."""
    rearranged = iban[4:] + iban[:4]
    # Harfleri rakamlara çevir: A=10, B=11, ... Z=35
    numeric = "".join(
        str(ord(c) - 55) if c.isalpha() else c for c in rearranged
    )
    # Büyük sayıyı parça parça işle.
    remainder = 0
    for digit in numeric:
        remainder = (remainder * 10 + int(digit)) % 97
    return remainder


def parse_iban(iban: str) -> IbanResult:
    normalized = normalize(iban)
    result = IbanResult(raw=iban, normalized=normalized, valid=False)

    if not re.fullmatch(r"[A-Z0-9]+", normalized):
        result.error = "IBAN sadece harf ve rakam içermelidir."
        return result

    if len(normalized) < 15 or len(normalized) > 34:
        result.error = "IBAN uzunluğu 15-34 karakter aralığında olmalı."
        return result

    country = normalized[:2]
    if not country.isalpha():
        result.error = "İlk iki karakter ülke kodu (harf) olmalı."
        return result

    result.country = country
    result.check_digits = normalized[2:4]

    expected = IBAN_LENGTHS.get(country)
    if expected is None:
        result.error = f"Bilinmeyen ülke kodu: {country}"
        return result

    if len(normalized) != expected:
        result.error = (
            f"{country} için beklenen uzunluk {expected}, "
            f"girilen {len(normalized)}."
        )
        return result

    if mod97(normalized) != 1:
        result.error = "Kontrol basamağı hatalı (mod-97 doğrulaması başarısız)."
        return result

    result.valid = True

    structure = COUNTRY_STRUCTURE.get(country)
    if structure:
        if "bank" in structure:
            start, end = structure["bank"]
            result.bank_code = normalized[start:end]
        if "branch" in structure:
            start, end = structure["branch"]
            result.branch_code = normalized[start:end]
        if "account" in structure:
            start, end = structure["account"]
            result.account = normalized[start:end]

    if country == "TR" and result.bank_code:
        result.bank_name = TR_BANK_CODES.get(result.bank_code, "Bilinmiyor")

    return result


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        ibans = argv[1:]
    else:
        try:
            entered = input("IBAN giriniz: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 1
        if not entered:
            print("Boş giriş.")
            return 1
        ibans = [entered]

    for i, iban in enumerate(ibans):
        if i:
            print("-" * 40)
        print(parse_iban(iban).format())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
