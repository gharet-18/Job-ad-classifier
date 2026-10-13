# 🛡️ AdVerify

**Live demo:** https://job-ad-classifier-kxugnzql4lwi2cpayfttty.streamlit.app/

AdVerify helps people check job and "digital skills" ads, especially the ones spread on TikTok, before they pay or share personal details.

Many scam ads look polished and contain no obvious red flags in the ad itself. The warning signs show up later: an upfront fee, a guaranteed-income promise, a WhatsApp-only contact, or a business that can't be found anywhere else. So this project doesn't only score text. It also guides people through verifying the business.

![App screenshot](docs/screenshot.png)

## Features
- **Verification checklist:** 7 questions about what the ad hides (fees, income promises, contact method, whether the business can be verified). Works on any ad, including polished ones.
- **Text scanner:** paste a caption, comments, or landing-page text. It scores the text and highlights the phrases behind each red flag.
- **Screenshot upload:** reads text from a TikTok screenshot with OCR, then scans it.
- **Pidgin and local phrases:** rules for common Nigerian scam wording.
- **ML layer (optional):** TF-IDF + logistic regression trained on the Kaggle Fake Job Postings dataset, blended with the rule score (60% rules, 40% ML).
- **Build your own dataset:** label scanned ads inside the app. Emails and phone numbers are removed automatically before saving.

## How the scoring works

| Score | Result |
|-------|--------|
| 60-100 | Likely scam |
| 25-59 | Suspicious |
| 0-24 | No strong red flags (this does **not** mean the ad is safe) |

Each red flag adds points (for example, an upfront fee adds 40). You can change the rules and points in `scam_core.py`.

## Project structure

```
scam-ad-detector/
├── app.py            Streamlit web app (checklist, text scan, screenshot)
├── scam_core.py      Rules, scoring, redaction, OCR
├── train.ipynb       Notebook that trains the ML layer
├── tests/            Unit tests for the rules
├── data/             Datasets (not committed)
├── models/           Trained model (not committed)
├── requirements.txt
└── packages.txt      System packages for Streamlit Cloud
```

## Setup

You need Python 3.11 and Tesseract (for screenshot reading).

```bash
git clone https://github.com/Gharet-18/scam-ad-detector.git
cd scam-ad-detector

conda create -n scamapp python=3.11 -y
conda activate scamapp
conda install -c conda-forge tesseract -y
pip install -r requirements.txt
```

## Run the web app

```bash
streamlit run app.py
```

The app works right away with rule-based scoring. Training the ML layer is optional.

## Train the ML layer (optional)
1. Download the **Real / Fake Job Posting Prediction** dataset from Kaggle:
   https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction

   Save it as `data/fake_job_postings.csv`. Check the dataset's license before reusing it.
2. Open `train.ipynb` with the `scamapp` kernel and run all cells.

This saves `models/scam_model.joblib`. Re-run the notebook after you label more examples in the app, because your own labeled data is added automatically and weighted higher. Restart the app afterwards to load the new model.

## Run the tests

```bash
pytest
```

## Deploying on Streamlit Community Cloud

Push the repo to GitHub and deploy `app.py`. The `packages.txt` file installs Tesseract. The trained model is not in the repo, so the deployed app uses rule-based scoring only unless you add a model file.

## Limitations

- **No tool can prove an ad is legitimate.** A low score means "no red flags found," not "safe." Always verify the business independently.
- **The ML layer was trained on English job postings** from Western job boards. It has no TikTok or Nigerian task scams, so the rules do most of the work for local scams.
- **The Pidgin phrase list is a starting point.** It needs real examples to improve.
- **OCR struggles with stylized or small video text.** Pasting the text is more reliable.
- **Your own labels are only as good as your verification.** Only label ads you have checked.

## Privacy

Nothing is sent to external services. Text you scan stays on your machine unless you click a label button, which saves a redacted copy to `data/scam_dataset.csv`. That folder is excluded from git, so don't commit real user data.

## Roadmap

- Explainability: show the top words driving the ML score
- Audio check: transcribe speech from video ads with Whisper
- Link and domain checker for landing pages
- Chat bot version (Telegram or WhatsApp)
- A larger, labeled dataset of local scam ads

## Safety note

If you've already paid or shared your BVN or bank details, contact your bank immediately and report the ad on the platform where you saw it.

## Dataset credit

The ML layer uses the Real / Fake Job Posting Prediction dataset on Kaggle, which comes from the University of the Aegean's Laboratory of Information & Communication Systems Security (EMSCAD).

## Author

Built by Ebong Margaret Christopher ([@Gharet-18](https://github.com/Gharet-18)).

## License

MIT License. See the `LICENSE` file.
