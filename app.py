import csv
import shutil
from datetime import date

import streamlit as st
from PIL import Image

from scam_core import (DATA_DIR, analyze, combined_score, read_image_text,
                       redact, verdict)

DATASET_FILE = DATA_DIR / "fake_job_postings.csv"

QUESTIONS = [
    ("They ask for money before you start (fee, kit, registration)", 35),
    ("They ask for BVN, ID, or bank details early", 30),
    ("They promise a specific income or guaranteed results", 25),
    ("I can't find an official website, CAC registration, or real reviews outside their own page", 20),
    ("Contact is only through WhatsApp, Telegram, or DMs", 15),
    ("I'm being pressured to decide fast (limited slots, countdown)", 15),
    ("The only testimonials are on their own page or screenshots", 10),
]


def highlight(text, spans):
    spans = sorted(spans)
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else:
            merged.append((s, e))
    out, last = "", 0
    for s, e in merged:
        out += text[last:s] + f":red-background[{text[s:e]}]"
        last = e
    return out + text[last:]


def save_example(text, label):
    DATA_DIR.mkdir(exist_ok=True)
    is_new = not DATASET_FILE.exists()
    with open(DATASET_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["text", "label", "date"])
        writer.writerow([redact(text), label, date.today().isoformat()])


def show_next_steps():
    st.subheader("What to do next")
    st.markdown(
        "- Never pay to get a job or start earning\n"
        "- Check the business on its official website, CAC search, and independent reviews\n"
        "- Don't share BVN, ID, or bank details before a verified offer\n"
        "- Report the suspicious ad on TikTok (Share > Report)"
    )


def render_result(text):
    st.session_state["last_text"] = text
    rule_s, flags, spans = analyze(text)
    s, ml = combined_score(text, rule_s)
    v = verdict(s)
    if v == "scam":
        st.error(f"🚨 Likely scam ({s}/100)")
    elif v == "suspicious":
        st.warning(f"⚠️ Suspicious ({s}/100)")
    else:
        st.info(
            f"No strong red flags in this text ({s}/100). That doesn't mean it's safe. "
            "Use the Checklist tab to verify the business."
        )
    if ml is not None:
        st.caption(f"Rule score: {rule_s} · ML score: {ml}")
    else:
        st.caption("ML model not found, showing rule score only.")
    if flags:
        st.subheader("Red flags found")
        for label, points, found in flags:
            st.write(f"**{label}** (+{points}): " + ", ".join(f"`{f}`" for f in found))
        st.subheader("Highlighted text")
        st.markdown(highlight(text, spans))
    show_next_steps()


st.set_page_config(page_title="AdVerify", page_icon="🛡️")
st.title("🛡️AdVerify")
st.caption("Seen a job or 'skills' ad on TikTok or any social platform? Check it before you pay or share details.")

tab_check, tab_text, tab_img = st.tabs(["✅ Checklist", "📝 Scan text", "📷 Screenshot"])

with tab_check:
    st.write("Tick everything that applies to the ad or the page it leads to.")
    score, ticked = 0, []
    for i, (question, pts) in enumerate(QUESTIONS):
        if st.checkbox(question, key=f"q{i}"):
            score += pts
            ticked.append(question)
    score = min(score, 100)
    if st.button("Get verdict", type="primary", key="verdict"):
        if score >= 60:
            st.error(f"🚨 High risk ({score}/100). Do not pay or send any details.")
        elif score >= 30:
            st.warning(f"⚠️ Be careful ({score}/100). Verify the business before going further.")
        else:
            st.info(
                f"🔍 Few warning signs ({score}/100). That doesn't prove it's safe. "
                "Confirm the business exists and read independent reviews before paying."
            )
        if ticked:
            st.subheader("Warning signs you found")
            for question in ticked:
                st.write("• " + question)
        show_next_steps()

with tab_text:
    st.write("Paste the caption, comments, or landing page text.")
    ad = st.text_area("Ad text", height=200, placeholder="Paste text here...")
    if st.button("Scan text", type="primary", key="scan"):
        if ad.strip():
            render_result(ad)
        else:
            st.warning("Paste some text first.")

with tab_img:
    st.write("Upload a screenshot of the ad. Include the caption or comments if you can.")
    img_file = st.file_uploader("Screenshot", type=["png", "jpg", "jpeg"])
    if shutil.which("tesseract") is None:
        st.error("Tesseract is not installed on this server, so screenshots can't be read.")
    if img_file is not None:
        image = Image.open(img_file)
        st.image(image, use_container_width=True)
        if st.button("Read and scan", type="primary", key="ocr"):
            extracted = read_image_text(image)
            if not extracted:
                st.warning(
                    "Couldn't read any text. Try a clearer screenshot, paste the text instead, "
                    "or check that Tesseract is installed."
                )
            else:
                with st.expander("Text read from image"):
                    st.write(extracted)
                render_result(extracted)

st.divider()
with st.expander("🧠 Help improve this tool"):
    last = st.session_state.get("last_text")
    if not last:
        st.write("Scan something first, then label it here to grow the dataset.")
    else:
        st.write(
            "Only label ads you have actually verified. "
            "Phone numbers and emails are removed automatically."
        )
        st.caption(redact(last)[:300])
        col1, col2 = st.columns(2)
        if col1.button("It was a scam", key="save_scam"):
            save_example(last, 1)
            st.success("Saved to data/scam_dataset.csv")
        if col2.button("It was legit", key="save_ok"):
            save_example(last, 0)
            st.success("Saved to data/scam_dataset.csv")
