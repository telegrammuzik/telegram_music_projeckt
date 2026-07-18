"""
Ek: Türkçe hece ölçüsü/kafiye sayacı. Basit ünlü-tabanlı hece bölme (Türkçe'de
her ünlü harf bir hece demektir — bu kural yaygın istisnalar dışında oldukça
güvenilirdir) ve son seslere bakarak kaba bir kafiye kontrolü yapar.
"""

VOWELS = set("aeıioöuüAEIİOÖUÜ")


def count_syllables(word: str) -> int:
    return max(sum(1 for ch in word if ch in VOWELS), 1)


def syllabify_line(line: str):
    words = line.split()
    return sum(count_syllables(w) for w in words)


def analyze_lyrics(lines):
    """lines: şarkı sözü satırları listesi. Her satırın hece sayısını ve
    satır sonu kafiye (son 2-3 harf) bilgisini döner."""
    results = []
    for line in lines:
        clean = "".join(ch for ch in line if ch.isalpha() or ch == " ")
        syll_count = syllabify_line(clean)
        last_word = clean.split()[-1] if clean.split() else ""
        rhyme_key = last_word.lower()[-3:] if len(last_word) >= 3 else last_word.lower()
        results.append({"line": line, "syllables": syll_count, "rhyme_key": rhyme_key})
    return results


def check_rhyme_scheme(lines):
    analysis = analyze_lyrics(lines)
    scheme = []
    seen = {}
    next_letter = ord("A")
    for item in analysis:
        key = item["rhyme_key"]
        if key not in seen:
            seen[key] = chr(next_letter)
            next_letter += 1
        scheme.append(seen[key])
    return "".join(scheme), analysis
