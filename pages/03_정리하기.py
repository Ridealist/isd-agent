# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import pypandoc
import os
import streamlit as st

@st.cache_resource
def ensure_pandoc():
    try:
        pypandoc.get_pandoc_version()
    except OSError:
        pypandoc.download_pandoc()
        os.environ["PYPANDOC_PANDOC"] = pypandoc.get_pandoc_path()

ensure_pandoc()

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import tempfile
import logging
import pytz
import sys
import streamlit as st

from datetime import datetime

from src.components.sidebar import render_sidebar


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_md_to_docx(md_text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpfile:
        pypandoc.convert_text(md_text, "docx", format="md", outputfile=tmpfile.name)
        tmpfile_path = tmpfile.name

    # Read the DOCX file into memory
    with open(tmpfile_path, "rb") as docx_file:
        docx_data = docx_file.read()

    return docx_data


#--------------------------------#
#         Streamlit App          #
#--------------------------------#
# Logo
st.logo(
    "https://media.licdn.com/dms/image/v2/C511BAQFHW_naY__2Fg/company-background_10000/company-background_10000/0/1583927014937/iled_lighting_systems_pvt_ltd__cover?e=2147483647&v=beta&t=Y1x2WJMstxhMwG8RDFgTgTQbhYyn6Us6rRGDRtsiaoA",
    link="https://iled.snu.ac.kr/",
    size="large"
)

#--------------------------------#
#         Streamlit Session State         #
#--------------------------------#

if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "is_end" not in st.session_state:
    st.session_state["is_end"] = False

if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "client_analysis" not in st.session_state:
    st.session_state["client_analysis"] = None

if "interview_analysis" not in st.session_state:
    st.session_state["interview_analysis"] = None

if "final_report" not in st.session_state:
    st.session_state["final_report"] = None



# Main layout
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.title("🔍 :red[ISD Agent] 수행 문제 분석 도우미", anchor=False)


    # Render sidebar and get selection (provider and model)
    selection = render_sidebar()

    # Check if API keys are set based on provider
    if selection["provider"] == "OpenAI":
        if not os.environ.get("OPENAI_API_KEY"):
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started")
            st.stop()
    # elif selection["provider"] == "GROQ":
    #     if not os.environ.get("GROQ_API_KEY"):
    #         st.warning("⚠️ Please enter your GROQ API key in the sidebar to get started")
    #         st.stop()

    # # Check EXA key for non-Ollama providers
    # if selection["provider"] != "Ollama":
    #     if not os.environ.get("EXA_API_KEY"):
    #         st.warning("⚠️ Please enter your EXA API key in the sidebar to get started")
    #         st.stop()

    # Add Ollama check
    # if selection["provider"] == "Ollama" and not selection["model"]:
    #     st.warning("⚠️ No Ollama models found. Please make sure Ollama is running and you have models loaded.")
    #     st.stop()


    st.subheader("최종 수행 문제 분석 보고서")
    # Convert CrewOutput to string for display and download
    result_text = str(st.session_state["final_report"])
    
    # Convert Markdown to DOCX
    docx_data = convert_md_to_docx(result_text)
    
    with st.container(height=500):
        # Display the final result
        if result_text and result_text != 'None':
            st.markdown(result_text)

    if st.session_state["final_report"]:

            # Create download buttons
            st.divider()
            download_col1, download_col2, download_col3 = st.columns([1, 2, 1])
            with download_col2:
                st.markdown("### 📥 Download Research Report")

                # Download as DOCX
                st.download_button(
                    label="MS Word 파일로 다운로드",
                    data=docx_data,
                    file_name="research_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Download the research report in Word format",
                )

                # Download as Markdown
                st.download_button(
                    label="Markdown 파일로 다운로드",
                    data=result_text,
                    file_name="research_report.md",
                    mime="text/markdown",
                    help="Download the research report in Markdown format"
                )


    # # 다음 단계로 버튼
    mov_col1, mov_col2, mov_col3 = st.columns([1, 1, 1])
    with mov_col1:
        if st.button(
            label="이전단계로",
            icon="⏪",
            type="primary",
            use_container_width=True
        ):
            st.switch_page("pages/02_분석하기.py")

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("ISD Agent는 실수를 할 수 있습니다. 응답을 다시 한 번 확인하고 비판적으로 검토해주세요.")