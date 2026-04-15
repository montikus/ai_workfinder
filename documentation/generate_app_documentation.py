from __future__ import annotations

from datetime import date
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.graphics.shapes import Circle, Drawing, Ellipse, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DOC_DIR = ROOT / "documentation"
TEST_REPORT_PDF = DOC_DIR / "AI Workfinder raport z testow.pdf"
OUTPUT_PDF = DOC_DIR / "AI Workfinder dokumentacja aplikacji.pdf"
TMP_MAIN_PDF = DOC_DIR / "_ai_workfinder_main_documentation.pdf"

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", FONT_BOLD))


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=base["Title"],
            fontName="DejaVuSans-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=18,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleCustom",
            parent=base["Heading2"],
            fontName="DejaVuSans",
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "H1Custom",
            parent=base["Heading1"],
            fontName="DejaVuSans-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=10,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "H2Custom",
            parent=base["Heading2"],
            fontName="DejaVuSans-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontName="DejaVuSans",
            fontSize=9.5,
            leading=13.5,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "body_left": ParagraphStyle(
            "BodyLeftCustom",
            parent=base["BodyText"],
            fontName="DejaVuSans",
            fontSize=9.5,
            leading=13.5,
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "bullet": ParagraphStyle(
            "BulletCustom",
            parent=base["BodyText"],
            fontName="DejaVuSans",
            fontSize=9.5,
            leading=13.5,
            leftIndent=14,
            firstLineIndent=-8,
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "SmallCustom",
            parent=base["BodyText"],
            fontName="DejaVuSans",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "CodeCustom",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            backColor=colors.HexColor("#f8fafc"),
            borderPadding=6,
            borderWidth=0.5,
            borderColor=colors.HexColor("#cbd5e1"),
        ),
    }


def p(text: str, style):
    return Paragraph(text, style)


def bullet(text: str, st):
    return Paragraph(f"• {text}", st)


def table(data, widths=None):
    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "DejaVuSans"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return tbl


def add_arrow(d: Drawing, x1, y1, x2, y2, color=colors.HexColor("#334155")):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.2))
    if x2 == x1 and y2 == y1:
        return
    if abs(x2 - x1) >= abs(y2 - y1):
        if x2 > x1:
            d.add(Line(x2, y2, x2 - 7, y2 + 3, strokeColor=color, strokeWidth=1.2))
            d.add(Line(x2, y2, x2 - 7, y2 - 3, strokeColor=color, strokeWidth=1.2))
        else:
            d.add(Line(x2, y2, x2 + 7, y2 + 3, strokeColor=color, strokeWidth=1.2))
            d.add(Line(x2, y2, x2 + 7, y2 - 3, strokeColor=color, strokeWidth=1.2))
    else:
        if y2 > y1:
            d.add(Line(x2, y2, x2 - 3, y2 - 7, strokeColor=color, strokeWidth=1.2))
            d.add(Line(x2, y2, x2 + 3, y2 - 7, strokeColor=color, strokeWidth=1.2))
        else:
            d.add(Line(x2, y2, x2 - 3, y2 + 7, strokeColor=color, strokeWidth=1.2))
            d.add(Line(x2, y2, x2 + 3, y2 + 7, strokeColor=color, strokeWidth=1.2))


def add_box(d: Drawing, x, y, w, h, title, lines, fill="#eff6ff"):
    d.add(Rect(x, y, w, h, strokeColor=colors.HexColor("#1d4ed8"), fillColor=colors.HexColor(fill), strokeWidth=1.2, rx=6, ry=6))
    d.add(Rect(x, y + h - 16, w, 16, strokeColor=colors.HexColor("#1d4ed8"), fillColor=colors.HexColor("#bfdbfe"), strokeWidth=1.0, rx=6, ry=6))
    d.add(String(x + 5, y + h - 12, title, fontName="DejaVuSans-Bold", fontSize=8.5, fillColor=colors.HexColor("#0f172a")))
    yy = y + h - 29
    for line in lines:
        d.add(String(x + 5, yy, line, fontName="DejaVuSans", fontSize=7.2, fillColor=colors.HexColor("#0f172a")))
        yy -= 9


def add_actor(d: Drawing, x, y, label):
    d.add(Circle(x, y + 26, 10, strokeColor=colors.black))
    d.add(Line(x, y + 16, x, y - 6, strokeColor=colors.black))
    d.add(Line(x - 12, y + 8, x + 12, y + 8, strokeColor=colors.black))
    d.add(Line(x, y - 6, x - 12, y - 22, strokeColor=colors.black))
    d.add(Line(x, y - 6, x + 12, y - 22, strokeColor=colors.black))
    d.add(String(x - 18, y - 34, label, fontName="DejaVuSans", fontSize=8))


def use_case_diagram():
    d = Drawing(520, 250)
    d.add(Rect(90, 20, 360, 200, strokeColor=colors.HexColor("#64748b"), fillColor=None, strokeDashArray=[4, 3]))
    d.add(String(220, 225, "System AI Workfinder", fontName="DejaVuSans-Bold", fontSize=10))

    add_actor(d, 40, 150, "Gość")
    add_actor(d, 490, 150, "Użytkownik")

    ovals = [
        (170, 165, "Rejestracja"),
        (170, 115, "Logowanie"),
        (300, 175, "Edycja profilu"),
        (300, 130, "Upload CV"),
        (300, 85, "Uruchomienie\nwyszukiwania"),
        (410, 170, "Przegląd ofert"),
        (410, 120, "Podgląd aplikacji"),
        (410, 70, "Podgląd statusu\n i logów"),
    ]
    for x, y, label in ovals:
        d.add(Ellipse(x, y, 58, 22, strokeColor=colors.HexColor("#0f766e"), fillColor=colors.HexColor("#ccfbf1")))
        parts = label.split("\n")
        if len(parts) == 1:
            d.add(String(x - 28, y - 2, parts[0], fontName="DejaVuSans", fontSize=7.2))
        else:
            d.add(String(x - 32, y + 2, parts[0], fontName="DejaVuSans", fontSize=7.2))
            d.add(String(x - 26, y - 8, parts[1], fontName="DejaVuSans", fontSize=7.2))

    for target in [(112, 165), (112, 115)]:
        add_arrow(d, 52, 158, target[0], target[1])
    for target in [(242, 175), (242, 130), (242, 85), (352, 170), (352, 120), (352, 70)]:
        add_arrow(d, 438, 158, target[0], target[1])
    return d


def class_diagram():
    d = Drawing(520, 300)
    add_box(d, 20, 190, 145, 90, "SchematUzytkownik", ["id: str", "email: EmailStr", "name: str?", "resume_filename: str?", "gmail_connected: bool"])
    add_box(d, 190, 190, 155, 90, "RepozytoriumUzytkownikow", ["znajdz_po_emailu()", "znajdz_po_id()", "utworz_pusty_profil()", "zaktualizuj()"], fill="#eef2ff")
    add_box(d, 370, 190, 130, 90, "SearchState", ["status: str", "jobs_found: int", "events: list", "jobs: list"], fill="#f5f3ff")
    add_box(d, 20, 65, 145, 95, "Search Routes", ["/api/start_search", "/api/search_status", "/api/jobs", "/api/search_stream"], fill="#fef3c7")
    add_box(d, 190, 65, 155, 95, "RunInput / RunSummary", ["specialization", "full_name", "resume_path", "apply_results", "llm_trace"], fill="#ecfccb")
    add_box(d, 370, 65, 130, 95, "JobPosting / ApplyHttpResult", ["url", "title", "raw_snippet", "status_code", "error"], fill="#fee2e2")

    add_arrow(d, 165, 235, 190, 235)
    add_arrow(d, 97, 160, 97, 190)
    add_arrow(d, 345, 235, 370, 235)
    add_arrow(d, 165, 110, 190, 110)
    add_arrow(d, 345, 110, 370, 110)
    add_arrow(d, 267, 160, 267, 190)
    add_arrow(d, 430, 160, 430, 190)
    return d


def data_model_diagram():
    d = Drawing(520, 270)
    add_box(
        d,
        20,
        145,
        220,
        105,
        "MongoDB: users",
        [
            "_id: ObjectId",
            "email: str (unique)",
            "password_hash: str",
            "name, phone, location",
            "job_preferences_text",
            "gmail_connected, resume_filename",
        ],
        fill="#eff6ff",
    )
    add_box(
        d,
        280,
        145,
        220,
        105,
        "Pamięć procesu: _states[user_id]",
        [
            "status, started_at, finished_at",
            "jobs_found, attempted_apply, applied_ok",
            "jobs: list[dict]",
            "summary: dict",
            "events: list[dict]",
        ],
        fill="#fef3c7",
    )
    add_box(
        d,
        20,
        25,
        220,
        85,
        "Pliki lokalne",
        [
            "backend/uploads/<user_id>/<filename>",
            "config.json z parametrami biegu AI",
            "CV jest referencjonowane przez resume_filename",
        ],
        fill="#ecfccb",
    )
    add_box(
        d,
        280,
        25,
        220,
        85,
        "Dane pośrednie AI",
        [
            "jobs -> one_click_jobs -> apply_results",
            "WorkflowState i RunSummary",
            "wyniki nie są trwałe w bazie MongoDB",
        ],
        fill="#fee2e2",
    )
    add_arrow(d, 130, 110, 130, 145)
    add_arrow(d, 390, 110, 390, 145)
    add_arrow(d, 240, 197, 280, 197)
    return d


def architecture_diagram():
    d = Drawing(520, 300)
    add_box(d, 10, 205, 100, 65, "Użytkownik", ["przeglądarka", "interakcja z UI"], fill="#f8fafc")
    add_box(d, 130, 205, 125, 65, "Frontend React", ["App / Routes", "AuthContext / I18n", "axios client"], fill="#eff6ff")
    add_box(d, 275, 205, 125, 65, "FastAPI", ["auth / profile", "search / applications", "JWT + CORS"], fill="#eef2ff")
    add_box(d, 420, 205, 90, 65, "MongoDB", ["kolekcja users"], fill="#ecfccb")
    add_box(d, 130, 95, 125, 70, "SSE + Status", ["search_state", "event log", "wyniki wyszukiwania"], fill="#fef3c7")
    add_box(d, 275, 95, 125, 70, "AI Runner", ["LangGraph", "search -> filter -> apply"], fill="#fee2e2")
    add_box(d, 420, 95, 90, 70, "Pliki", ["uploads/", "config.json"], fill="#f5f3ff")
    add_box(d, 275, 10, 235, 55, "Usługi zewnętrzne", ["JustJoin.it, OpenAI-compatible API, HTTP apply endpoints"], fill="#fff7ed")

    add_arrow(d, 110, 237, 130, 237)
    add_arrow(d, 255, 237, 275, 237)
    add_arrow(d, 400, 237, 420, 237)
    add_arrow(d, 192, 205, 192, 165)
    add_arrow(d, 337, 205, 337, 165)
    add_arrow(d, 400, 130, 420, 130)
    add_arrow(d, 337, 95, 337, 65)
    add_arrow(d, 255, 130, 275, 130)
    return d


def ui_mockups():
    d = Drawing(520, 340)
    boxes = [
        (20, 185, "Login", ["Email", "Hasło", "[ Zaloguj ]", "Link: Rejestracja"]),
        (270, 185, "Dashboard", ["specjalizacja / lokalizacja", "limit / max_apply", "status + statystyki", "log stream + lista ofert"]),
        (20, 20, "Profil", ["imię, telefon, lokalizacja", "preferencje pracy", "upload CV", "[ Zapisz ]"]),
        (270, 20, "Applications", ["lista wysłanych aplikacji", "firma, data, status", "link do ogłoszenia"]),
    ]
    for x, y, title, lines in boxes:
        add_box(d, x, y, 220, 125, title, lines, fill="#f8fafc")
        d.add(Rect(x + 15, y + 55, 190, 12, strokeColor=colors.HexColor("#94a3b8"), fillColor=None))
        d.add(Rect(x + 15, y + 35, 190, 12, strokeColor=colors.HexColor("#94a3b8"), fillColor=None))
        d.add(Rect(x + 15, y + 12, 70, 14, strokeColor=colors.HexColor("#1d4ed8"), fillColor=colors.HexColor("#dbeafe")))
    return d


def add_page_number(canvas, doc):
    canvas.setFont("DejaVuSans", 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawRightString(A4[0] - 1.8 * cm, 1.2 * cm, str(doc.page))


def build_main_pdf():
    register_fonts()
    st = styles()
    doc = SimpleDocTemplate(
        str(TMP_MAIN_PDF),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.6 * cm,
        title="AI Workfinder - dokumentacja aplikacji",
        author="Roman Nadkernychnyi, Maksim Pyanin, Bohdan Hrytsai, Maksym Stepaniuk",
    )

    story = []

    story.append(Spacer(1, 2.2 * cm))
    story.append(p("AI Workfinder", st["title"]))
    story.append(p("Dokumentacja aplikacji", st["title"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(p("Autorzy: Roman Nadkernychnyi, Maksim Pyanin, Bohdan Hrytsai, Maksym Stepaniuk", st["subtitle"]))
    story.append(p(f"Data opracowania: {date.today().strftime('%d.%m.%Y')}", st["subtitle"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        p(
            "Dokument opisuje problem biznesowy, analizę wymagań, projekt rozwiązania, architekturę, "
            "technologie, interfejsy, model danych oraz implementację aplikacji AI Workfinder. "
            "Ostatnią część dokumentu stanowi pełna, niezmodyfikowana treść raportu z testów.",
            st["body"],
        )
    )
    story.append(PageBreak())

    story.append(p("Spis treści", st["h1"]))
    toc = [
        "1. Wprowadzenie",
        "2. Opis problemu",
        "3. Projekt i analiza",
        "4. Implementacja",
        "5. Testy – pełna treść raportu z pliku „AI Workfinder raport z testow.pdf”",
    ]
    for item in toc:
        story.append(bullet(item, st["bullet"]))
    story.append(PageBreak())

    story.append(p("1. Wprowadzenie", st["h1"]))
    story.append(p("1.1. Cel dokumentu", st["h2"]))
    story.append(
        p(
            "Celem dokumentu jest przedstawienie kompletnej dokumentacji aplikacji AI Workfinder: "
            "zakresu produktu, założeń analitycznych, wymagań funkcjonalnych i pozafunkcjonalnych, "
            "modelu danych, interfejsów, architektury oraz implementacji. Dokument ma stanowić "
            "spójny opis rozwiązania na potrzeby projektu inżynierskiego/licencjackiego.",
            st["body"],
        )
    )
    story.append(p("1.2. Przyjęte zasady w dokumencie", st["h2"]))
    for item in [
        "Priorytet P0 oznacza wymaganie krytyczne, P1 ważne, P2 uzupełniające.",
        "Skróty: UI – interfejs użytkownika, API – interfejs programistyczny, JWT – token uwierzytelniający, LLM – model językowy, SSE – Server-Sent Events.",
        "Opis odnosi się do aktualnej implementacji znajdującej się w repozytorium projektu, a część testowa jest dołączona w postaci pełnego raportu PDF.",
    ]:
        story.append(bullet(item, st["bullet"]))
    story.append(p("1.3. Zakres produktu", st["h2"]))
    story.append(
        p(
            "AI Workfinder jest webową aplikacją wspierającą użytkownika indywidualnego w wyszukiwaniu pracy. "
            "System umożliwia rejestrację i logowanie, uzupełnienie profilu, dodanie CV, skonfigurowanie "
            "parametrów wyszukiwania, uruchomienie wieloagentowego pipeline’u AI oraz przegląd ofert i wysłanych aplikacji.",
            st["body"],
        )
    )
    story.append(p("1.4. Literatura", st["h2"]))
    lit_rows = [
        ["Pozycja", "Zakres wykorzystania"],
        ["Dokumentacja FastAPI", "warstwa API, routingi, zależności, modele wejścia/wyjścia"],
        ["Dokumentacja React i React Router", "warstwa SPA, routing, konteksty i ochrona tras"],
        ["Dokumentacja MongoDB / PyMongo", "trwałe przechowywanie danych użytkowników"],
        ["Dokumentacja LangChain / LangGraph", "orchestracja wieloagentowego pipeline’u AI"],
        ["Dokumentacja OpenAI-compatible API", "konfiguracja modelu LLM i połączenia z backendem AI"],
    ]
    story.append(table(lit_rows, [6.2 * cm, 9.3 * cm]))
    story.append(PageBreak())

    story.append(p("2. Opis problemu", st["h1"]))
    story.append(p("2.1. Dokładny opis problemu", st["h2"]))
    story.append(
        p(
            "Poszukiwanie pracy w branży IT wymaga równoległego przeglądania wielu ofert, oceny ich dopasowania "
            "do kompetencji użytkownika oraz ręcznego wypełniania formularzy aplikacyjnych. Proces jest czasochłonny, "
            "powtarzalny i podatny na pominięcie atrakcyjnych ofert. AI Workfinder ma ograniczyć ten koszt operacyjny "
            "poprzez centralizację profilu użytkownika oraz automatyzację wyszukiwania i części procesu aplikowania.",
            st["body"],
        )
    )
    story.append(
        p(
            "Projekt ma charakter proof of concept / prototypu systemu AI-assisted job search. Głównym celem było "
            "sprawdzenie możliwości zbudowania pipeline’u złożonego z wyszukiwania ofert, filtrowania 1-click apply "
            "oraz automatycznego wysyłania zgłoszeń na podstawie danych użytkownika i przesłanego CV.",
            st["body"],
        )
    )
    story.append(p("2.2. Porównanie dostępnych rozwiązań", st["h2"]))
    comparison_rows = [
        ["Kategoria", "Charakterystyka", "Ograniczenia względem AI Workfinder"],
        ["Ręczne przeglądanie portali pracy", "użytkownik sam filtruje i aplikuje", "wysoki nakład czasu, brak automatyzacji i centralnego statusu"],
        ["Klasyczne agregatory ofert", "prezentują oferty i podstawowe filtry", "zwykle nie automatyzują wysyłki aplikacji"],
        ["Rozszerzenia auto-apply / skrypty", "upraszczają pojedyncze formularze", "zwykle nie mają profilu użytkownika, dashboardu i pełnego pipeline’u"],
        ["AI Workfinder", "łączy profil, AI search, filtrację i monitoring procesu", "aktualnie ograniczony do jednego źródła ofert i do roli użytkownika indywidualnego"],
    ]
    story.append(table(comparison_rows, [3.5 * cm, 5.4 * cm, 6.6 * cm]))
    story.append(p("2.3. Możliwości zastosowania praktycznego", st["h2"]))
    for item in [
        "Wsparcie kandydata IT w szybkim reagowaniu na nowe oferty pracy.",
        "Automatyzacja rutynowych zadań: wyszukiwania, filtrowania i części procesu aplikowania.",
        "Budowa podstawy pod przyszły system rekomendacyjny lub platformę job-matching.",
        "Walidacja użyteczności integracji LLM + crawler + HTTP apply w jednym produkcie.",
    ]:
        story.append(bullet(item, st["bullet"]))
    story.append(PageBreak())

    story.append(p("3. Projekt i analiza", st["h1"]))
    story.append(p("3.1. Perspektywa produktu", st["h2"]))
    story.append(
        p(
            "Produkt jest aplikacją klient-serwer. Frontend w React udostępnia interfejs webowy, "
            "backend w FastAPI udostępnia REST API i SSE, a MongoDB przechowuje profile użytkowników. "
            "Wyszukiwanie i automatyczne aplikowanie realizowane są przez pipeline AI korzystający "
            "z modelu LLM oraz narzędzi HTTP/scrapingowych.",
            st["body"],
        )
    )
    story.append(p("3.2. Funkcje produktu", st["h2"]))
    for item in [
        "Rejestracja i logowanie użytkownika z użyciem JWT.",
        "Przechowywanie i edycja profilu użytkownika.",
        "Przesyłanie pliku CV do lokalnego magazynu plików backendu.",
        "Konfiguracja procesu wyszukiwania ofert pracy.",
        "Wielostopniowy pipeline AI: search -> filter -> apply.",
        "Strumieniowanie statusu oraz logów procesu wyszukiwania.",
        "Przegląd listy znalezionych ofert i listy wysłanych aplikacji.",
        "Dwujęzyczny interfejs użytkownika (PL/EN).",
    ]:
        story.append(bullet(item, st["bullet"]))
    story.append(p("3.3. Ograniczenia", st["h2"]))
    for item in [
        "Aktualna implementacja koncentruje się na użytkowniku indywidualnym; role firma/admin nie są zaimplementowane w interfejsie ani API.",
        "Źródłem ofert w aktualnej wersji jest portal justjoin.it.",
        "Status wyszukiwania i lista ofert są przechowywane w pamięci procesu, więc restart serwera czyści stan.",
        "Uruchomienie pipeline’u AI wymaga zewnętrznego endpointu kompatybilnego z OpenAI oraz poprawnej konfiguracji .env.",
        "Integracja Gmail jest obecna po stronie zależności i części frontendu, ale nie jest obecnie udostępniona jako kompletna ścieżka backendowa.",
    ]:
        story.append(bullet(item, st["bullet"]))
    story.append(p("3.4. Aktorzy i charakterystyka użytkowników", st["h2"]))
    actor_rows = [
        ["ID", "Nazwa", "Opis"],
        ["GUEST", "Gość", "Osoba niezalogowana. Może założyć konto lub zalogować się do systemu."],
        ["USER", "Użytkownik", "Osoba zalogowana. Zarządza profilem, CV, uruchamia wyszukiwanie i przegląda wyniki."],
        ["AI_PIPELINE", "Pipeline AI", "Aktor pomocniczy/techniczny odpowiedzialny za wykonanie procesu search-filter-apply."],
        ["EXTERNAL_SERVICES", "Usługi zewnętrzne", "JustJoin.it oraz endpoint LLM/OpenAI-compatible, od których zależy pełna realizacja procesu."],
    ]
    story.append(table(actor_rows, [2.4 * cm, 3.6 * cm, 9.4 * cm]))
    story.append(p("3.5. Obiekty biznesowe", st["h2"]))
    business_rows = [
        ["Obiekt", "Opis"],
        ["Profil użytkownika", "Dane osobowe i preferencje pracy użytkownika oraz referencja do przesłanego CV."],
        ["CV", "Plik PDF/DOC/DOCX przechowywany lokalnie po stronie backendu."],
        ["Oferta pracy", "Opis znalezionego ogłoszenia wraz z URL, źródłem i ewentualnym statusem aplikacji."],
        ["Aplikacja", "Wynik próby wysłania zgłoszenia do oferty, wraz ze statusem sukces/błąd."],
        ["Stan wyszukiwania", "Bieżący status procesu AI, liczniki, zdarzenia i lista wyników."],
        ["Konfiguracja uruchomienia", "Parametry biegu AI zapisywane do pliku config.json."],
    ]
    story.append(table(business_rows, [4.5 * cm, 10.9 * cm]))
    story.append(p("3.6. Wymagania funkcjonalne", st["h2"]))
    fr_rows = [
        ["ID", "Wymaganie", "Priorytet"],
        ["FR1", "System umożliwia rejestrację użytkownika za pomocą adresu e-mail i hasła.", "P0"],
        ["FR2", "System umożliwia logowanie i uwierzytelnianie żądań za pomocą JWT w nagłówku Authorization.", "P0"],
        ["FR3", "System udostępnia widok i edycję profilu użytkownika.", "P0"],
        ["FR4", "System pozwala przesłać i przechowywać plik CV użytkownika.", "P0"],
        ["FR5", "System pozwala uruchomić proces wyszukiwania ofert z parametrami: specjalizacja, poziom, lokalizacja, limity.", "P0"],
        ["FR6", "System wykonuje pipeline AI obejmujący wyszukiwanie, filtrację ofert 1-click oraz próbę automatycznego apply.", "P0"],
        ["FR7", "System udostępnia strumień statusu i logów procesu wyszukiwania w czasie zbliżonym do rzeczywistego.", "P1"],
        ["FR8", "System prezentuje listę znalezionych ofert pracy oraz listę wysłanych aplikacji.", "P0"],
        ["FR9", "Interfejs użytkownika umożliwia zmianę języka między polskim i angielskim.", "P1"],
        ["FR10", "System centralizuje komunikację frontend-backend przez wspólny klient HTTP.", "P1"],
    ]
    story.append(table(fr_rows, [1.4 * cm, 12.7 * cm, 1.3 * cm]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(use_case_diagram())
    story.append(p("Rysunek 1. Diagram przypadków użycia dla AI Workfinder.", st["small"]))
    story.append(p("3.7. Charakterystyka interfejsów", st["h2"]))
    ui_req_rows = [
        ["ID", "Wymaganie", "Priorytet"],
        ["UI1", "Interfejs musi działać w przeglądarce jako SPA z publicznymi i chronionymi trasami.", "P0"],
        ["UI2", "Formularze logowania, rejestracji i profilu muszą walidować obecność wymaganych danych.", "P0"],
        ["UI3", "UI musi prezentować stan procesu wyszukiwania, liczby znalezionych ofert i wyniki aplikowania.", "P0"],
        ["UI4", "UI powinno aktualizować log procesu bez pełnego odświeżania strony dzięki SSE.", "P1"],
        ["UI5", "UI powinno oferować lokalizację PL/EN i spójne nazewnictwo statusów.", "P1"],
    ]
    story.append(table(ui_req_rows, [1.4 * cm, 12.7 * cm, 1.3 * cm]))
    ext_rows = [
        ["Interfejs", "Opis"],
        ["REST API", "Endpointy /api/register, /api/login, /api/profile, /api/upload_resume, /api/start_search, /api/search_status, /api/jobs, /api/search_stream, /api/applications."],
        ["SSE", "Endpoint /api/search_stream do strumieniowania logów i statusu procesu AI."],
        ["MongoDB", "Połączenie backendu z bazą dokumentową przechowującą kolekcję users."],
        ["OpenAI-compatible API", "Backend AI wykorzystuje ChatOpenAI z parametrami z .env i config.json."],
        ["JustJoin.it / HTTP apply", "Crawler i automatyzacja apply korzystają z zewnętrznych endpointów portalu ofert pracy."],
    ]
    story.append(table(ext_rows, [4.2 * cm, 11.2 * cm]))
    story.append(p("3.8. Wymagania pozafunkcjonalne", st["h2"]))
    nfr_rows = [
        ["ID", "Nazwa", "Opis", "Priorytet"],
        ["NFR1", "Bezpieczeństwo", "Hasła nie mogą być przechowywane jako tekst jawny; system stosuje hash PBKDF2 oraz JWT.", "P0"],
        ["NFR2", "Integralność danych", "Adres e-mail użytkownika musi być unikalny w bazie MongoDB.", "P0"],
        ["NFR3", "Użyteczność", "Interfejs powinien być prosty, formularzowy i czytelny dla użytkownika nietechnicznego.", "P1"],
        ["NFR4", "Obsługa błędów", "System powinien zwracać przewidywalne komunikaty walidacyjne i błędy startu wyszukiwania.", "P0"],
        ["NFR5", "Rozszerzalność", "Architektura ma umożliwiać dodanie kolejnych źródeł ofert i kolejnych agentów.", "P1"],
        ["NFR6", "Przenośność", "Aplikacja powinna działać lokalnie na środowisku developerskim z backendem FastAPI, frontendem Vite i MongoDB.", "P1"],
    ]
    story.append(table(nfr_rows, [1.4 * cm, 2.8 * cm, 10.4 * cm, 1.2 * cm]))
    story.append(PageBreak())

    story.append(p("3.9. Diagram klas", st["h2"]))
    story.append(
        p(
            "Poniższy diagram pokazuje kluczowe klasy i modele danych biorące udział w działaniu aplikacji. "
            "Uwzględniono zarówno warstwę domenową backendu, jak i struktury używane w pipeline’ie AI.",
            st["body"],
        )
    )
    story.append(class_diagram())
    story.append(p("Rysunek 2. Uproszczony diagram klas i modeli systemu.", st["small"]))
    story.append(p("3.10. Model danych i organizacja przechowywania danych", st["h2"]))
    story.append(
        p(
            "Projekt nie korzysta z relacyjnej bazy danych. Dane trwałe przechowywane są w dokumentowej bazie MongoDB, "
            "natomiast dane operacyjne procesu wyszukiwania są utrzymywane w pamięci aplikacji. CV przechowywane jest "
            "w systemie plików backendu, a konfiguracja pojedynczego uruchomienia pipeline’u w pliku config.json.",
            st["body"],
        )
    )
    story.append(data_model_diagram())
    story.append(p("Rysunek 3. Model danych trwałych i danych tymczasowych.", st["small"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Preformatted(
            """Przykładowy dokument użytkownika (MongoDB / users):
{
  "_id": "ObjectId(...)",
  "email": "user@example.com",
  "password_hash": "<hash>",
  "name": "Jan Kowalski",
  "phone": "+48 123 456 789",
  "location": "Warszawa",
  "job_preferences_text": "Python backend, remote",
  "gmail_connected": false,
  "resume_filename": "resume.pdf"
}""",
            st["code"],
        )
    )
    story.append(Spacer(1, 0.18 * cm))
    story.append(
        Preformatted(
            """Przykładowy stan wyszukiwania (w pamięci procesu):
{
  "status": "finished",
  "jobs_found": 20,
  "applied_ok": 3,
  "attempted_apply": 3,
  "events": [{"ts": "...", "level": "INFO", "message": "AI search started"}],
  "jobs": [{ "title": "Python Developer", "apply_url": "...", "application_status": "Applied" }]
}""",
            st["code"],
        )
    )
    story.append(p("3.11. Projekt interfejsu użytkownika", st["h2"]))
    story.append(
        p(
            "Interfejs został zorganizowany wokół czterech głównych widoków: logowania, panelu wyszukiwania, "
            "profilu oraz listy aplikacji. Część zalogowana pracuje w układzie z lewym menu nawigacyjnym.",
            st["body"],
        )
    )
    story.append(ui_mockups())
    story.append(p("Rysunek 4. Uproszczone makiety kluczowych ekranów aplikacji.", st["small"]))
    story.append(PageBreak())

    story.append(p("4. Implementacja", st["h1"]))
    story.append(p("4.1. Architektura rozwiązania", st["h2"]))
    story.append(
        p(
            "Architektura systemu ma postać klient-serwer. Frontend React odpowiada za routing, formularze, "
            "lokalny stan sesji i prezentację danych. Backend FastAPI wystawia API HTTP/SSE, realizuje autoryzację "
            "i obsługę plików oraz steruje pipeline’em AI. MongoDB przechowuje wyłącznie dane użytkowników. "
            "Wyniki wyszukiwania i logi przebiegu są trzymane w pamięci procesu.",
            st["body"],
        )
    )
    story.append(architecture_diagram())
    story.append(p("Rysunek 5. Diagram architektury rozwiązania.", st["small"]))
    story.append(p("4.2. Użyte technologie", st["h2"]))
    tech_rows = [
        ["Warstwa", "Technologie"],
        ["Frontend", "React 19, React Router, Vite, axios, CSS, konteksty Auth/I18n"],
        ["Backend API", "Python, FastAPI, Uvicorn, Pydantic"],
        ["Baza danych", "MongoDB, PyMongo"],
        ["Bezpieczeństwo", "JWT (python-jose), Passlib PBKDF2"],
        ["AI / orkiestracja", "langchain-openai, langgraph, ChatOpenAI"],
        ["Scraping / apply", "requests, BeautifulSoup, lxml, własne wrappery HTTP"],
        ["Pliki i konfiguracja", "python-dotenv, lokalny storage backend/uploads, config.json"],
        ["Testy i raportowanie", "pytest, pytest-cov, Vitest, Testing Library, coverage reports"],
    ]
    story.append(table(tech_rows, [4.0 * cm, 11.4 * cm]))
    story.append(p("4.3. Moduły backendowe", st["h2"]))
    backend_rows = [
        ["Moduł", "Rola"],
        ["app/api/routes/auth.py", "rejestracja i logowanie użytkownika"],
        ["app/api/routes/profile.py", "pobieranie i aktualizacja profilu, upload CV"],
        ["app/api/routes/search.py", "start procesu AI, status, lista ofert, stream SSE"],
        ["app/api/routes/applications.py", "lista wysłanych aplikacji użytkownika"],
        ["app/repositories/uzytkownik_repo.py", "operacje CRUD na kolekcji users"],
        ["app/services/search_state.py", "stan procesu wyszukiwania w pamięci"],
        ["app/services/ai_runner.py", "walidacja configu, uruchomienie grafu agentów"],
        ["app/services/ai/*", "definicje agentów, grafu i stanów workflow"],
        ["app/tools/*", "crawler, filtr 1-click, wrapper apply HTTP"],
    ]
    story.append(table(backend_rows, [5.2 * cm, 10.2 * cm]))
    story.append(p("4.4. Moduły frontendowe", st["h2"]))
    frontend_rows = [
        ["Moduł", "Rola"],
        ["src/App.jsx", "definicja tras publicznych i chronionych"],
        ["src/context/AuthContext.jsx", "stan sesji, login, register, logout, pobranie profilu"],
        ["src/context/I18nContext.jsx", "słowniki tłumaczeń PL/EN i zmiana języka"],
        ["src/pages/LoginPage.jsx / RegisterPage.jsx", "formularze wejścia do systemu"],
        ["src/pages/ProfilePage.jsx", "edycja profilu i upload CV"],
        ["src/pages/DashboardPage.jsx", "konfiguracja wyszukiwania, SSE, lista ofert"],
        ["src/pages/ApplicationsPage.jsx", "lista wysłanych aplikacji"],
        ["src/components/MainLayout.jsx", "szkielet części zalogowanej"],
        ["src/api/*.js", "warstwa komunikacji z backendem"],
    ]
    story.append(table(frontend_rows, [5.2 * cm, 10.2 * cm]))
    story.append(p("4.5. Integracje zewnętrzne i ograniczenia implementacyjne", st["h2"]))
    for item in [
        "Endpoint LLM jest dostarczany zewnętrznie i wskazywany przez OPENAI_BASE_URL oraz OPENAI_API_KEY.",
        "Część apply HTTP zależy od kompatybilności z aktualnym formularzem i endpointami justjoin.it.",
        "Magazyn aplikacji nie jest trwały; po restarcie backendu stan wyszukiwania i lista ofert są tracone.",
        "W kodzie przygotowano zależności pod Celery/Redis i Gmail API, lecz w aktualnej implementacji główna ścieżka działa na FastAPI BackgroundTasks i lokalnym pipeline’ie.",
    ]:
        story.append(bullet(item, st["bullet"]))

    story.append(PageBreak())
    story.append(p("5. Testy", st["h1"]))
    story.append(
        p(
            "Poniżej dołączono pełną, niezmodyfikowaną treść pliku „AI Workfinder raport z testow.pdf”. "
            "Raport stanowi ostatnią część dokumentacji zgodnie z wymaganiem projektowym.",
            st["body"],
        )
    )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


def merge_with_test_report():
    writer = PdfWriter()
    for path in [TMP_MAIN_PDF, TEST_REPORT_PDF]:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
    with OUTPUT_PDF.open("wb") as fh:
        writer.write(fh)


def main():
    build_main_pdf()
    merge_with_test_report()
    if TMP_MAIN_PDF.exists():
        TMP_MAIN_PDF.unlink()
    print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
