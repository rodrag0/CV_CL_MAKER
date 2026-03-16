from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, abort, render_template, request, send_file

from app.ai_tailor import tailor_application_with_openai
from app.generator import GENERATED_ROOT, cleanup_old_packs, generate_application_pack
from app.tailor import tailor_application


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


def form_defaults() -> dict[str, str]:
    return {
        "job_posting": "",
        "company": "",
        "title": "",
        "job_id": "",
        "language": "auto",
        "tailoring_mode": "heuristic",
        "openai_model": "gpt-5.4",
        "api_key": "",
        "create_cover_letter": "on",
        "include_founder": "on",
    }


def build_downloads(pack_id: str, generated) -> list[dict[str, str]]:
    downloads = [
        {
            "label": "Download Full Pack (.zip)",
            "path": str(generated.bundle_zip.relative_to(generated.output_root)),
            "kind": "bundle",
        },
        {
            "label": "ATS CV (.docx)",
            "path": str(generated.ats_docx.relative_to(generated.output_root)),
            "kind": "docx",
        },
        {
            "label": "Designed CV (.docx)",
            "path": str(generated.designed_docx.relative_to(generated.output_root)),
            "kind": "docx",
        },
    ]

    if generated.letter_docx:
        downloads.append(
            {
                "label": "Cover Letter (.docx)",
                "path": str(generated.letter_docx.relative_to(generated.output_root)),
                "kind": "docx",
            }
        )

    optional_files = [
        (generated.ats_pdf, "ATS CV (.pdf)"),
        (generated.designed_pdf, "Designed CV (.pdf)"),
        (generated.letter_pdf, "Cover Letter (.pdf)"),
        (generated.manifest_path, "Manifest (.json)"),
        (generated.job_posting_path, "Original Posting (.txt)"),
    ]
    for path, label in optional_files:
        if path is not None:
            downloads.append(
                {
                    "label": label,
                    "path": str(path.relative_to(generated.output_root)),
                    "kind": path.suffix.lstrip("."),
                }
            )
    for item in downloads:
        item["url"] = f"/download/{pack_id}/{item['path']}"
    return downloads


def safe_generated_path(pack_id: str, relative_path: str) -> Path:
    base = (GENERATED_ROOT / pack_id).resolve()
    target = (base / relative_path).resolve()
    if base != target and base not in target.parents:
        raise FileNotFoundError(relative_path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError(relative_path)
    return target


@app.route("/", methods=["GET", "POST"])
def index():
    cleanup_old_packs()
    values = form_defaults()
    result = None
    error = None

    if request.method == "POST":
        values.update({key: request.form.get(key, "") for key in values})
        values["create_cover_letter"] = "on" if request.form.get("create_cover_letter") else ""
        values["include_founder"] = "on" if request.form.get("include_founder") else ""

        if not values["job_posting"].strip():
            error = "Paste a job posting before generating an application pack."
        else:
            try:
                if values["tailoring_mode"] == "openai":
                    application = tailor_application_with_openai(
                        values["job_posting"],
                        api_key=request.form.get("api_key", ""),
                        model=values["openai_model"],
                        requested_job_id=values["job_id"],
                        requested_company=values["company"],
                        requested_title=values["title"],
                        requested_language=values["language"],
                        include_founder=bool(values["include_founder"]),
                    )
                else:
                    application = tailor_application(
                        values["job_posting"],
                        requested_job_id=values["job_id"],
                        requested_company=values["company"],
                        requested_title=values["title"],
                        requested_language=values["language"],
                        include_founder=bool(values["include_founder"]),
                    )

                pack_id = uuid.uuid4().hex
                generated = generate_application_pack(
                    application,
                    pack_id=pack_id,
                    create_cover_letter=bool(values["create_cover_letter"]),
                )
                result = {
                    "job_id": application.job_id,
                    "role": application.role,
                    "company": application.company or "Not inferred",
                    "language": application.language,
                    "focuses": ", ".join(application.focuses),
                    "tailoring_mode": application.tailoring_mode,
                    "ai_model": application.ai_model or "Not used",
                    "pack_id": pack_id,
                    "downloads": build_downloads(pack_id, generated),
                }
            except Exception as exc:
                error = str(exc)

        values["api_key"] = ""

    return render_template("index.html", values=values, result=result, error=error)


@app.get("/download/<pack_id>/<path:relative_path>")
def download(pack_id: str, relative_path: str):
    try:
        path = safe_generated_path(pack_id, relative_path)
    except FileNotFoundError:
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
