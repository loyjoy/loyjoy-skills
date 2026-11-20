#!/usr/bin/env python3
"""Mechanical checks for a LoyJoy phone-agent custom block.

Usage:
    python3 prompt_check.py CUSTOM_BLOCK [--standard STANDARD] [--budget 2000] [--json]

Runs the measurements and sweeps that the skill requires before every delivery
and that a model does not perform reliably by hand: size against budget,
duplicate sentences (including shorter sentences contained in longer ones),
cross-reference resolution, overlap with the standard prompt, topic ownership
(one topic, one section), tool-name consistency, search-discipline
contradictions, and a set of formatting checks.

Every finding is a pointer, not a verdict. Read the named line before changing
anything. Exit code is 1 when at least one ERROR-level finding exists.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict

# Characters per token for German prose. Deliberately conservative.
CHARS_PER_TOKEN = 3.0

STANDARD_TERMS = [
    "markdown", "emoji", "begrüßung", "begruessung", "ziffer", "buchstabier",
    "wissenssuche", "such", "weiterleit", "preis", "sprache", "abschluss",
    "acknowledge", "bridging", "tool", "datum", "uhrzeit", "locale",
]

SEARCH_REQUIRED = re.compile(r"\b(such|recherchier|nachschlag|knowledge|wissensbasis)", re.I)
SEARCH_FORBIDDEN = re.compile(r"(ohne\s+such|nicht\s+such|keine\s+such|no\s+search|ohne\s+tool)", re.I)
STATE_VERB = re.compile(
    r"\b(frag|erfass|lies\s+vor|wiederhol|bestätig|bestaetig|notier|prüf|pruef|"
    r"warte|übernimm|uebernimm|sende|leite)", re.I)
PSEUDOCODE = re.compile(r"(\bIF\b.{0,40}\bTHEN\b|==|>=|<=|&&|\|\||\{\{|\bELSE\b)")
MARKDOWN_INLINE = re.compile(r"(\[[^\]]{1,60}\]\([^)]{1,200}\)|\*\*|__|`[^`]{1,40}`)")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]")
HARDCODED_DATE = re.compile(r"\b(\d{1,2}\.\s?\d{1,2}\.\s?\d{2,4}|\b20\d{2}\b)")
DATE_TEMPLATE = re.compile(r"\$\{[^}]*[Dd]ate[^}]*\}")
TEMPLATE_EXPR = re.compile(r"\$\{[^}]*\}")
DYNAMIC_TEMPLATE = re.compile(
    r"\$\{[^}]*\b(?:formattedLocalDate(?:Time)?|localDate(?:DayOfWeek|DayOfMonth|MonthOfYear|Year)?"
    r"|localDateTime|displayLanguage|clientLocale|arrayIncludes|arrayLength|toInteger"
    r"|timestamp(?:Ms)?)\s*\(")
DIGIT_COUNT = re.compile(r"(anzahl\s+der\s+ziffern|zähl|zaehl|wie\s+viele\s+ziffern|digit\s+count)", re.I)
HEADING = re.compile(r"^\s{0,3}#{1,4}\s+(.+?)\s*$", re.M)
NUMBERED = re.compile(r"^\s*\d+[.)]\s+", re.M)
BULLET = re.compile(r"^\s*[-*+]\s+", re.M)

# Topics that one section must own exclusively. Prefix matching on word
# boundaries, so "ziffer" also matches "Ziffernfolge". Extend the lists when a
# tenant adds a topic; topics here are heuristics, WARN is a pointer.
TOPIC_TERMS = {
    "Ziffern erfassen": ("ziffer",),
    "Preis": ("preis", "kosten", "tarif", "gebühr", "gebuehr"),
    "Suche/Wissen": ("suche", "sucht", "suchen", "wissensbasis", "knowledge", "nachschlag"),
    "Transfer/Weiterleitung": ("transfer", "weiterleit", "durchstell", "durchverbind"),
    "Datenschutz/sensible Daten": ("datenschutz", "sensibl", "gesundheitsdaten"),
    "Erreichbarkeit/Zeiten": ("erreichbar", "servicezeit", "öffnungszeit", "geöffnet", "geoeffnet",
                             "geschlossen"),
    "Sprache": ("sprache", "englisch", "deutsch", "fremdsprache"),
    "Begrüßung": ("begrüßung", "begruessung", "grüß", "gruess"),
    "Gesprächsabschluss": ("gesprächsabschluss", "gespraechsabschluss", "verabschied",
                           "auf wiederhör", "auf wiederhoer", "tschüss", "tschuess", "aufleg"),
    "Notfall": ("notfall", "notruf", "gefahr", "gefähr"),
    "E-Mail": ("e-mail", "email"),
}
TOPIC_PATTERNS = {
    topic: re.compile(r"(?i)\b(?:" + "|".join(re.escape(t) for t in terms) + r")")
    for topic, terms in TOPIC_TERMS.items()
}
# Same reference markers as check_cross_refs; such sentences delegate, they do
# not regulate, so they do not count as topic ownership.
REFERENCE_SENTENCE = re.compile(r"(?i)\b(?:siehe|vgl|wechsle in|nutze|gemäß|gemäss|see)\b")

BUDGETS = {
    "single": (800, 1500),
    "service": (2000, 3000),
    "complex": (3000, 4000),
}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def sentences(text):
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for part in re.split(r"(?<=[.!?:])\s+", stripped):
            part = part.strip(" -*+0123456789.)")
            if len(part.split()) >= 4:
                out.append((lineno, part))
    return out


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def section_map(text):
    """Return a function mapping a line number to its enclosing section name."""
    marks = [(text[:m.start()].count("\n") + 1, m.group(1)) for m in HEADING.finditer(text)]

    def section_for(lineno):
        name = ""
        for line, heading in marks:
            if line <= lineno:
                name = re.sub(r"^\d+[.)]\s*", "", heading).split("(")[0].strip()
            else:
                break
        return name

    return section_for


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, check, message, line=None):
        self.items.append({"level": level, "check": check, "message": message, "line": line})

    def error(self, *a, **k):
        self.add("ERROR", *a, **k)

    def warn(self, *a, **k):
        self.add("WARN", *a, **k)

    def info(self, *a, **k):
        self.add("INFO", *a, **k)


def check_size(text, budget, rep):
    chars = len(text)
    words = len(text.split())
    tokens = round(chars / CHARS_PER_TOKEN)
    target, ceiling = budget
    rep.info("size", f"{words} Wörter, {chars} Zeichen, ca. {tokens} Token "
                     f"(Budget {target}, Hard Ceiling {ceiling})")
    if tokens > ceiling:
        rep.error("size", f"Über dem Hard Ceiling: {tokens} > {ceiling} Token. "
                          "Nichts mehr ergänzen, umstrukturieren.")
    elif tokens > target:
        rep.warn("size", f"Über Budget: {tokens} > {target} Token. "
                         "Vor der nächsten Ergänzung kürzen.")
    return {"chars": chars, "words": words, "tokens": tokens}


def check_duplicates(sents, section_for, rep):
    seen = []
    for lineno, s in sents:
        toks = norm(s)
        if len(toks) < 3:
            continue
        sec = section_for(lineno)
        for prev_line, prev_s, prev_toks, prev_sec in seen:
            sim = jaccard(toks, prev_toks)
            if sim >= 0.95:
                rep.error("duplicate", f"Zeile {lineno} ({sec}) wiederholt Zeile {prev_line} ({prev_sec}) "
                                       f"fast wörtlich: \"{s[:80]}\"", lineno)
                break
            if sim >= 0.7:
                rep.warn("duplicate", f"Zeile {lineno} ({sec}) überlappt stark mit Zeile {prev_line} "
                                      f"({prev_sec}) ({sim:.0%}): \"{s[:80]}\"", lineno)
                break
            # Containment catches the shorter rule fully restated inside a
            # longer one, which jaccard underrates because of unequal lengths.
            smaller, larger = sorted((toks, prev_toks), key=len)
            small_set = set(smaller)
            if small_set:
                containment = len(small_set & set(larger)) / len(small_set)
                if containment >= 0.8:
                    if len(toks) <= len(prev_toks):
                        inner, inner_sec, outer, outer_sec = lineno, sec, prev_line, prev_sec
                    else:
                        inner, inner_sec, outer, outer_sec = prev_line, prev_sec, lineno, sec
                    rep.warn("duplicate", f"Teilduplikat: Zeile {inner} ({inner_sec}) ist zu "
                                          f"{containment:.0%} in Zeile {outer} ({outer_sec}) "
                                          f"enthalten: \"{s[:80]}\"", inner)
                    break
        seen.append((lineno, s, toks, sec))


def check_sections(text, rep):
    headings = [h.strip() for h in HEADING.findall(text)]
    clean = [re.sub(r"^\d+[.)]\s*", "", h) for h in headings]
    dupes = [h for h, c in Counter(clean).items() if c > 1]
    for d in dupes:
        rep.error("sections", f"Sektionsname mehrfach vergeben: \"{d}\"")
    # Only shared building blocks are expected to be referenced by other sections.
    shared = ("datenerfassung", "gesprächsabschluss", "gespraechsabschluss", "eskalation",
              "erreichbarkeit", "notfall", "wissensnutzung", "einwandbehandlung")
    for h in clean:
        key = h.split("(")[0].strip()
        if len(key) < 4 or not key.lower().startswith(shared):
            continue
        hits = len(re.findall(re.escape(key), text, re.I)) - clean.count(h)
        if hits <= 0:
            rep.warn("sections", f"Gemeinsame Sektion \"{key}\" wird von keinem Use Case "
                                 "referenziert. Entweder tote Sektion oder fehlender Verweis.")
    rep.info("sections", f"{len(clean)} Sektionen: " + ", ".join(clean))
    return clean


def check_cross_refs(text, sections, rep):
    keys = [re.sub(r"^\d+[.)]\s*", "", s).split("(")[0].strip().lower() for s in sections]
    pattern = re.compile(r"(?i:siehe|vgl\.?|wechsle in|nutze|gemäß|see)\s+([A-ZÄÖÜ][\wÄÖÜäöüß \-/]{3,40})")
    for m in pattern.finditer(text):
        target = m.group(1).strip().rstrip(".,;:").lower()
        if not target:
            continue
        if not any(target.startswith(k) or k.startswith(target) for k in keys):
            line = text[:m.start()].count("\n") + 1
            rep.warn("crossref", f"Zeile {line}: Verweis auf \"{m.group(1).strip()}\" "
                                 "löst auf keine Sektion auf", line)


def check_standard_overlap(text, standard, section_for, rep):
    if not standard:
        rep.info("standard", "Kein Standard-Prompt übergeben, Dublettenprüfung gegen den Standard "
                             "übersprungen. Mit --standard nachholen.")
        return
    std_sents = [norm(s) for _, s in sentences(standard)]
    for lineno, s in sentences(text):
        toks = norm(s)
        if len(toks) < 3:
            continue
        for st in std_sents:
            if jaccard(toks, st) >= 0.6:
                rep.error("standard", f"Zeile {lineno} ({section_for(lineno)}) dupliziert eine "
                                      f"Standard-Regel: \"{s[:90]}\". Entfernen oder als "
                                      f"Override deklarieren.", lineno)
                break
    low = text.lower()
    for term in STANDARD_TERMS:
        if term in low and term in standard.lower():
            rep.info("standard", f"Begriff \"{term}\" kommt in Custom-Block und Standard vor. "
                                 "Prüfen, ob Override oder Dublette.")


def check_topics(text, section_for, rep):
    """One topic, one section: a topic regulated in two or more sections is a
    WARN, sentences that merely reference another section do not count."""
    by_section = defaultdict(list)
    for lineno, s in sentences(text):
        by_section[section_for(lineno)].append((lineno, s))
    owners = defaultdict(list)  # topic -> [(section, [lines])]
    for topic, pattern in TOPIC_PATTERNS.items():
        for sec, sents in by_section.items():
            lines = [lineno for lineno, s in sents
                     if pattern.search(s) and not REFERENCE_SENTENCE.search(s)]
            if len(lines) >= 2:
                owners[topic].append((sec, lines))
    for topic, secs in sorted(owners.items()):
        if len(secs) >= 2:
            detail = "; ".join(f"\"{sec}\" (Zeilen {', '.join(map(str, lines))})"
                               for sec, lines in secs)
            rep.warn("topics", f"Thema \"{topic}\" wird in mehreren Sektionen geregelt: {detail}. "
                               "Eine Sektion besitzt das Thema, die anderen verweisen darauf "
                               "(siehe ...).")
    single = "; ".join(f"{t} → \"{secs[0][0]}\""
                       for t, secs in sorted(owners.items()) if len(secs) == 1)
    if single:
        rep.info("topics", f"Themenkarte: {single}")
    if not owners:
        rep.info("topics", "Keines der bekannten Themen erkannt. Themenliste im Skript "
                           "erweitern, wenn der Agent weitere Themen regelt.")
    return owners


def check_tools(text, rep):
    m = re.search(r"^\s{0,3}#{1,4}\s*\d*\.?\s*Tools?\s*$(.*?)(?=^\s{0,3}#{1,4}\s|\Z)",
                  text, re.M | re.S | re.I)
    if not m:
        rep.warn("tools", "Keine Tools-Sektion gefunden. Jeder Custom-Block braucht eine.")
        return []
    block = m.group(1)
    names = re.findall(r"^\s*[-*+]?\s*`?([a-z][a-z0-9_]{2,40})`?\s*[:–-]", block, re.M | re.I)
    names = sorted(set(names))
    if not names:
        rep.warn("tools", "Tools-Sektion enthält keine erkennbaren Tool-Namen "
                          "(erwartet: \"- tool_name: ...\").")
    for n in names:
        occurrences = len(re.findall(re.escape(n), text, re.I))
        if occurrences == 1:
            rep.info("tools", f"Tool \"{n}\" wird nur in der Tools-Sektion genannt, "
                              "von keinem Use Case referenziert")
    eager = re.compile(r"(proaktiv|mit vorank|mit zustimmung|proactive|confirmation)", re.I)
    for line in block.splitlines():
        if re.match(r"^\s*[-*+]", line) and not eager.search(line):
            rep.warn("tools", f"Tool-Zeile ohne Eagerness-Klasse: \"{line.strip()[:70]}\"")
    return names


def check_search_discipline(sents, rep):
    required, forbidden = [], []
    for lineno, s in sents:
        if SEARCH_FORBIDDEN.search(s):
            forbidden.append((lineno, s))
        elif SEARCH_REQUIRED.search(s):
            required.append((lineno, s))
    if not required:
        rep.warn("search", "Keine Suchpflicht formuliert. Ohne sie antwortet der Agent aus dem Prompt.")
    subjects = defaultdict(list)
    for lineno, s in required + forbidden:
        for w in norm(s):
            if len(w) > 5:
                subjects[w].append(lineno)
    req_lines = {l for l, _ in required}
    forb_lines = {l for l, _ in forbidden}
    for w, lines in subjects.items():
        if set(lines) & req_lines and set(lines) & forb_lines:
            rep.error("search", f"Begriff \"{w}\" steht sowohl in einer Suchpflicht- als auch in "
                                f"einer Kein-Suchen-Regel (Zeilen {sorted(set(lines))}). "
                                "Widerspruch auflösen.")


def check_formatting(text, rep):
    for m in MARKDOWN_INLINE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        frag = m.group(0).strip()
        rep.warn("format", f"Zeile {line}: Markdown-Syntax im Sprach-Prompt (\"{frag[:40]}\"). "
                           "Der Agent liest Sonderzeichen vor.", line)
        break
    if EMOJI.search(text):
        rep.error("format", "Emoji im Sprach-Prompt. Emojis lassen sich nicht sprechen.")
    # Template expressions are runtime-resolved and may legitimately contain
    # operators (==, >=, &&). Mask them before the pseudocode scan.
    masked = TEMPLATE_EXPR.sub("TEMPLATE", text)
    for m in PSEUDOCODE.finditer(masked):
        line = text[:m.start()].count("\n") + 1
        rep.error("format", f"Zeile {line}: Pseudocode statt Satz (\"{m.group(0)}\"). "
                            "Logik ausformulieren.", line)
    if DIGIT_COUNT.search(text):
        rep.error("primitives", "Regel stützt sich auf das Zählen von Ziffern. "
                                "Modelle zählen unzuverlässig, Validierung schlägt auf korrekten Werten an.")
    if HARDCODED_DATE.search(text) and not DATE_TEMPLATE.search(text):
        rep.warn("date", "Festes Datum oder Jahreszahl ohne Datums-Template. "
                         "${localDate()} oder Äquivalent verwenden.")
    # Dynamic template values (date, time, state) belong at the end: the system
    # message is a concatenation, only the static head stays cacheable, and a
    # dynamic expression in the middle breaks the prefix cache.
    total = len(text.splitlines())
    if total:
        # First ~70% of lines are the cacheable static head.
        cutoff = max(1, int(total * 0.7))
        for m in DYNAMIC_TEMPLATE.finditer(text):
            line = text[:m.start()].count("\n") + 1
            if 1 <= line <= cutoff:
                rep.warn("date", f"Zeile {line}: dynamischer Template-Ausdruck im statischen Teil "
                                 f"({line}/{total}). Ans Ende verschieben, sonst wird der "
                                 "Cache-Präfix gebrochen.", line)


def check_flows(text, rep):
    blocks = re.split(r"^\s{0,3}#{1,4}\s+", text, flags=re.M)
    for block in blocks[1:]:
        title = block.splitlines()[0].strip() if block.splitlines() else ""
        bullets = BULLET.findall(block)
        numbered = NUMBERED.findall(block)
        stateful = len(STATE_VERB.findall(block))
        if len(bullets) >= 3 and not numbered and stateful >= 3:
            rep.error("flow", f"Sektion \"{title[:50]}\": Ablauf mit Zustand als Bullet-Liste. "
                              "Bullets tragen keine Reihenfolge, der Agent feuert Schritte erneut. "
                              "Als nummerierten Flow schreiben.")


def check_variety(text, rep):
    low = text.lower()
    has_samples = any(k in low for k in ("beispielformulierung", "sample phrase", "beispielsätze"))
    has_antilock = any(k in low for k in ("variiere", "wiederhole kein", "vary", "nicht wörtlich"))
    if has_samples and not has_antilock:
        rep.error("variety", "Beispielformulierungen ohne Anti-Lock-in-Zeile. "
                             "Der Agent wiederholt die Beispiele wörtlich.")
    if not has_antilock:
        rep.warn("variety", "Keine Variety-Regel gefunden. Der Agent klingt nach drei Turns robotisch.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("custom")
    ap.add_argument("--standard", help="Datei mit dem LoyJoy Standard-Voice-Prompt")
    ap.add_argument("--budget", default="service", help="single | service | complex | <Zahl>")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    text = open(args.custom, encoding="utf-8").read()
    standard = open(args.standard, encoding="utf-8").read() if args.standard else None

    if args.budget in BUDGETS:
        budget = BUDGETS[args.budget]
    else:
        t = int(args.budget)
        budget = (t, int(t * 1.4))

    rep = Report()
    section_for = section_map(text)
    size = check_size(text, budget, rep)
    sents = sentences(text)
    check_duplicates(sents, section_for, rep)
    sections = check_sections(text, rep)
    check_cross_refs(text, sections, rep)
    check_standard_overlap(text, standard, section_for, rep)
    check_topics(text, section_for, rep)
    check_tools(text, rep)
    check_search_discipline(sents, rep)
    check_formatting(text, rep)
    check_flows(text, rep)
    check_variety(text, rep)

    errors = [i for i in rep.items if i["level"] == "ERROR"]
    warns = [i for i in rep.items if i["level"] == "WARN"]

    if args.json:
        print(json.dumps({"size": size, "findings": rep.items}, ensure_ascii=False, indent=2))
    else:
        order = {"ERROR": 0, "WARN": 1, "INFO": 2}
        for item in sorted(rep.items, key=lambda i: (order[i["level"]], i["check"])):
            print(f"[{item['level']:5}] {item['check']:10} {item['message']}")
        print(f"\n{len(errors)} Fehler, {len(warns)} Warnungen.")
        if errors:
            print("Fehler vor der Auslieferung beheben. Warnungen bewusst entscheiden, nicht ignorieren.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
