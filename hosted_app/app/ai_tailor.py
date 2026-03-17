from __future__ import annotations

import os
from datetime import date
import json
from dataclasses import asdict

from openai import OpenAI
from pydantic import BaseModel, Field

from app.profile import CandidateProfile, PROFILE, blank_profile, candidate_profile_from_payload
from app.tailor import (
    GeneratedExperience,
    TailoredApplication,
    build_contact_line,
    build_links_line,
    extract_company,
    extract_title,
    format_letter_date,
    infer_language,
    rank_focuses,
    select_founder,
    should_include_founder,
    slugify,
)


class AIExperience(BaseModel):
    company: str
    title: str
    date: str
    bullets: list[str] = Field(min_length=2, max_length=4)


class AIApplicationPack(BaseModel):
    company: str = ""
    role: str
    summary: str
    skills: list[str] = Field(min_length=4, max_length=7)
    experiences: list[AIExperience] = Field(min_length=2, max_length=4)
    education: list[str] = Field(min_length=2, max_length=4)
    projects: list[str] = Field(min_length=2, max_length=5)
    founder_experience: list[str] = Field(default_factory=list, max_length=3)
    cover_letter_recipient: str
    cover_letter_subject: str
    cover_letter_body: list[str] = Field(min_length=5, max_length=7)


class AIProfileTaggedText(BaseModel):
    text: str
    tags: list[str] = Field(default_factory=list, max_length=5)


class AIProfileExperience(BaseModel):
    company: str
    title: str
    date: str
    bullets: list[AIProfileTaggedText] = Field(default_factory=list, max_length=6)


class AIExtractedCandidateProfile(BaseModel):
    name: str = ""
    headline: str = ""
    city: str = ""
    address: str = ""
    phone: str = ""
    email: str = ""
    github: str = ""
    linkedin: str = ""
    languages: list[str] = Field(default_factory=list, max_length=8)
    education: list[str] = Field(default_factory=list, max_length=8)
    experiences: list[AIProfileExperience] = Field(default_factory=list, max_length=8)
    projects: list[AIProfileTaggedText] = Field(default_factory=list, max_length=8)
    founder_experience: list[AIProfileTaggedText] = Field(default_factory=list, max_length=6)


SYSTEM_PROMPT = """You tailor truthful CVs and cover letters for the supplied candidate profile.

Rules:
- Ground every statement strictly in the supplied candidate profile and the pasted job posting.
- Do not invent employers, dates, degrees, metrics, responsibilities, certifications, tools, or language ability.
- You may rewrite, condense, and reorder facts for fit, ATS clarity, and stronger positioning.
- Keep the CV concise and achievement-oriented.
- Keep the cover letter warm, direct, and human, not generic corporate fluff.
- Do not mention transcripts.
- Include founder experience only when it is relevant to the role or the caller requested it.
- Match the requested output language exactly.
- Return only structured data matching the schema.
"""


PROFILE_EXTRACTION_PROMPT = """You extract a truthful structured candidate profile from resume text.

Rules:
- Use only facts present in the supplied text.
- Do not invent employers, dates, degrees, contact details, tools, links, languages, projects, or founder history.
- Keep bullets concise and factual.
- If a field is missing, leave it empty.
- Return only structured data matching the schema.
- For `tags`, use only short lowercase labels that help tailoring, such as software, embedded, ai, sales, ops, product, web, startup, automation, systems, simulation, quality, business.
"""


def resolve_api_key(provided_key: str) -> str:
    api_key = provided_key.strip() or os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OpenAI mode requires an API key. Provide one in the form or set OPENAI_API_KEY.")
    return api_key


def extract_candidate_profile_from_text(
    source_text: str,
    *,
    api_key: str,
    model: str,
) -> CandidateProfile:
    cleaned = source_text.strip()
    if not cleaned:
        raise ValueError("The uploaded profile source is empty.")

    client = OpenAI(api_key=resolve_api_key(api_key))
    response = client.responses.parse(
        model=model,
        reasoning={"effort": "medium"},
        max_output_tokens=4000,
        store=False,
        text_format=AIExtractedCandidateProfile,
        input=f"Extract a structured candidate profile from the text below.\n\nCandidate source text:\n{cleaned}",
        instructions=PROFILE_EXTRACTION_PROMPT,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI did not return a structured candidate profile.")
    return candidate_profile_from_payload(parsed.model_dump(), base=blank_profile())


def build_user_prompt(
    *,
    profile: CandidateProfile,
    job_posting: str,
    language: str,
    include_founder: bool,
    requested_company: str,
    requested_title: str,
    heuristic_company: str,
    heuristic_title: str,
    focuses: tuple[str, ...],
) -> str:
    founder_instruction = "yes" if include_founder else "only if clearly relevant"
    return f"""Build a tailored application pack from the data below.

Requested language: {language}
Founder experience: {founder_instruction}
Requested company override: {requested_company or '(none)'}
Requested title override: {requested_title or '(none)'}
Heuristic company hint: {heuristic_company or '(none)'}
Heuristic role hint: {heuristic_title or '(none)'}
Heuristic focus areas: {', '.join(focuses)}

Output requirements:
- `role`: exact target role title.
- `company`: employer name when inferable.
- `summary`: one tight paragraph for the CV.
- `skills`: 4 to 7 role-matched lines.
- `experiences`: select and rewrite only the most relevant bullets from the candidate facts.
- `education`: keep factual and concise.
- `projects`: 2 to 5 relevant project lines.
- `founder_experience`: empty if not relevant.
- `cover_letter_recipient`: simple hiring-team style recipient block.
- `cover_letter_subject`: concise subject line.
- `cover_letter_body`: 5 to 7 paragraphs including greeting and signoff.

Candidate profile JSON:
{json.dumps(asdict(profile), ensure_ascii=False, indent=2)}

Job posting:
{job_posting}
"""


def tailor_application_with_openai(
    job_posting: str,
    *,
    api_key: str,
    model: str,
    requested_job_id: str = "",
    requested_company: str = "",
    requested_title: str = "",
    requested_language: str = "auto",
    include_founder: bool = True,
    profile: CandidateProfile = PROFILE,
) -> TailoredApplication:
    language = infer_language(job_posting, requested_language)
    heuristic_company = extract_company(job_posting, requested_company)
    heuristic_title = extract_title(job_posting, requested_title)
    focuses = rank_focuses(job_posting)
    founder_enabled = should_include_founder(include_founder, focuses, job_posting)

    client = OpenAI(api_key=resolve_api_key(api_key))
    response = client.responses.parse(
        model=model,
        reasoning={"effort": "medium"},
        max_output_tokens=4000,
        store=False,
        text_format=AIApplicationPack,
        input=build_user_prompt(
            profile=profile,
            job_posting=job_posting,
            language=language,
            include_founder=founder_enabled,
            requested_company=requested_company,
            requested_title=requested_title,
            heuristic_company=heuristic_company,
            heuristic_title=heuristic_title,
            focuses=focuses,
        ),
        instructions=SYSTEM_PROMPT,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI did not return a structured application pack.")

    company = parsed.company.strip() or heuristic_company
    role = parsed.role.strip() or heuristic_title
    job_id_source = requested_job_id or "_".join(part for part in (company, role) if part)
    job_id = slugify(job_id_source or role)

    founder_items = tuple(parsed.founder_experience)
    if not founder_enabled:
        founder_items = ()
    elif not founder_items:
        founder_items = select_founder(profile.founder_experience, focuses, True)

    return TailoredApplication(
        profile=profile,
        job_id=job_id,
        company=company,
        role=role,
        language=language,
        tailoring_mode="openai",
        ai_model=model,
        role_label=role if not company else f"{role} | {company}",
        summary=parsed.summary.strip(),
        skills=tuple(item.strip() for item in parsed.skills if item.strip()),
        experiences=tuple(
            GeneratedExperience(
                company=item.company.strip(),
                title=item.title.strip(),
                date=item.date.strip(),
                bullets=tuple(bullet.strip() for bullet in item.bullets if bullet.strip()),
            )
            for item in parsed.experiences
        ),
        education=tuple(item.strip() for item in parsed.education if item.strip()),
        projects=tuple(item.strip() for item in parsed.projects if item.strip()),
        founder_experience=tuple(item.strip() for item in founder_items if item.strip()),
        contact_line=build_contact_line(profile),
        links_line=build_links_line(profile),
        cover_letter_recipient=parsed.cover_letter_recipient.strip(),
        cover_letter_date=format_letter_date(language, date.today()),
        cover_letter_subject=parsed.cover_letter_subject.strip(),
        cover_letter_body=tuple(item.strip() for item in parsed.cover_letter_body if item.strip()),
        job_posting=job_posting,
        focuses=focuses,
    )
