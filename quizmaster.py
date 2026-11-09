"""
KI-QuizMaster LF 1–4 – Version 3.1
Lern-App für die Zwischenprüfung (IT-Berufe), Design angelehnt an die Siemens-Farbwelt.

Starten:
    pip install -r requirements.txt
    streamlit run quizmaster.py

Dateien im selben Ordner:
    fragen.json      Fragenkatalog (auch über die Seite "Eigene Fragen" erweiterbar)
    lernstand.json   wird automatisch angelegt (Statistik, Einstellungen, Lernfortschritt)
    logo.png         optional: wird oben rechts im Kopfbereich angezeigt
"""

import base64
import hashlib
import json
import random
import time
from html import escape
from pathlib import Path

import streamlit as st

ORDNER = Path(__file__).parent
FRAGEN_DATEI = ORDNER / "fragen.json"
LERNSTAND_DATEI = ORDNER / "lernstand.json"
ALT_STATS_DATEI = ORDNER / "stats.json"   # nur zur Übernahme alter Daten
LOGO_DATEI = ORDNER / "logo.png"
BUCHSTABEN = "ABCDEF"
PRUEFUNG_FRAGEN = 20
JOKER_START = 3
LF_ICONS = {"1": "🏢", "2": "🖥️", "3": "🌐", "4": "🔒"}


def lf_icon(key) -> str:
    return LF_ICONS.get(str(key), "📘")

st.set_page_config(page_title="KI-QuizMaster LF 1–4", page_icon="🎓", layout="centered")

# ---------------------------------------------------------------------------
# Design: zwei Farbpaletten (hell/dunkel) + gemeinsames Stylesheet
# ---------------------------------------------------------------------------
HELL = {
    "bg": "#f6f8f9", "panel": "#ffffff", "text": "#1c2433", "muted": "#5b6675",
    "rand": "#d5dce2", "grau": "#eef1f4", "petrol": "#009999", "petrol_d": "#007a7a",
    "petrol_l": "#e0f4f4", "akzent": "#007a7a", "on_petrol": "#ffffff", "hover": "#f2fbfb",
    "ok": "#1a8f4c", "ok_l": "#e3f5ea", "nok": "#c8322d", "nok_l": "#fbe6e5",
}
DUNKEL = {
    "bg": "#0a101c", "panel": "#131c2d", "text": "#e8edf3", "muted": "#9aa8b8",
    "rand": "#27344a", "grau": "#1d2940", "petrol": "#14b8b8", "petrol_d": "#0f9696",
    "petrol_l": "#0f2c38", "akzent": "#5ee0e0", "on_petrol": "#04202a", "hover": "#182a3e",
    "ok": "#3ddc84", "ok_l": "#0f2a1d", "nok": "#ff6b66", "nok_l": "#33171a",
}

CSS = """
.stApp{background:var(--bg);}
.stApp,.stApp p,.stApp li,.stApp label,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
.stApp div[data-testid="stMarkdownContainer"],.stApp button{
  color:var(--text);font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;}
.block-container{max-width:940px;padding-top:1.6rem;padding-bottom:4rem;}
footer,#MainMenu,[data-testid="stAppDeployButton"],[data-testid="stMainMenu"]{visibility:hidden;}
header[data-testid="stHeader"]{background:transparent;}
header[data-testid="stHeader"] *{color:var(--text)!important;}
section[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--rand);}
hr{border-color:var(--rand)!important;}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:var(--muted)!important;}
[data-testid="stExpander"]{background:var(--panel);border:1px solid var(--rand);border-radius:12px;}
[data-testid="stExpander"] summary,[data-testid="stExpander"] summary *{color:var(--text)!important;}
div[data-baseweb="input"],div[data-baseweb="textarea"],div[data-baseweb="base-input"]{
  background:var(--panel)!important;border-color:var(--rand)!important;border-radius:10px!important;}
.stTextInput input,.stTextArea textarea{background:var(--panel)!important;color:var(--text)!important;
  -webkit-text-fill-color:var(--text)!important;}
div[data-baseweb="input"]:focus-within,div[data-baseweb="textarea"]:focus-within{
  border-color:var(--petrol)!important;box-shadow:0 0 0 1px var(--petrol)!important;}
::placeholder{color:var(--muted)!important;-webkit-text-fill-color:var(--muted)!important;opacity:.8;}

.hero{background:linear-gradient(115deg,#000028 0%,#001f3f 55%,#007f86 130%);border-radius:18px;
  padding:26px 30px;margin-bottom:22px;border:1px solid rgba(255,255,255,.08);border-bottom:4px solid var(--petrol);
  display:flex;justify-content:space-between;align-items:center;gap:20px;}
.hero,.hero *{color:#fff!important;}
.hero .eyebrow{color:#7fe3e3!important;text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;font-weight:600;margin-bottom:6px;}
.hero .t{font-size:1.85rem;font-weight:700;letter-spacing:-.01em;line-height:1.15;}
.hero .s{opacity:.85;margin-top:6px;font-size:1rem;}

.tag{font-size:.74rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--akzent);}
.card{background:var(--panel);border:1px solid var(--rand);border-top:4px solid var(--petrol);border-radius:16px;
  padding:18px 20px 14px;min-height:178px;margin-bottom:8px;}
.card.dark{background:linear-gradient(120deg,#000028,#003a4d);border-color:#000028;border-top-color:var(--petrol);}
.card.dark,.card.dark *{color:#fff!important;}
.card .nr{display:inline-block;background:var(--petrol-l);color:var(--akzent)!important;font-weight:700;
  font-size:.78rem;padding:3px 10px;border-radius:999px;letter-spacing:.04em;}
.card .ti{font-weight:650;font-size:1.05rem;margin:10px 0 6px;line-height:1.3;}
.card .me{font-size:.85rem;color:var(--muted);}
.card.dark .nr{background:rgba(255,255,255,.15);}
.card.dark .me{opacity:.8;}

.stButton>button,.stDownloadButton>button{border-radius:12px;border:1px solid var(--rand);background:var(--panel);
  color:var(--text);font-weight:600;padding:.6rem 1rem;transition:all .15s ease;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--petrol);color:var(--akzent);background:var(--hover);}
.stButton>button p,.stDownloadButton>button p{color:inherit;margin:0;}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{
  background:var(--petrol);border-color:var(--petrol);color:var(--on-petrol);}
.stButton>button[kind="primary"]:hover,.stButton>button[data-testid="stBaseButton-primary"]:hover{
  background:var(--petrol-d);border-color:var(--petrol-d);color:var(--on-petrol);}
.stButton>button:disabled{opacity:.45;}
.st-key-opts button{justify-content:flex-start;text-align:left;padding:.9rem 1.1rem;font-weight:500;}
.st-key-opts button p{text-align:left;}

.frage{background:var(--panel);border:1px solid var(--rand);border-left:6px solid var(--petrol);border-radius:14px;
  padding:20px 24px;margin:8px 0 18px;}
.frage .q{font-size:1.3rem;line-height:1.4;margin-top:6px;font-weight:650;}
.frage.rueck{border-left-color:#000028;}

.opt{display:flex;align-items:center;gap:12px;background:var(--panel);border:1.5px solid var(--rand);
  border-radius:12px;padding:.85rem 1.1rem;margin-bottom:.55rem;}
.opt .b{flex:0 0 28px;height:28px;border-radius:50%;background:var(--grau);display:flex;
  align-items:center;justify-content:center;font-weight:700;font-size:.85rem;}
.opt .m{margin-left:auto;font-weight:700;}
.opt.ok{background:var(--ok-l);border-color:var(--ok);}
.opt.ok .b{background:var(--ok);color:var(--on-petrol);}
.opt.nok{background:var(--nok-l);border-color:var(--nok);}
.opt.nok .b{background:var(--nok);color:var(--on-petrol);}
.opt.dim{opacity:.5;}

.feedback{border-radius:14px;padding:14px 20px;margin:14px 0 8px;border:1px solid;font-weight:700;}
.feedback.ok{background:var(--ok-l);border-color:var(--ok);color:var(--ok);}
.feedback.nok{background:var(--nok-l);border-color:var(--nok);color:var(--nok);}
.erk{background:var(--petrol-l);border-left:5px solid var(--petrol);border-radius:10px;
  padding:14px 18px;margin:8px 0 16px;font-size:.96rem;line-height:1.55;}

.meta{display:flex;justify-content:space-between;font-size:.85rem;color:var(--muted);margin-bottom:6px;}
.bar{height:8px;background:var(--grau);border-radius:99px;overflow:hidden;}
.bar>div{height:100%;background:linear-gradient(90deg,var(--petrol),#33c2c2);border-radius:99px;}

.ring{width:176px;height:176px;border-radius:50%;margin:8px auto 14px;display:flex;align-items:center;justify-content:center;}
.ring-i{width:132px;height:132px;border-radius:50%;background:var(--bg);display:flex;flex-direction:column;
  align-items:center;justify-content:center;}
.ring-i b{font-size:2rem;line-height:1.1;}
.ring-i span{color:var(--muted);font-size:.9rem;}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:14px;}
.kpi{flex:1 1 140px;background:var(--panel);border:1px solid var(--rand);border-radius:14px;padding:14px 16px;text-align:center;}
.kpi b{display:block;font-size:1.5rem;}
.kpi span{color:var(--muted);font-size:.8rem;}
.srow{background:var(--panel);border:1px solid var(--rand);border-radius:14px;padding:16px 20px;margin-bottom:12px;}
.srow .k{font-weight:650;margin-bottom:4px;}
.srow .me{font-size:.85rem;color:var(--muted);}
.hero .ico{font-size:3.2rem;line-height:1;filter:drop-shadow(0 4px 10px rgba(0,0,0,.35));}
.card{transition:transform .15s ease,box-shadow .15s ease;}
.card:hover{transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.12);}
.card .kopf{display:flex;justify-content:space-between;align-items:center;}
.card .ic{font-size:2rem;line-height:1;}
.kpi .i{display:block;font-size:1.4rem;margin-bottom:2px;}
.sec{display:flex;align-items:center;gap:8px;margin:10px 0 8px;}
.sec .tag{font-size:.8rem;}
.srow .k .ic{margin-right:6px;}
.chip{display:inline-block;background:var(--grau);border-radius:999px;padding:2px 10px;font-size:.78rem;margin-right:6px;}
"""


def css_fuer(dunkel: bool) -> str:
    palette = DUNKEL if dunkel else HELL
    variablen = ";".join(f"--{k.replace('_', '-')}:{v}" for k, v in palette.items())
    schema = "dark" if dunkel else "light"
    return f":root{{{variablen}}}html{{color-scheme:{schema};}}{CSS}"


def md(text: str) -> None:
    st.markdown(text, unsafe_allow_html=True)


def esc(text) -> str:
    return escape(str(text))


# ---------------------------------------------------------------------------
# Daten, Lernstand, Hilfsfunktionen
# ---------------------------------------------------------------------------
@st.cache_data
def lade_fragen(pfad: str) -> dict:
    with open(pfad, encoding="utf-8") as datei:
        return json.load(datei)


def lade_lernstand() -> dict:
    leer = {"einstellungen": {}, "lf": {}, "fragen": {}}
    try:
        daten = json.loads(LERNSTAND_DATEI.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        try:  # Übernahme der Statistik aus Version 2
            leer["lf"] = json.loads(ALT_STATS_DATEI.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        return leer
    for schluessel, wert in leer.items():
        daten.setdefault(schluessel, wert)
    return daten


def speichere_lernstand() -> None:
    try:
        LERNSTAND_DATEI.write_text(
            json.dumps(st.session_state.lernstand, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # Die App läuft auch ohne Schreibrechte weiter


def frage_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:10]


def ist_sicher(eintrag) -> bool:
    return bool(eintrag) and eintrag.get("letzte") is True and eintrag.get("r", 0) >= 2


def lf_beherrschung(lf: dict):
    gelernt = st.session_state.lernstand["fragen"]
    sicher = sum(1 for f in lf["fragen"] if ist_sicher(gelernt.get(frage_id(f["frage"]))))
    return sicher, len(lf["fragen"])


def schwache_fragen(daten: dict) -> list:
    gelernt = st.session_state.lernstand["fragen"]
    return [dict(f, lf=k) for k, lf in daten.items() for f in lf["fragen"]
            if gelernt.get(frage_id(f["frage"]), {}).get("letzte") is False]


def ihk_note(prozent: int):
    if prozent >= 92:
        return "1", "sehr gut"
    if prozent >= 81:
        return "2", "gut"
    if prozent >= 67:
        return "3", "befriedigend"
    if prozent >= 50:
        return "4", "ausreichend"
    if prozent >= 30:
        return "5", "mangelhaft"
    return "6", "ungenügend"


def zeit_text(sekunden: int) -> str:
    return f"{sekunden // 60}:{sekunden % 60:02d} min"


def fehler_text(fehler: list) -> str:
    zeilen = ["Lernzettel – Fragen zum Wiederholen", ""]
    for nr, f in enumerate(fehler, 1):
        zeilen += [f"{nr}. {f['frage']}", f"   Richtig: {f['richtig_text']}",
                   f"   Erklärung: {f['erklaerung']}", ""]
    return "\n".join(zeilen)


def init_state() -> None:
    if "lernstand" not in st.session_state:
        st.session_state.lernstand = lade_lernstand()
    einst = st.session_state.lernstand["einstellungen"]
    standard = {
        "seite": "start",       # start | lauf | ende | statistik | editor
        "modus": "quiz",        # quiz | karten | pruefung
        "lf_key": None,         # "1".."4", "alle" oder "schwach"
        "fragen": [], "index": 0, "score": 0, "geprueft": False, "gewaehlt": None,
        "fehler": [], "durchlauf": 0, "zaehlt": True,
        "serie": 0, "beste_serie": 0, "joker": JOKER_START, "ausgeblendet": [],
        "start_zeit": time.time(), "dauer": 0,
        "dark": bool(einst.get("dark", False)),
        "anzahl": int(einst.get("anzahl", 10)),
        # Editor "Eigene Fragen"
        "ed_lf": "1", "ed_frage": "", "ed_o0": "", "ed_o1": "", "ed_o2": "", "ed_o3": "",
        "ed_richtig": 0, "ed_erk": "", "ed_meldung": None,
    }
    for schluessel, wert in standard.items():
        st.session_state.setdefault(schluessel, wert)


# ---------------------------------------------------------------------------
# Aktionen (Button-Callbacks)
# ---------------------------------------------------------------------------
def gehe(seite: str) -> None:
    st.session_state.seite = seite


def setze(schluessel: str, wert) -> None:
    st.session_state[schluessel] = wert


def setze_anzahl(wert: int) -> None:
    st.session_state.anzahl = wert
    st.session_state.lernstand["einstellungen"]["anzahl"] = wert
    speichere_lernstand()


def wechsle_theme() -> None:
    st.session_state.dark = not st.session_state.dark
    st.session_state.lernstand["einstellungen"]["dark"] = st.session_state.dark
    speichere_lernstand()


def starte(modus: str, lf_key: str, daten: dict, fragen=None, zaehlt: bool = True) -> None:
    s = st.session_state
    if fragen is None:
        if lf_key == "alle":
            pool = [dict(f, lf=k) for k, lf in daten.items() for f in lf["fragen"]]
        elif lf_key == "schwach":
            pool = schwache_fragen(daten)
            zaehlt = False
        else:
            pool = [dict(f, lf=lf_key) for f in daten[lf_key]["fragen"]]
        random.shuffle(pool)
        limit = PRUEFUNG_FRAGEN if modus == "pruefung" else s.anzahl
        fragen = pool[:limit] if limit else pool

    vorbereitet = []
    for f in fragen:
        f = dict(f)
        f.pop("gewaehlt", None)
        f["id"] = frage_id(f["frage"])
        f["richtig_text"] = f["optionen"][f["richtig"]]
        f["optionen_gemischt"] = random.sample(f["optionen"], k=len(f["optionen"]))
        vorbereitet.append(f)

    s.update(seite="lauf", modus=modus, lf_key=lf_key, fragen=vorbereitet, index=0, score=0,
             geprueft=False, gewaehlt=None, fehler=[], zaehlt=zaehlt, serie=0, beste_serie=0,
             joker=JOKER_START, ausgeblendet=[], start_zeit=time.time(), dauer=0,
             durchlauf=s.durchlauf + 1)


def registriere(frage: dict, richtig: bool) -> None:
    s = st.session_state
    eintrag = s.lernstand["fragen"].setdefault(frage["id"], {"r": 0, "f": 0, "letzte": None})
    eintrag["r" if richtig else "f"] += 1
    eintrag["letzte"] = richtig
    if richtig:
        s.score += 1
        s.serie += 1
        s.beste_serie = max(s.beste_serie, s.serie)
    else:
        s.serie = 0


def speichere_ergebnis() -> None:
    s = st.session_state
    if s.modus in ("quiz", "pruefung") and s.zaehlt and s.fragen:
        prozent = round(s.score / len(s.fragen) * 100)
        eintrag = s.lernstand["lf"].setdefault(s.lf_key, {"versuche": 0, "bestes": 0, "letztes": 0})
        eintrag["versuche"] += 1
        eintrag["bestes"] = max(eintrag["bestes"], prozent)
        eintrag["letztes"] = prozent
    speichere_lernstand()


def weiter() -> None:
    s = st.session_state
    s.index += 1
    s.geprueft = False
    s.gewaehlt = None
    s.ausgeblendet = []
    if s.index >= len(s.fragen):
        s.seite = "ende"
        s.dauer = int(time.time() - s.start_zeit)
        speichere_ergebnis()


def antworte(option: str) -> None:
    s = st.session_state
    frage = s.fragen[s.index]
    richtig = option == frage["richtig_text"]
    s.geprueft = True
    s.gewaehlt = option
    registriere(frage, richtig)
    if not richtig:
        s.fehler.append(dict(frage, gewaehlt=option))
    if s.modus == "pruefung":   # Prüfungsmodus: kein Feedback, direkt weiter
        weiter()


def nutze_joker() -> None:
    s = st.session_state
    frage = s.fragen[s.index]
    falsche = [o for o in frage["optionen_gemischt"] if o != frage["richtig_text"]]
    if s.joker > 0 and not s.ausgeblendet and len(falsche) >= 3:
        s.ausgeblendet = random.sample(falsche, 2)
        s.joker -= 1


def decke_auf() -> None:
    st.session_state.geprueft = True


def bewerte_karte(gewusst: bool) -> None:
    s = st.session_state
    karte = s.fragen[s.index]
    registriere(karte, gewusst)
    if not gewusst:
        s.fehler.append(dict(karte))
    weiter()


def setze_lernstand_zurueck() -> None:
    s = st.session_state
    s.lernstand["lf"] = {}
    s.lernstand["fragen"] = {}
    s.reset_frage = False
    speichere_lernstand()


def speichere_frage() -> None:
    s = st.session_state
    frage = s.ed_frage.strip()
    erklaerung = s.ed_erk.strip()
    texte = [s[f"ed_o{n}"].strip() for n in range(4)]
    optionen = [t for t in texte if t]
    richtige = texte[s.ed_richtig]

    fehler = None
    if not frage:
        fehler = "Bitte gib eine Frage ein."
    elif len(optionen) < 2:
        fehler = "Bitte gib mindestens zwei Antwortmöglichkeiten ein."
    elif len(set(optionen)) != len(optionen):
        fehler = "Die Antwortmöglichkeiten müssen unterschiedlich sein."
    elif not richtige:
        fehler = "Die als richtig markierte Antwort ist leer."
    elif not erklaerung:
        fehler = "Bitte ergänze eine kurze Erklärung."
    if fehler:
        s.ed_meldung = ("nok", fehler)
        return

    try:
        katalog = json.loads(FRAGEN_DATEI.read_text(encoding="utf-8"))
        katalog[s.ed_lf]["fragen"].append({
            "frage": frage, "optionen": optionen, "richtig": optionen.index(richtige),
            "erklaerung": erklaerung,
        })
        FRAGEN_DATEI.write_text(json.dumps(katalog, ensure_ascii=False, indent=2), encoding="utf-8")
    except (OSError, ValueError, KeyError):
        s.ed_meldung = ("nok", "Die Frage konnte nicht in fragen.json gespeichert werden.")
        return

    lade_fragen.clear()
    for schluessel in ("ed_frage", "ed_o0", "ed_o1", "ed_o2", "ed_o3", "ed_erk"):
        s[schluessel] = ""
    s.ed_richtig = 0
    s.ed_meldung = ("ok", f"Gespeichert! Die Frage ist jetzt in Lernfeld {s.ed_lf} enthalten.")


# ---------------------------------------------------------------------------
# Bausteine
# ---------------------------------------------------------------------------
def hero(eyebrow: str, titel: str, untertitel: str = "", icon: str = "🎓") -> None:
    logo = f'<div class="ico">{icon}</div>'
    if LOGO_DATEI.exists():
        b64 = base64.b64encode(LOGO_DATEI.read_bytes()).decode()
        logo = f'<img src="data:image/png;base64,{b64}" style="height:34px">'
    md(f'<div class="hero"><div><div class="eyebrow">{esc(eyebrow)}</div>'
       f'<div class="t">{esc(titel)}</div><div class="s">{esc(untertitel)}</div></div>{logo}</div>')


def kopfleiste() -> None:
    _, rechts = st.columns([4, 1])
    with rechts:
        st.button("☀️ Hell" if st.session_state.dark else "🌙 Dunkel", key="theme",
                  on_click=wechsle_theme, use_container_width=True)


def fortschritt(erledigt: int, gesamt: int, links: str, rechts: str = "") -> None:
    prozent = round(erledigt / gesamt * 100)
    md(f'<div class="meta"><span>{esc(links)}</span><span>{rechts}</span></div>'
       f'<div class="bar"><div style="width:{prozent}%"></div></div>')


def sitzungstitel(daten: dict):
    s = st.session_state
    if s.lf_key == "alle":
        if s.modus == "pruefung":
            return "Prüfungssimulation", "Alle Lernfelder, zufällig gemischt"
        return "Alle Lernfelder", "Zufällig gemischt"
    if s.lf_key == "schwach":
        return "Schwächentraining", "Fragen, die du zuletzt falsch beantwortet hast"
    return f"Lernfeld {s.lf_key}", daten[s.lf_key]["titel"]


def sidebar() -> None:
    s = st.session_state
    with st.sidebar:
        md('<div style="font-size:2.2rem">🎓</div><div class="tag">KI-QuizMaster</div>'
           '<div style="font-size:1.2rem;font-weight:700;margin-bottom:12px">Lernfelder 1–4</div>')
        for label, seite in (("🏠  Startseite", "start"), ("📊  Statistik", "statistik"), ("✏️  Eigene Fragen", "editor")):
            st.button(label, key=f"nav_{seite}", type="primary" if s.seite == seite else "secondary",
                      on_click=gehe, args=(seite,), use_container_width=True)
        st.divider()
        st.caption("🛠️ Ausbildung IT-Berufe · Vorbereitung auf die Zwischenprüfung · Version 3.1")


# ---------------------------------------------------------------------------
# Seiten
# ---------------------------------------------------------------------------
def zeige_start(daten: dict) -> None:
    s = st.session_state
    gesamt = sum(len(lf["fragen"]) for lf in daten.values())
    hero("Ausbildung IT-Berufe · Zwischenprüfung", "KI-QuizMaster LF 1–4",
         f"📚 {gesamt} Fragen · 🧠 Quiz · 🗂️ Karteikarten · 🎯 Prüfung · 📊 Statistik", "🎓")

    md('<div class="sec"><span>🔢</span><span class="tag">Fragen pro Durchgang</span></div>')
    spalten = st.columns([1, 1, 1, 5])
    for spalte, (label, wert) in zip(spalten, (("5", 5), ("10", 10), ("Alle", 0))):
        with spalte:
            st.button(label, key=f"anz_{wert}", type="primary" if s.anzahl == wert else "secondary",
                      on_click=setze_anzahl, args=(wert,), use_container_width=True)
    md('<div class="sec"><span>📚</span><span class="tag">Lernfelder</span></div>')

    eintraege = list(daten.items())
    for zeile in range(0, len(eintraege), 2):
        spalten = st.columns(2, gap="medium")
        for spalte, (key, lf) in zip(spalten, eintraege[zeile:zeile + 2]):
            with spalte:
                stat = s.lernstand["lf"].get(key)
                info = f"Bestwert {stat['bestes']} %" if stat else "Noch nicht bearbeitet"
                sicher, anzahl = lf_beherrschung(lf)
                prozent = round(sicher / anzahl * 100) if anzahl else 0
                md(f'<div class="card"><div class="kopf"><span class="nr">LF {esc(key)}</span>'
                   f'<span class="ic">{lf_icon(key)}</span></div>'
                   f'<div class="ti">{esc(lf["titel"])}</div>'
                   f'<div class="me">📝 {anzahl} Fragen · 🏆 {esc(info)}</div>'
                   f'<div class="bar" style="margin-top:12px"><div style="width:{prozent}%"></div></div>'
                   f'<div class="me" style="margin-top:4px">✅ Sicher gewusst: {sicher} / {anzahl}</div></div>')
                b1, b2 = st.columns(2)
                with b1:
                    st.button("▶️ Quiz", key=f"q_{key}", type="primary", on_click=starte,
                              args=("quiz", key, daten), use_container_width=True)
                with b2:
                    st.button("🗂️ Karten", key=f"k_{key}", on_click=starte,
                              args=("karten", key, daten), use_container_width=True)
        md('<div style="height:10px"></div>')

    md('<div class="sec"><span>🎯</span><span class="tag">Prüfung & Wiederholung</span></div>')
    spalte_a, spalte_b = st.columns(2, gap="medium")
    with spalte_a:
        stat = s.lernstand["lf"].get("alle")
        info = f"Bestwert {stat['bestes']} %" if stat else "Noch nicht absolviert"
        md(f'<div class="card dark"><div class="kopf"><span class="nr">Prüfungsmodus</span><span class="ic">🎯</span></div>'
           f'<div class="ti">Prüfungssimulation</div>'
           f'<div class="me">📝 {PRUEFUNG_FRAGEN} Fragen · 🙈 kein Feedback bis zum Ende · '
           f'🏅 Note nach IHK-Schlüssel<br>🏆 {esc(info)}</div></div>')
        st.button("🚀 Simulation starten", key="q_pruefung", type="primary", on_click=starte,
                  args=("pruefung", "alle", daten), use_container_width=True)
    with spalte_b:
        offen = len(schwache_fragen(daten))
        text = (f"{offen} Fragen warten auf Wiederholung" if offen
                else "Noch keine Fehler – falsch beantwortete Fragen erscheinen hier automatisch")
        md(f'<div class="card"><div class="kopf"><span class="nr">Training</span><span class="ic">💪</span></div>'
           f'<div class="ti">Schwächentraining</div>'
           f'<div class="me">{esc(text)}</div></div>')
        st.button("💪 Training starten", key="q_schwach", type="primary", disabled=offen == 0,
                  on_click=starte, args=("quiz", "schwach", daten), use_container_width=True)

    md('<div style="height:10px"></div>')
    spalte_c, spalte_d = st.columns(2, gap="medium")
    with spalte_c:
        st.button("🔀 Quiz: alle Lernfelder gemischt", key="q_alle", on_click=starte,
                  args=("quiz", "alle", daten), use_container_width=True)
    with spalte_d:
        st.button("🃏 Karteikarten: alle Lernfelder", key="k_alle", on_click=starte,
                  args=("karten", "alle", daten), use_container_width=True)


def zeige_quiz(daten: dict) -> None:
    s = st.session_state
    frage = s.fragen[s.index]
    titel, untertitel = sitzungstitel(daten)
    pruefung = s.modus == "pruefung"
    hero("Prüfungsmodus · Auswertung am Ende" if pruefung else "Quiz", titel, untertitel,
         "🎯" if pruefung else lf_icon(s.lf_key) if s.lf_key in LF_ICONS else "🧠")

    rechts = ""
    if not pruefung:
        rechts = f"⭐ Punkte: <b>{s.score}</b>" + (f" · Serie 🔥 {s.serie}" if s.serie >= 2 else "")
    fortschritt(s.index + (1 if s.geprueft else 0), len(s.fragen),
                f"Frage {s.index + 1} von {len(s.fragen)}", rechts)
    md(f'<div class="frage"><div class="tag">{lf_icon(frage["lf"])} Lernfeld {esc(frage["lf"])}</div>'
       f'<div class="q">{esc(frage["frage"])}</div></div>')

    if not s.geprueft:
        with st.container(key="opts"):
            for n, option in enumerate(frage["optionen_gemischt"]):
                if option in s.ausgeblendet:
                    continue
                st.button(f"{BUCHSTABEN[n]})  {option}", key=f"opt_{s.durchlauf}_{s.index}_{n}",
                          on_click=antworte, args=(option,), use_container_width=True)
        if not pruefung:
            kann = s.joker > 0 and not s.ausgeblendet and len(frage["optionen_gemischt"]) >= 4
            st.button(f"🎲 50:50-Joker · {'🃏' * s.joker or 'keiner'} übrig", key=f"joker_{s.durchlauf}_{s.index}",
                      on_click=nutze_joker, disabled=not kann)
        return

    for n, option in enumerate(frage["optionen_gemischt"]):
        if option == frage["richtig_text"]:
            klasse, marke = "ok", "✓"
        elif option == s.gewaehlt:
            klasse, marke = "nok", "✗"
        else:
            klasse, marke = "dim", ""
        md(f'<div class="opt {klasse}"><div class="b">{BUCHSTABEN[n]}</div>'
           f'<div>{esc(option)}</div><div class="m">{marke}</div></div>')

    if s.gewaehlt == frage["richtig_text"]:
        md(f'<div class="feedback ok">✅ Richtig! {random.choice(["🎉", "👏", "💯", "🚀", "🙌"])}</div>')
    else:
        md('<div class="feedback nok">❌ Leider falsch – kein Problem, die Frage kommt ins Schwächentraining.</div>')
    md(f'<div class="erk"><b>💡 Erklärung:</b> {esc(frage["erklaerung"])}</div>')

    letzte = s.index + 1 >= len(s.fragen)
    st.button("🏁 Ergebnis anzeigen" if letzte else "Nächste Frage ➡️", type="primary", on_click=weiter)


def zeige_karte(daten: dict) -> None:
    s = st.session_state
    karte = s.fragen[s.index]
    titel, untertitel = sitzungstitel(daten)
    hero("Karteikarten", titel, untertitel, "🗂️")
    fortschritt(s.index, len(s.fragen), f"Karte {s.index + 1} von {len(s.fragen)}",
                f"✅ Gewusst: <b>{s.score}</b>")
    md(f'<div class="frage"><div class="tag">{lf_icon(karte["lf"])} Lernfeld {esc(karte["lf"])} · ❓ Frage</div>'
       f'<div class="q">{esc(karte["frage"])}</div></div>')

    if not s.geprueft:
        st.button("👀 Antwort aufdecken", type="primary", on_click=decke_auf, use_container_width=True)
        return

    md(f'<div class="frage rueck"><div class="tag">💡 Antwort</div>'
       f'<div class="q">{esc(karte["richtig_text"])}</div></div>')
    md(f'<div class="erk">{esc(karte["erklaerung"])}</div>')
    spalte1, spalte2 = st.columns(2)
    with spalte1:
        st.button("🔁 Nochmal üben", on_click=bewerte_karte, args=(False,), use_container_width=True)
    with spalte2:
        st.button("✅ Gewusst", type="primary", on_click=bewerte_karte, args=(True,), use_container_width=True)


def zeige_ende(daten: dict) -> None:
    s = st.session_state
    gesamt = len(s.fragen)
    prozent = round(s.score / gesamt * 100)
    titel, untertitel = sitzungstitel(daten)
    hero({"quiz": "Ergebnis", "pruefung": "Prüfungsergebnis", "karten": "Karteikarten abgeschlossen"}[s.modus],
         titel, untertitel, "🏆" if prozent >= 70 else "📈")

    md(f'<div class="ring" style="background:conic-gradient(var(--petrol) {prozent}%, var(--rand) 0)">'
       f'<div class="ring-i"><b>{s.score} / {gesamt}</b><span>{prozent} %</span></div></div>')

    kpis = [("⏱️", zeit_text(s.dauer), "Dauer")]
    if s.modus != "karten":
        note, note_text = ihk_note(prozent)
        kpis.insert(0, ("🏅", note, f"Note · {note_text} (IHK-Schlüssel)"))
        kpis.append(("🔥", str(s.beste_serie), "Beste Serie"))
        kpis.append(("❌", str(len(s.fehler)), "Fehler"))
    md('<div class="kpis">' + "".join(f'<div class="kpi"><span class="i">{i}</span><b>{esc(w)}</b><span>{esc(b)}</span></div>'
                                     for i, w, b in kpis) + '</div>')

    if prozent >= 90:
        meldung = "🏆 Hervorragend – du bist bestens vorbereitet!"
    elif prozent >= 70:
        meldung = "👍 Gut gemacht – mit etwas Wiederholung wird es noch besser."
    elif prozent >= 50:
        meldung = "📚 Solide Basis – schau dir die markierten Fragen noch einmal an."
    else:
        meldung = "💪 Hier lohnt sich eine Wiederholung – das Schwächentraining hilft dir dabei."
    if s.modus == "karten":
        meldung = f"{s.score} von {gesamt} Karten gewusst. " + meldung
    md(f'<div class="erk" style="text-align:center"><b>{esc(meldung)}</b></div>')
    if prozent >= 90 and s.modus != "karten":
        st.balloons()

    if s.fehler:
        with st.expander(f"📌 Zu wiederholen ({len(s.fehler)})", expanded=s.modus == "pruefung"):
            for f in s.fehler:
                eigene = f'<div>❌ Deine Antwort: {esc(f["gewaehlt"])}</div>' if f.get("gewaehlt") else ""
                md(f'<div class="srow"><div class="k">{esc(f["frage"])}</div>{eigene}'
                   f'<div>✅ Richtig: {esc(f["richtig_text"])}</div>'
                   f'<div class="me" style="margin-top:6px">💡 {esc(f["erklaerung"])}</div></div>')

    spalte1, spalte2, spalte3 = st.columns(3)
    with spalte1:
        if s.fehler:
            wiederhol_modus = "quiz" if s.modus == "pruefung" else s.modus
            st.button("🔁 Fehler wiederholen", type="primary", on_click=starte, use_container_width=True,
                      args=(wiederhol_modus, s.lf_key, daten, list(s.fehler), False))
    with spalte2:
        st.button("🔄 Nochmal", on_click=starte, args=(s.modus, s.lf_key, daten), use_container_width=True)
    with spalte3:
        st.button("🏠 Startseite", on_click=gehe, args=("start",), use_container_width=True)
    if s.fehler:
        st.download_button("📥 Fehlerliste als Lernzettel (.txt)", data=fehler_text(s.fehler),
                           file_name="lernzettel_fehler.txt", mime="text/plain")


def zeige_statistik(daten: dict) -> None:
    s = st.session_state
    hero("Lernstatistik", "Dein Fortschritt", "Bestwerte, Lernstand und deine schwächsten Fragen", "📊")

    alle = [(k, f) for k, lf in daten.items() for f in lf["fragen"]]
    gelernt = s.lernstand["fragen"]
    durchgaenge = sum(e.get("versuche", 0) for e in s.lernstand["lf"].values())
    sicher = sum(1 for _, f in alle if ist_sicher(gelernt.get(frage_id(f["frage"]))))
    bearbeitet = sum(1 for _, f in alle if frage_id(f["frage"]) in gelernt)
    md('<div class="kpis">'
       f'<div class="kpi"><span class="i">🔁</span><b>{durchgaenge}</b><span>Quiz-Durchgänge</span></div>'
       f'<div class="kpi"><span class="i">📝</span><b>{bearbeitet} / {len(alle)}</b><span>Fragen bearbeitet</span></div>'
       f'<div class="kpi"><span class="i">✅</span><b>{sicher} / {len(alle)}</b><span>Sicher gewusst</span></div></div>')

    zeilen = [(f"Lernfeld {k}", lf["titel"], k, lf) for k, lf in daten.items()]
    for name, titel, key, lf in zeilen:
        eintrag = s.lernstand["lf"].get(key)
        sicher_lf, anzahl = lf_beherrschung(lf)
        if eintrag:
            detail = (f'Bestwert {eintrag["bestes"]} % · letzter Durchgang {eintrag["letztes"]} % · '
                      f'{eintrag["versuche"]} Durchgänge')
        else:
            detail = "🆕 Noch kein Quiz absolviert"
        prozent = round(sicher_lf / anzahl * 100) if anzahl else 0
        md(f'<div class="srow"><div class="k"><span class="ic">{lf_icon(key)}</span>{esc(name)} – {esc(titel)}</div>'
           f'<div class="me" style="margin-bottom:8px">{esc(detail)} · ✅ Sicher gewusst: {sicher_lf} / {anzahl}</div>'
           f'<div class="bar"><div style="width:{prozent}%"></div></div></div>')

    stat = s.lernstand["lf"].get("alle")
    if stat:
        md(f'<div class="srow"><div class="k"><span class="ic">🎯</span>Prüfungssimulation / gemischte Quiz</div>'
           f'<div class="me">Bestwert {stat["bestes"]} % · letzter Durchgang {stat["letztes"]} % · '
           f'{stat["versuche"]} Durchgänge</div></div>')

    suche = {frage_id(f["frage"]): (k, f["frage"]) for k, f in alle}
    schwach = sorted(((e.get("f", 0), i) for i, e in gelernt.items() if e.get("f") and i in suche),
                     reverse=True)[:5]
    if schwach:
        md('<div class="sec"><span>⚠️</span><span class="tag">Deine schwächsten Fragen</span></div>')
        for fehler_anzahl, i in schwach:
            k, text = suche[i]
            e = gelernt[i]
            md(f'<div class="srow"><div class="k">{esc(text)}</div>'
               f'<div class="me"><span class="chip">{lf_icon(k)} LF {esc(k)}</span>❌ {fehler_anzahl}× falsch · ✅ {e.get("r", 0)}× richtig</div></div>')

    if not s.get("reset_frage"):
        st.button("🗑️ Lernstand zurücksetzen", on_click=setze, args=("reset_frage", True))
    else:
        md('<div class="feedback nok">⚠️ Wirklich den gesamten Lernstand löschen? '
           'Das kann nicht rückgängig gemacht werden.</div>')
        ja, nein = st.columns(2)
        with ja:
            st.button("🗑️ Ja, alles löschen", type="primary", on_click=setze_lernstand_zurueck,
                      use_container_width=True)
        with nein:
            st.button("↩️ Abbrechen", on_click=setze, args=("reset_frage", False), use_container_width=True)


def zeige_editor(daten: dict) -> None:
    s = st.session_state
    hero("Eigene Fragen", "Fragen hinzufügen",
         "Ergänze den Katalog mit Inhalten aus deinen Lernzetteln – gespeichert in fragen.json", "✏️")

    md('<div class="sec"><span>📚</span><span class="tag">Lernfeld</span></div>')
    for spalte, key in zip(st.columns(len(daten)), daten.keys()):
        with spalte:
            st.button(f"{lf_icon(key)} LF {key}", key=f"edlf_{key}", type="primary" if s.ed_lf == key else "secondary",
                      on_click=setze, args=("ed_lf", key), use_container_width=True)

    st.text_area("❓ Frage", key="ed_frage", height=90)
    for n in range(4):
        st.text_input(f"Antwort {BUCHSTABEN[n]}" + (" (optional)" if n >= 2 else ""), key=f"ed_o{n}")

    md('<div class="sec"><span>✅</span><span class="tag">Richtige Antwort</span></div>')
    for spalte, n in zip(st.columns(4), range(4)):
        with spalte:
            st.button(BUCHSTABEN[n], key=f"edr_{n}", type="primary" if s.ed_richtig == n else "secondary",
                      on_click=setze, args=("ed_richtig", n), use_container_width=True)

    st.text_area("💡 Erklärung (wird nach der Antwort angezeigt)", key="ed_erk", height=90)
    st.button("💾 Frage speichern", type="primary", on_click=speichere_frage)

    if s.ed_meldung:
        art, text = s.ed_meldung
        md(f'<div class="feedback {art}">{esc(text)}</div>')
    md('<div class="me" style="color:var(--muted);font-size:.85rem">💡 Tipp: Sichere dir vorher eine Kopie '
       'deiner fragen.json, wenn du viele Fragen ergänzt.</div>')


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main() -> None:
    init_state()
    md(f"<style>{css_fuer(st.session_state.dark)}</style>")

    if not FRAGEN_DATEI.exists():
        st.error(f"Fragendatei nicht gefunden: {FRAGEN_DATEI.name} muss im selben Ordner wie dieses Skript liegen.")
        st.stop()

    daten = lade_fragen(str(FRAGEN_DATEI))
    sidebar()
    kopfleiste()

    seite = st.session_state.seite
    if seite == "lauf":
        zeige_karte(daten) if st.session_state.modus == "karten" else zeige_quiz(daten)
    elif seite == "ende":
        zeige_ende(daten)
    elif seite == "statistik":
        zeige_statistik(daten)
    elif seite == "editor":
        zeige_editor(daten)
    else:
        zeige_start(daten)


main()
