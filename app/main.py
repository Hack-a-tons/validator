"""Streamlit UI for Validator."""

from __future__ import annotations

from dotenv import load_dotenv
import streamlit as st

from app.extractor import VideoExtractionError, extract_mp4_url
from app.openai_client import ArbitrationError, Verdict, arbitrate
from app.twelvelabs_client import TwelveLabsError, describe_primary_subject

load_dotenv()

st.set_page_config(page_title="PRE-GEN detect", page_icon="🛡️", layout="centered")
st.title("🛡️ PRE-GEN detect — Visual Jailbreak Detection")
st.write("Compare a generated video's visible subject against a protected description before distribution.")

with st.form("validation-form"):
    video_url = st.text_input("Video URL", placeholder="https://buddian.com/app/video?id=241")
    protected_description = st.text_area(
        "Protected Description",
        placeholder="Describe the protected subject's observable physical traits…",
        height=150,
    )
    submitted = st.form_submit_button("Validate Generation", type="primary")

if submitted:
    if not video_url.strip() or not protected_description.strip():
        st.error("Both the video URL and protected description are required.")
    else:
        try:
            with st.status("Validation in progress…", expanded=True) as status:
                st.write("1. Extracting a direct MP4 URL…")
                mp4_url = extract_mp4_url(video_url)
                st.write("2. Scanning visual content with TwelveLabs…")
                visual_description = describe_primary_subject(mp4_url)
                st.write("3. Arbitrating against the protected description…")
                result: Verdict = arbitrate(protected_description, visual_description)
                status.update(label="Validation complete", state="complete", expanded=False)
        except (VideoExtractionError, TwelveLabsError, ArbitrationError) as exc:
            st.error(str(exc))
        else:
            if result.verdict == "DECLINE":
                st.error("## 🔴 DECLINE\nThe generated visual subject may match the protected description.")
            else:
                st.success("## 🟢 APPROVE\nClear visual differences were found from the protected description.")
            st.caption(f"Reasoning: {result.reasoning}")
            with st.expander("Visual extraction details"):
                st.write(visual_description)
                st.code(mp4_url, language=None)
