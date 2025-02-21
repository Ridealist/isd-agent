# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import tempfile
import pypandoc
import magic
import PyPDF2
import io
import logging
import streamlit as st
import os

from src.components.llm import get_chat_completion
from src.components.prompts import CLIENT_REQUIREMENTS_PROMPT, INTERVIEW_PROMPT
from src.components.sidebar import render_sidebar
from src.components.researcher import GapAnalysisCrew, StreamToExpander
# from src.components.researcher import create_researcher, create_research_task, run_research
from src.utils.output_handler import capture_output


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#--------------------------------#
#         Streamlit App          #
#--------------------------------#
# Configure the page
st.set_page_config(
    page_title="CrewAI Research Assistant",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo
st.logo(
    "https://cdn.prod.website-files.com/66cf2bfc3ed15b02da0ca770/66d07240057721394308addd_Logo%20(1).svg",
    link="https://www.crewai.com/",
    size="large"
)

#--------------------------------#
#         Streamlit Session State         #
#--------------------------------#
if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

### PDF-File Handler

def process_pdf_file(file) -> str:
    """PDF 파일을 처리하고 텍스트를 추출하는 헬퍼 함수"""
    content_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)
    
    if content_type != "application/pdf":
        st.error("PDF 파일만 업로드 가능합니다.")
    
    contents = file.read()
    pdf = PyPDF2.PdfReader(io.BytesIO(contents))
    
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text()
    
    return full_text

# Main layout
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🔍 :red[CrewAI] Performance Analysis Assistant", anchor=False)


st.subheader("클라이언트 요구사항 파일")
uploaded_file_client = st.file_uploader(
    "클라이언트 요구사항 파일", accept_multiple_files=False
)
# if uploaded_file_client:
#     bytes_data = uploaded_file_client.read()
#     full_text = process_pdf_file(uploaded_file_client)
#     # st.write("file content:", full_text)
#     # st.write(bytes_data)

st.subheader("인터뷰 내용 파일")
uploaded_file_interview = st.file_uploader(
    "인터뷰 내용 파일", accept_multiple_files=False
)
# if uploaded_file_interview:
#     bytes_data = uploaded_file_interview.read()
#     full_text = process_pdf_file(uploaded_file_interview)
#     # st.write("file content:", full_text)
#     # st.write(bytes_data)


def analyze_files(client_file, interview_file):
    logger.info("Received analysis request")
    
    # try:
    # 클라이언트 파일 처리
    client_content = process_pdf_file(client_file)
    client_prompt = CLIENT_REQUIREMENTS_PROMPT.format(text=client_content)
    client_analysis = get_chat_completion(client_prompt)
    
    # 인터뷰 파일 처리
    interview_content = process_pdf_file(interview_file)
    interview_prompt = INTERVIEW_PROMPT.format(text=interview_content)
    interview_analysis = get_chat_completion(interview_prompt)
    
    return {
        "status": "success",
        "client_analysis": client_analysis,
        "interview_analysis": interview_analysis
    }
    
    # except Exception as e:
    #     logger.error(f"Analysis failed: {str(e)}", exc_info=True)
    #     raise HTTPException(status_code=500, detail=str(e))


bt_col1, bt_col2, bt_col3 = st.columns([1, 1, 1])
with bt_col2:
    button_analyze = st.button(label="📝 Summarize Documents", type="primary", use_container_width=True)

if button_analyze:
    col1, col2 = st.columns([1, 1])

    if uploaded_file_client and uploaded_file_interview:
        with st.status("Processing data...", expanded=True) as status:
            results = analyze_files(uploaded_file_client, uploaded_file_interview)
            status.update(
                label="Process complete!", state="complete", expanded=False
            )
            with col1.container():
                st.markdown("### <클라이언트 요구사항 분석>")
                st.write(results["client_analysis"])
                st.session_state["client_analysis"] = results["client_analysis"]
            with col2.container():
                st.markdown("### <인터뷰 핵심 내용 정리>")
                st.write(results["interview_analysis"])
                st.session_state["interview_analysis"] = results["interview_analysis"]
            
            st.session_state["analyze_ready"] = True


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

# Create two columns for the input section
# input_col1, input_col2, input_col3 = st.columns([1, 3, 1])
# with input_col2:
#     task_description = st.text_area(
#         "What would you like to research?",
#         value="Research the latest AI Agent news in February 2025 and summarize each.",
#         height=68
#     )

# Convert Markdown to DOCX using a temporary file
# def convert_md_to_docx(md_text):
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmpfile:
#         pypandoc.convert_text(md_text, "docx", format="md", outputfile=tmpfile.name)
#         tmpfile_path = tmpfile.name

#     # Read the DOCX file into memory
#     with open(tmpfile_path, "rb") as docx_file:
#         docx_data = docx_file.read()

#     return docx_data

if st.session_state["analyze_ready"]:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        start_research = st.button("🚀 Start Analysis", use_container_width=True, type="primary")

    if start_research:

        with st.status("🤖 **Agents at work...**", state="running", expanded=True) as status:
            try:
                with st.container(height=500, border=False):
                    sys.stdout = StreamToExpander(st)
                    crew = GapAnalysisCrew()
                    
                    # 분석 실행
                    final_report = crew.analyze(
                        st.session_state["client_analysis"],
                        st.session_state["interview_analysis"],
                    )
                status.update(label="✅ Analysis completed!", state="complete", expanded=False)

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
        
        # # Convert Markdown to DOCX
        # docx_data = convert_md_to_docx(result_text)
        
        # Display the final result
        st.markdown(result_text)

        # Create download buttons
        st.divider()
        download_col1, download_col2, download_col3 = st.columns([1, 2, 1])
        with download_col2:
            st.markdown("### 📥 Download Research Report")

            # Download as Markdown
            st.download_button(
                label="Download Report as Mardown",
                data=result_text,
                file_name="research_report.md",
                mime="text/markdown",
                help="Download the research report in Markdown format"
            )

            # # Download as DOCX
            # st.download_button(
            #     label="Download as DOCX",
            #     data=docx_data,
            #     file_name="research_report.docx",
            #     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            #     help="Download the research report in Word format"
            # )

            st.session_state["analyze_ready"] = False

        # Renew previous process
        st.session_state["analyze_ready"] = False

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("Made with ❤️ using [CrewAI](https://crewai.com), [Exa](https://exa.ai) and [Streamlit](https://streamlit.io)")
