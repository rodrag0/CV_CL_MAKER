# Application Pack Wrapper

Local Flask app for generating tailored CV and cover-letter document packs from a pasted job posting.

## Run

```powershell
python -m pip install -r requirements.txt
python webapp.py
```

Open `http://127.0.0.1:5000`.

## Tailoring Modes

- `Fast local`: rule-based tailoring with no API key.
- `OpenAI tailored`: stronger tailoring using an OpenAI API key from the form or `OPENAI_API_KEY`.

Recommended model:

- `gpt-5.4` for highest-quality tailoring
- `gpt-5-mini` for cheaper, faster iterations

## Output

- `CV/<job_id>/files/Rodrigo_Ponce_Cortes_CV_ATS_Styled.docx`
- `CV/<job_id>/files/Rodrigo_Ponce_Cortes_CV_Designed.docx`
- `Cover Letters/<job_id>/files/Rodrigo_Ponce_Cortes_Cover_Letter_Styled.docx`
- `CV/<job_id>/application_manifest.json`
- `CV/<job_id>/job_posting.txt`

PDF files are generated only when `LibreOffice` or `soffice` is available on the machine.

## Hosted version

The VPS-ready version lives in [hosted_app/README.md](/C:/Users/Rodrigo/Documents/Projects2/codex-projects/job%20search/hosted_app/README.md) with deployment notes in [hosted_app/DEPLOY.md](/C:/Users/Rodrigo/Documents/Projects2/codex-projects/job%20search/hosted_app/DEPLOY.md).
