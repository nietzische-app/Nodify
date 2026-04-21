"""IBAN doğrulama ve banka bilgisi çıkarma."""

from __future__ import annotations

import re
import sys


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


TR_BANK_CODES: dict[str, str] = {
    "00010": "Ziraat Bankası",
    "00012": "Halkbank",
    "00015": "Vakıfbank",
    "00032": "TEB",
    "00046": "Akbank",
    "00062": "Garanti BBVA",
    "00064": "İş Bankası",
    "00067": "Yapı Kredi",
    "00092": "Denizbank",
    "00111": "QNB Finansbank",
    "00148": "Vakıf Katılım",
    "00203": "Albaraka Türk",
    "00205": "Kuveyt Türk",
    "00206": "Türkiye Finans",
    "00209": "Ziraat Katılım",
    "00210": "Emlak Katılım",
}


def mod97(iban: str) -> int:
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
    remainder = 0
    for digit in numeric:
        remainder = (remainder * 10 + int(digit)) % 97
    return remainder


def parse_iban(iban: str) -> str:
    normalized = re.sub(r"\s+", "", iban).upper()

    if not re.fullmatch(r"[A-Z0-9]+", normalized):
        return "Geçersiz: IBAN sadece harf ve rakam içermelidir."

    country = normalized[:2]
    expected = IBAN_LENGTHS.get(country)
    if expected is None:
        return f"Geçersiz: bilinmeyen ülke kodu ({country})."
    if len(normalized) != expected:
        return f"Geçersiz: {country} için uzunluk {expected} olmalı."
    if mod97(normalized) != 1:
        return "Geçersiz: kontrol basamağı hatalı."

    lines = ["Geçerli ✓", f"Ülke: {country}"]
    if country == "TR":
        bank_code = normalized[4:9]
        bank_name = TR_BANK_CODES.get(bank_code, "bilinmiyor")
        lines.append(f"Banka: {bank_name} ({bank_code})")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    iban = argv[1] if len(argv) > 1 else input("IBAN: ").strip()
    if not iban:
        return 1
    print(parse_iban(iban))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
