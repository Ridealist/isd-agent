# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import tempfile
import pypandoc
import magic
import PyPDF2
import io
import logging
import streamlit as st
import os
from datetime import datetime
import pytz

from src.components.llm import get_chat_completion
from src.components.prompts import CLIENT_REQUIREMENTS_PROMPT, INTERVIEW_PROMPT
from src.components.sidebar import render_sidebar
from src.components.researcher import GapAnalysisCrew, StreamToExpander
from src.components.db import DynamoDBManager
from src.utils.output_handler import capture_output


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#--------------------------------#
#         Streamlit Session State         #
#--------------------------------#
if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "client_analysis" not in st.session_state:
    st.session_state["client_analysis"] = None

if "interview_analysis" not in st.session_state:
    st.session_state["interview_analysis"] = None


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
# Configure the page
st.set_page_config(
    page_title="ISD-Agent",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo
st.logo(
    "https://media.licdn.com/dms/image/v2/C511BAQFHW_naY__2Fg/company-background_10000/company-background_10000/0/1583927014937/iled_lighting_systems_pvt_ltd__cover?e=2147483647&v=beta&t=Y1x2WJMstxhMwG8RDFgTgTQbhYyn6Us6rRGDRtsiaoA",
    link="https://iled.snu.ac.kr/",
    size="large"
)

#--------------------------------#
#         Streamlit Session State         #
#--------------------------------#

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "is_end" not in st.session_state:
    st.session_state["is_end"] = False


if st.session_state["logged_in"]:
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
    elif selection["provider"] == "GROQ":
        if not os.environ.get("GROQ_API_KEY"):
            st.warning("⚠️ Please enter your GROQ API key in the sidebar to get started")
            st.stop()

    # Check EXA key for non-Ollama providers
    if selection["provider"] != "Ollama":
        if not os.environ.get("EXA_API_KEY"):
            st.warning("⚠️ Please enter your EXA API key in the sidebar to get started")
            st.stop()

    # Add Ollama check
    if selection["provider"] == "Ollama" and not selection["model"]:
        st.warning("⚠️ No Ollama models found. Please make sure Ollama is running and you have models loaded.")
        st.stop()


    with st.expander("See Summarization"):
        prev_col1, prev_col2 = st.columns([1, 1])

        with prev_col1.container():
            st.markdown("### <클라이언트 요구사항 분석>")
            st.write(st.session_state["client_analysis"])
        with prev_col2.container():
            st.markdown("### <인터뷰 핵심 내용 정리>")
            st.write(st.session_state["interview_analysis"])


    if st.session_state["analyze_ready"]:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            start_research = st.button("🚀 Start Analysis", use_container_width=True, type="primary")

        if start_research:
            with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
                try:
                    # Initialize DynamoDB manager
                    db_manager = DynamoDBManager()
                    # Get current time in KST
                    kst = pytz.timezone('Asia/Seoul')
                    timestamp = datetime.now(kst).isoformat()

                    with st.container(height=500, border=False):
                        sys.stdout = StreamToExpander(st)
                        crew = GapAnalysisCrew(
                            client_analysis=st.session_state["client_analysis"],
                            interview_analysis=st.session_state["interview_analysis"]
                        )

                        final_report = crew.analyze(
                            st.session_state["client_analysis"],
                            st.session_state["interview_analysis"],
                        )

                        # Save analysis results to DynamoDB
                        db_manager.insert_chat_data(
                            student_id=st.session_state["session_id"],
                            timestamp=timestamp,
                            who="agent",
                            content=str(final_report),
                            context="gap_analysis"
                        )

                    status.update(label="✅ Analysis completed!", state="complete", expanded=False)
                    st.session_state["is_end"] = True

                except Exception as e:
                    status.update(label="❌ Error occurred", state="error")
                    st.error(f"An error occurred: {str(e)}")
                    st.stop()

            # final_report = """# Research Report

            #     ## Introduction
            #     This is an automatically generated research report.

            #     ## Findings
            #     - Finding 1: Important discovery.
            #     - Finding 2: Another key insight.

            #     ## Conclusion
            #     The research indicates that...
            #     """
            
            # Convert CrewOutput to string for display and download
            result_text = str(final_report)
            
            # Convert Markdown to DOCX
            docx_data = convert_md_to_docx(result_text)
            
            # Display the final result
            st.markdown(result_text)

            # Create download buttons
            st.divider()
            download_col1, download_col2, download_col3 = st.columns([1, 2, 1])
            with download_col2:
                st.markdown("### 📥 Download Research Report")

                # # Download as Markdown
                # st.download_button(
                #     label="Download Report as Mardown",
                #     data=result_text,
                #     file_name="research_report.md",
                #     mime="text/markdown",
                #     help="Download the research report in Markdown format"
                # )

                # Download as DOCX
                st.download_button(
                    label="Download as DOCX",
                    data=docx_data,
                    file_name="research_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    help="Download the research report in Word format"
                )

                st.session_state["analyze_ready"] = False

            # Renew previous process
            st.session_state["analyze_ready"] = False


    # # 다음 단계로 버튼
    mov_col1, mov_col2, mov_col3 = st.columns([1, 1, 1])
    with mov_col1:
        if st.button(
            label="이전단계로",
            icon="⏪",
            help="요약하기로 이동하기",
            type="primary",
            use_container_width=True
        ):
            st.switch_page("pages/01_요약하기.py")
    # with col2:
    #     st.button(
    #             label="재실행",
    #             icon="🔄",
    #             help="다시 AI 답변 받기",
    #             on_click=""
    #         )
    # with mov_col3:
    #     if st.session_state["analyze_ready"]:
    #         if st.button(
    #             label="다음단계로",
    #             icon="⏩",
    #             help="과제분석으로 이동하기",
    #             type="primary",
    #             use_container_width=True
    #         ):
    #             st.switch_page("pages/과제분석.py")
else:
    st.error("먼저 로그인을 해주세요!")

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("Made with ❤️ using [CrewAI](https://crewai.com) and [Streamlit](https://streamlit.io)")