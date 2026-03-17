from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from app.profile import CandidateProfile, PROFILE, TaggedText


FOCUS_KEYWORDS = {
    "software": (
        "software",
        "developer",
        "development",
        "backend",
        "frontend",
        "api",
        "java",
        "python",
        "javascript",
        "typescript",
        "sql",
        "sap",
        "abap",
        "s/4hana",
        "coding",
        "programming",
        "cloud",
    ),
    "embedded": (
        "embedded",
        "firmware",
        "iot",
        "esp32",
        "arduino",
        "raspberry pi",
        "sensor",
        "robot",
        "hardware",
        "mechatronic",
        "plc",
        "electronics",
        "automation technology",
    ),
    "ai": (
        "ai",
        "machine learning",
        "computer vision",
        "yolo",
        "llm",
        "data",
        "analytics",
        "automation",
        "optimization",
        "vision",
        "agent",
    ),
    "sales": (
        "sales",
        "vertrieb",
        "customer",
        "client",
        "partner",
        "solution",
        "consult",
        "stakeholder",
        "business development",
        "presales",
    ),
    "ops": (
        "operations",
        "support",
        "linux",
        "infrastructure",
        "systems",
        "workspace",
        "installation",
        "maintenance",
        "troubleshooting",
        "deployment",
        "enablement",
    ),
    "product": (
        "product",
        "prototype",
        "innovation",
        "startup",
        "build",
        "launch",
        "feature",
        "roadmap",
    ),
}

GERMAN_SIGNALS = (
    "bewerbung",
    "kenntnisse",
    "erfahrung",
    "entwicklung",
    "ingenieur",
    "deutsch",
    "aufgaben",
    "anforderungen",
    "mitarbeiter",
    "standort",
    "wir suchen",
)

GENERIC_NOISE_LINES = {
    "fuer arbeitgeber",
    "fur arbeitgeber",
    "für arbeitgeber",
    "job finden",
    "jobboerse",
    "jobborse",
    "jobbörse",
    "unternehmen",
    "jetzt bewerben",
    "auf einen blick",
    "deine mission",
    "dein profil",
    "deine schluesselaufgaben",
    "deine schlüsselaufgaben",
    "kontaktperson:",
    "profil ansehen",
    "d",
}

ROLE_HINTS = (
    "manager",
    "engineer",
    "developer",
    "specialist",
    "associate",
    "lead",
    "consultant",
    "analyst",
    "architect",
    "intern",
    "trainee",
)

COMPANY_HINTS = (
    "gmbh",
    "ggmbh",
    "se",
    "ag",
    "inc",
    "llc",
    "ltd",
    "corp",
    "company",
    "universidad",
    "hochschule",
)

MONTHS_DE = {
    1: "Januar",
    2: "Februar",
    3: "Maerz",
    4: "April",
    5: "Mai",
    6: "Juni",
    7: "Juli",
    8: "August",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Dezember",
}


@dataclass(frozen=True)
class GeneratedExperience:
    company: str
    title: str
    date: str
    bullets: tuple[str, ...]


@dataclass(frozen=True)
class TailoredApplication:
    profile: CandidateProfile
    job_id: str
    company: str
    role: str
    language: str
    tailoring_mode: str
    ai_model: str
    role_label: str
    summary: str
    skills: tuple[str, ...]
    experiences: tuple[GeneratedExperience, ...]
    education: tuple[str, ...]
    projects: tuple[str, ...]
    founder_experience: tuple[str, ...]
    contact_line: str
    links_line: str
    cover_letter_recipient: str
    cover_letter_date: str
    cover_letter_subject: str
    cover_letter_body: tuple[str, ...]
    job_posting: str
    focuses: tuple[str, ...]


def slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.strip().lower()).strip("_")
    return cleaned or "general"


def normalize_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def normalized_lower(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def cleaned_lines(job_posting: str) -> list[str]:
    lines: list[str] = []
    for raw in job_posting.splitlines():
        line = normalize_text(raw.strip())
        if len(line) < 2:
            continue
        lowered = normalized_lower(line)
        if lowered in GENERIC_NOISE_LINES:
            continue
        if line.startswith(("http://", "https://")):
            continue
        lines.append(line)
    return lines


def infer_language(job_posting: str, requested_language: str) -> str:
    if requested_language in {"en", "de"}:
        return requested_language
    lowered = job_posting.lower()
    german_hits = sum(lowered.count(keyword) for keyword in GERMAN_SIGNALS)
    return "de" if german_hits >= 2 else "en"


def first_meaningful_line(job_posting: str) -> str:
    for line in cleaned_lines(job_posting):
        lowered = normalized_lower(line)
        if any(hint in lowered for hint in ROLE_HINTS):
            return line
    for line in cleaned_lines(job_posting):
        return line
    return ""


def looks_like_company(line: str) -> bool:
    lowered = normalized_lower(line)
    return any(re.search(rf"\b{re.escape(hint)}\b", lowered) for hint in COMPANY_HINTS)


def looks_like_role(line: str) -> bool:
    lowered = normalized_lower(line)
    if ":" in line or len(line) > 90:
        return False
    if any(hint in lowered for hint in ROLE_HINTS):
        return True
    return 3 <= len(line.split()) <= 9 and line == line.title()


def repeated_lines(lines: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    order: list[str] = []
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
        if line not in order:
            order.append(line)
    return [line for line in order if counts[line] > 1]


def extract_title(job_posting: str, explicit_title: str) -> str:
    if explicit_title.strip():
        return explicit_title.strip()
    lines = cleaned_lines(job_posting)
    for line in repeated_lines(lines):
        if looks_like_role(line):
            return line
    match = re.search(r"(?im)^([^\r\n]+?)\s+Arbeitgeber\s*:\s*[^\r\n]+$", job_posting)
    if match:
        candidate = normalize_text(match.group(1))
        if looks_like_role(candidate):
            return candidate
    patterns = (
        r"(?im)^(?:job title|position|role)\s*[:\-]\s*(.+)$",
        r"(?im)^title\s*[:\-]\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, job_posting)
        if match:
            return normalize_text(match.group(1))
    for line in lines:
        if looks_like_role(line):
            return line
    return first_meaningful_line(job_posting) or "Target Role"


def extract_company(job_posting: str, explicit_company: str) -> str:
    if explicit_company.strip():
        return explicit_company.strip()
    patterns = (
        r"(?im)^(?:company|unternehmen|employer)\s*[:\-]\s*(.+)$",
        r"(?im)^about\s+([A-Z][^\n]+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, job_posting)
        if match:
            return normalize_text(match.group(1))
    lines = cleaned_lines(job_posting)
    for index, line in enumerate(lines):
        if normalized_lower(line) == "unternehmen" and index + 1 < len(lines):
            candidate = lines[index + 1]
            if looks_like_company(candidate):
                return candidate
    for line in lines:
        if looks_like_company(line):
            return line
    match = re.search(r"(?im)^[^\r\n]+?\s+Arbeitgeber\s*:\s*([^\r\n]+)$", job_posting)
    if match:
        return normalize_text(match.group(1))
    return ""


def rank_focuses(job_posting: str) -> tuple[str, ...]:
    lowered = job_posting.lower()
    scores: list[tuple[int, str]] = []
    for focus, keywords in FOCUS_KEYWORDS.items():
        score = sum(lowered.count(keyword) for keyword in keywords)
        scores.append((score, focus))
    scores.sort(reverse=True)
    selected = [focus for score, focus in scores if score > 0][:3]
    if "software" not in selected:
        selected = ["software", *selected[:2]]
    return tuple(dict.fromkeys(selected))[:3]


def describe_focuses(focuses: tuple[str, ...], language: str) -> str:
    if language == "de":
        labels = {
            "software": "Softwareentwicklung",
            "embedded": "Embedded- und IoT-Systeme",
            "ai": "datengetriebene Automatisierung und KI-nahe Workflows",
            "sales": "technische Kunden- und Stakeholderarbeit",
            "ops": "Betrieb, Enablement und technische Infrastruktur",
            "product": "produktnahe Entwicklung und Prototyping",
        }
        return ", ".join(labels[item] for item in focuses[:3])
    labels = {
        "software": "software engineering",
        "embedded": "embedded and IoT systems",
        "ai": "AI-enabled automation and data workflows",
        "sales": "technical customer and stakeholder work",
        "ops": "systems operations and technical enablement",
        "product": "product-focused prototyping and delivery",
    }
    return ", ".join(labels[item] for item in focuses[:3])


def build_summary(
    profile: CandidateProfile,
    role: str,
    company: str,
    focuses: tuple[str, ...],
    language: str,
) -> str:
    del profile
    focus_text = describe_focuses(focuses, language)
    company_phrase = f" at {company}" if company and language == "en" else ""
    if company and language == "de":
        company_phrase = f" bei {company}"
    if language == "de":
        return (
            "Mechatronik-Ingenieur mit starker Praxis an der Schnittstelle von "
            f"{focus_text}. Ich uebersetze Anforderungen in saubere, lauffaehige "
            "Loesungen, arbeite sicher in interdisziplinaeren Teams und bringe eine "
            f"schnelle Einarbeitung fuer die Rolle {role}{company_phrase} mit."
        )
    return (
        "Mechatronics engineer and junior software engineer with hands-on experience across "
        f"{focus_text}. I translate requirements into reliable implementations, work well "
        "across multidisciplinary teams, and ramp quickly in new stacks and domains. "
        f"This version is targeted to {role}{company_phrase}."
    )


def score_tagged_text(item: TaggedText, focuses: tuple[str, ...]) -> int:
    score = 0
    for focus in focuses:
        if focus in item.tags:
            score += 3
    if "software" in item.tags:
        score += 1
    if "product" in item.tags:
        score += 1
    return score


def select_skills(focuses: tuple[str, ...], language: str) -> tuple[str, ...]:
    if language == "de":
        library = {
            "software": (
                "Programmierung: Python, Java, C++, C#, JavaScript/TypeScript, SQL",
                "Engineering Practices: OOP, Testing, Debugging, Dokumentation",
            ),
            "embedded": (
                "Embedded und IoT: ESP32, Arduino, Raspberry Pi, Sensorintegration, MQTT, Node-RED",
                "Prototyping: CAD, 3D-Druck, Hardware-Software-Schnittstellen",
            ),
            "ai": (
                "Daten und KI-nahe Workflows: Python-Automatisierung, OpenCV, YOLO, Optimierungslogik, Analytics",
            ),
            "sales": (
                "Schnittstellenarbeit: Anforderungen klaeren, technische Abstimmung, partnernahe Kommunikation",
            ),
            "ops": (
                "Betrieb und Infrastruktur: Linux, Services, Logging, Troubleshooting, Deployment Readiness",
            ),
            "product": (
                "Produktarbeit: Prototyping, MVP-Umsetzung, interdisziplinaere Delivery",
            ),
        }
    else:
        library = {
            "software": (
                "Programming: Python, Java, C++, C#, JavaScript/TypeScript, SQL",
                "Engineering Practices: OOP, testing, debugging, documentation",
            ),
            "embedded": (
                "Embedded and IoT: ESP32, Arduino, Raspberry Pi, sensor integration, MQTT, Node-RED",
                "Prototyping: CAD, 3D printing, hardware-software integration",
            ),
            "ai": (
                "AI-enabled workflows: Python automation, OpenCV, YOLO, optimization logic, analytics",
            ),
            "sales": (
                "Cross-functional delivery: requirements gathering, technical communication, partner-facing coordination",
            ),
            "ops": (
                "Systems and operations: Linux, services, logging, troubleshooting, deployment readiness",
            ),
            "product": (
                "Product work: prototyping, MVP execution, multidisciplinary delivery",
            ),
        }

    selected: list[str] = []
    for focus in focuses:
        selected.extend(library.get(focus, ()))
    if language == "de":
        selected.append(
            "Sprachen: Deutsch (fortgeschritten), Englisch (fliessend), Spanisch (Muttersprache), Franzoesisch (mittel)"
        )
    else:
        selected.append(
            "Languages: German (Advanced), English (Proficient), Spanish (Native), French (Intermediate)"
        )
    return tuple(dict.fromkeys(selected))[:6]


def select_experiences(profile: CandidateProfile, focuses: tuple[str, ...]) -> tuple[GeneratedExperience, ...]:
    experiences: list[GeneratedExperience] = []
    for record in profile.experiences:
        ranked = sorted(
            record.bullets,
            key=lambda bullet: (score_tagged_text(bullet, focuses), len(bullet.text)),
            reverse=True,
        )
        selected = tuple(item.text for item in ranked[:4])
        experiences.append(
            GeneratedExperience(
                company=record.company,
                title=record.title,
                date=record.date,
                bullets=selected,
            )
        )
    return tuple(experiences)


def select_projects(projects: tuple[TaggedText, ...], focuses: tuple[str, ...]) -> tuple[str, ...]:
    ranked = sorted(
        projects,
        key=lambda item: (score_tagged_text(item, focuses), len(item.text)),
        reverse=True,
    )
    return tuple(item.text for item in ranked[:4])


def should_include_founder(include_founder: bool, focuses: tuple[str, ...], job_posting: str) -> bool:
    if include_founder:
        return True
    lowered = job_posting.lower()
    startup_keywords = ("startup", "ownership", "builder", "entrepreneur", "ambiguity", "0 to 1")
    return any(keyword in lowered for keyword in startup_keywords) or "product" in focuses


def select_founder(
    founder_items: tuple[TaggedText, ...],
    focuses: tuple[str, ...],
    enabled: bool,
) -> tuple[str, ...]:
    if not enabled:
        return ()
    ranked = sorted(
        founder_items,
        key=lambda item: (score_tagged_text(item, focuses), len(item.text)),
        reverse=True,
    )
    return tuple(item.text for item in ranked[:3])


def format_letter_date(language: str, today: date) -> str:
    if language == "de":
        return f"Heilbronn, {today.day}. {MONTHS_DE[today.month]} {today.year}"
    return today.strftime("Heilbronn, %d %B %Y")


def build_cover_letter(
    role: str,
    company: str,
    focuses: tuple[str, ...],
    language: str,
) -> tuple[str, str, tuple[str, ...]]:
    recipient = "Hiring Team"
    if company:
        recipient = f"Hiring Team\n{company}" if language == "en" else f"HR-Team\n{company}"

    if language == "de":
        subject = f"Bewerbung als {role}"
        company_phrase = f" bei {company}" if company else ""
        focus_text = describe_focuses(focuses, language)
        body = (
            "Sehr geehrtes Team,",
            (
                f"die Rolle {role}{company_phrase} passt sehr gut zu meinem Profil, weil "
                f"ich praktische Erfahrung in {focus_text} mitbringe und gern an der "
                "Schnittstelle von Technik, Umsetzung und Nutzeranforderungen arbeite."
            ),
            (
                "In meinen bisherigen Stationen habe ich technische Anforderungen in "
                "strukturierte Aufgaben uebersetzt, funktionsuebergreifend mit Software-, "
                "Hardware- und Datenteams gearbeitet und sowohl Prototyping als auch "
                "Testing, Dokumentation und operative Stabilitaet unterstuetzt."
            ),
            (
                "Ich bringe eine schnelle Einarbeitung, saubere Kommunikation und eine "
                "hands-on Arbeitsweise mit. Besonders stark bin ich dort, wo komplexe "
                "Systeme pragmatisch in nutzbare Loesungen ueberfuehrt werden muessen."
            ),
            "Ich freue mich ueber die Moeglichkeit, meinen Hintergrund in einem Gespraech naeher vorzustellen.",
            "Mit freundlichen Gruessen,\n\nRodrigo Ponce Cortes",
        )
        return recipient, subject, body

    subject = f"Application for {role}"
    company_phrase = f" at {company}" if company else ""
    focus_text = describe_focuses(focuses, language)
    body = (
        "Dear Hiring Team,",
        (
            f"The {role} opportunity{company_phrase} is a strong fit for my background because "
            f"I bring practical experience across {focus_text} and I enjoy turning complex "
            "technical requirements into reliable, usable outcomes."
        ),
        (
            "Across my recent roles I have coordinated work between software, hardware, and "
            "data teams, translated stakeholder needs into structured execution plans, and "
            "supported testing, documentation, and deployment readiness."
        ),
        (
            "I bring a fast ramp-up curve, clear communication, and a hands-on engineering style. "
            "I am strongest in environments where multidisciplinary systems need pragmatic execution "
            "and where technical breadth is an advantage."
        ),
        "I would welcome the opportunity to discuss how I can contribute.",
        "Sincerely,\n\nRodrigo Ponce Cortes",
    )
    return recipient, subject, body


def build_contact_line(profile: CandidateProfile) -> str:
    return f"{profile.city} | {profile.address} | {profile.phone} | {profile.email}"


def build_links_line(profile: CandidateProfile) -> str:
    return f"GitHub: https://{profile.github} | LinkedIn: https://{profile.linkedin}"


def tailor_application(
    job_posting: str,
    *,
    requested_job_id: str = "",
    requested_company: str = "",
    requested_title: str = "",
    requested_language: str = "auto",
    include_founder: bool = True,
    profile: CandidateProfile = PROFILE,
) -> TailoredApplication:
    role = extract_title(job_posting, requested_title)
    company = extract_company(job_posting, requested_company)
    language = infer_language(job_posting, requested_language)
    focuses = rank_focuses(job_posting)
    job_id_source = requested_job_id or "_".join(part for part in (company, role) if part)
    job_id = slugify(job_id_source or role)
    founder_enabled = should_include_founder(include_founder, focuses, job_posting)
    recipient, subject, body = build_cover_letter(role, company, focuses, language)

    return TailoredApplication(
        profile=profile,
        job_id=job_id,
        company=company,
        role=role,
        language=language,
        tailoring_mode="heuristic",
        ai_model="",
        role_label=role if not company else f"{role} | {company}",
        summary=build_summary(profile, role, company, focuses, language),
        skills=select_skills(focuses, language),
        experiences=select_experiences(profile, focuses),
        education=profile.education,
        projects=select_projects(profile.projects, focuses),
        founder_experience=select_founder(profile.founder_experience, focuses, founder_enabled),
        contact_line=build_contact_line(profile),
        links_line=build_links_line(profile),
        cover_letter_recipient=recipient,
        cover_letter_date=format_letter_date(language, date.today()),
        cover_letter_subject=subject,
        cover_letter_body=body,
        job_posting=job_posting,
        focuses=focuses,
    )
