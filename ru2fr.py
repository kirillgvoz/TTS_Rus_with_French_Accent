#!/usr/bin/env python3
"""ru2fr — русский текст → французская транскрипция (весь язык, без лексикона).

Пайплайн:
    русский текст → [epitran: русский G2P → IPA] → [IPA → французская орфография]
    → французская запись для чтения Kyutai TTS русскими звуками с акцентом.

Примеры:
    другой       → druk         → drouque       (= друк)
    здравствуйте → zdrafstvujtʲe → zdrafstvouïtié
    спасибо      → spasʲibo     → spaçibo       (ç = анти-liaison)

Использование:
    python ru2fr.py "Здравствуйте, друг!"
    echo "Привет" | python ru2fr.py -
    python ru2fr.py --phon "друг"
"""
import sys
import re
import warnings

warnings.filterwarnings("ignore")
import epitran

_EPI = epitran.Epitran("rus-Cyrl")

VOWELS = set("aeiouɨəɛɔy")

# IPA-символ → французская запись (длинные символы первыми)
MAP = [
    ("t͡ɕ", "tch"), ("d͡ʒ", "dj"), ("ɕː", "chtch"), ("ɕ", "chtch"),
    ("ts", "ts"), ("ʃ", "ch"), ("ʂ", "ch"), ("ʒ", "j"), ("ʐ", "j"),
    ("ʈ", "t"), ("ɖ", "d"), ("ɳ", "n"), ("ɭ", "l"), ("x", "kh"),
    ("a", "a"), ("e", "é"), ("i", "i"), ("o", "o"), ("u", "ou"),
    ("ɨ", "u"), ("ə", "e"), ("ɛ", "è"), ("ɔ", "o"), ("y", "u"),
    ("p", "p"), ("b", "b"), ("t", "t"), ("d", "d"), ("k", "k"), ("ɡ", "g"), ("g", "g"),
    ("f", "f"), ("v", "v"), ("s", "s"), ("z", "z"), ("r", "r"), ("l", "l"),
    ("m", "m"), ("n", "n"), ("ɲ", "gn"), ("j", "i"),
]

LIAISON_ONSET = {"s": "ç", "z": "z", "t": "t", "d": "d", "n": "n", "p": "p", "x": "x"}


def ipa_to_fr(word_ipa: str) -> str:
    """IPA русского слова → французская орфография."""
    out = []
    soft = False          # после ʲ — вставить i перед следующей гласной
    prev_out_vowel = False
    i = 0
    s = word_ipa
    table = dict(MAP)
    while i < len(s):
        if s[i] == "ː":
            if out and out[-1] and out[-1][-1] in "aeiouéè":
                out[-1] = out[-1] * 2
            i += 1
            continue
        if s[i] in "ʲˠ":
            if s[i] == "ʲ":
                soft = True
            i += 1
            continue
        sym = None
        for k, _ in MAP:
            if s.startswith(k, i):
                sym = k
                break
        if sym is None:
            sym = s[i]
        i += len(sym)
        g = table.get(sym, "")
        if not g:
            continue
        is_vowel = sym in VOWELS
        if is_vowel:
            if soft and sym != "i":
                g = "i" + g      # лʲе → lie, меня → mienia
            soft = False
        elif sym == "j":
            if prev_out_vowel:
                g = "ï"          # май → maï, уй → ouï
            soft = False         # iotation уже в "i" от j (съезд → siést)
        else:
            soft = False         # согласная поглощает ʲ (большое → bolchoé)
        out.append(g)
        prev_out_vowel = bool(g) and g[-1] in "aeiouéèï"
    word = "".join(out)
    # финальные оглушения/буквенные особенности французского
    if word.endswith("k") and len(word) > 1:
        word = word[:-1] + "que"     # друг→drouque
    if word.endswith("g") and len(word) > 1:
        word = word[:-1] + "gue"
    if word.endswith("s") and len(word) > 2 and word[-2] in "aeiouéè":
        word = word + "s"            # час → tchass (иначе French молчит)
    return word


def convert(text: str) -> str:
    """Весь текст: G2P по каждому слову + анти-liaison + французская пунктуация."""
    tokens = re.findall(r"[\w\-]+|[^\w\s]+|\s+", text, re.UNICODE)
    result = []
    prev_word_ends_vowel = False
    for tok in tokens:
        if re.fullmatch(r"[\w\-]+", tok, re.UNICODE):
            ipa = _EPI.transliterate(tok.lower())
            fr = ipa_to_fr(ipa)
            if prev_word_ends_vowel and fr and fr[0].lower() in LIAISON_ONSET:
                repl = LIAISON_ONSET[fr[0].lower()]
                if fr[0].isupper():
                    repl = repl.upper()
                fr = repl + fr[1:]
            result.append(fr)
            prev_word_ends_vowel = bool(fr) and fr[-1].lower() in "aeiouéèï"
        elif re.fullmatch(r"[^\w\s]+", tok):
            if tok[0] in "!?:;" and result and result[-1] != " ":
                result.append(" ")
            result.append(tok)
            if tok[0] in ".!?…;:":
                prev_word_ends_vowel = False
        else:
            result.append(tok)
    return "".join(result).strip()


def phon_debug(word: str) -> str:
    ipa = _EPI.transliterate(word.lower())
    return f"{word} → /{ipa}/ → {ipa_to_fr(ipa)}"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    if args[0] == "--phon":
        print(phon_debug(args[1]))
        return
    inp = args[0]
    text = sys.stdin.read() if inp == "-" else inp
    print(convert(text))


if __name__ == "__main__":
    main()
