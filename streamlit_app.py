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

#     client_content = """
# 고객의 요구사항 문서를 기반으로 다음과 같이 분석하여 정리했습니다.

# 1. **프로젝트의 핵심 목표**
#    - 서비스센터 직원들의 서비스 역량을 개선하기 위한 교육 프로그램 개발.
#    - DE CS 마인드를 특히 강화하여 고객 만족도를 높이는 것을 목표로 함.

# 2. **주요 요구사항 목록**
#    - 서비스센터 직원들이 DE CS 마인드를 이해하고 적용할 수 있는 교육 내용 포함.
#    - 고객 만족도 지수를 높이기 위한 실질적인 서비스 기술 교육 제공.
#    - 서비스 관련 교육의 효과성 평가를 위한 기준 마련.
#    - 교육 프로그램은 모든 서비스센터 직원이 참여할 수 있도록 유연한 형태로 설계.

# 3. **제약사항이나 특별 고려사항**
#    - 서비스센터 직원들은 개별 사업자 소속이므로, 교육 프로그램이 각 센터의 운영에 실질적으로 적용될 수 있어야 함.
#    - 현재 제공된 교육의 내용과 형식이 직원들에게 유용한지 검토 후 개선 방안 제시가 필요.
#    - 경쟁사와의 비교 분석을 통해 차별화된 교육 프로그램 개발이 요구됨.
#    - 직원의 서비스 향상을 위해 실시간 피드백과 평가 프로그램 필요.

# 4. **기대하는 결과물**
#    - 개발된 교육 프로그램과 매뉴얼: DE CS 마인드 관련 자료와 서비스 기술 훈련 모듈 포함.
#    - 교육 효과 평가 리포트: 교육 후 고객 만족도 지수 변화 및 직원 피드백 결과 포함.
#    - 고객 만족도 지수 개선 목표 수치 도출 및 이를 달성하기 위한 실행 계획. 

# 이와 같은 분석을 통해 요구사항을 명확히 파악하고, 교육 프로그램 개발 방향성을 설정할 수 있습니다.
# """

#     interview_content = """
# ### 1. 인터뷰 대상자의 주요 관심사
# - **고객 평가**: 고객 평가가 성과급과 연결되어 있어, 엔지니어들이 평가에 대한 높은 스트레스를 느끼고 있습니다. 고객의 성향 파악과 고객 응대 능력이 중요함을 강조합니다.
# - **기술과 소통의 균형**: 기술적인 능력 외에 고객 응대나 소통 능력이 더 중요하다는 인식이 있습니다. 특히 기술을 잘 알고도 고객 질문에 당황하는 사례를 지적합니다.
# - **업무의 편차**: 담당하는 제품에 따라 업무량이 달라지며, 이는 엔지니어의 수입에 직접적인 영향을 미친다는 점도 주요 관심사입니다.

# ### 2. 파악된 문제점이나 니즈
# - **고객 응대 능력 부족**: 엔지니어들이 고객 응대 시 필요한 기술이나 소통 능력이 부족한 경우가 많아, 낮은 평가를 받는 경우가 발생합니다.
# - **교육의 비효율성**: 기존 고객 응대 교육이 현장 상황을 반영하지 못하고, 엔지니어들이 형식적으로 교육을 이행하여 실제 상황에 적용하기 어렵습니다.
# - **신입 교육 부족**: 신입 엔지니어에 대한 현장교육이 미비하여, 실무에 필요한 기술 습득과 고객 응대 능력이 제대로 배양되지 않고 있습니다.
# - **단발성 교육의 한계**: 현재 진행되는 교육이 일회성으로, 지속적이고 맞춤형 교육이 부족합니다.

# ### 3. 제안된 해결방안이나 아이디어
# - **맞춤형 교육 필요성**: 개인별 문제점(예: 고객 응대, 기술 문제 등)을 파악하고 코칭하여 맞춤형 교육을 시행해야 한다는 아이디어가 제안되었습니다.
# - **현장 경험 반영**: 실제 현장의 어려움과 경험자들의 의견을 반영하여 교육 프로그램을 개선해야 한다는 필요성이 있습니다.
# - **지속적인 평가 및 피드백**: 교육이 끝난 후에도 데이터를 기반으로 지속적으로 엔지니어의 성과를 관리하고 평가해야 하며, 정기적으로 코칭을 해야 한다는 제안이 있습니다.
# - **롤플레잉과 상황별 훈련 강화**: 롤플레잉을 통한 고객 응대 교육을 보다 효과적으로 수행하고, 실제 고객 상황에 맞춘 훈련 방식으로 개선해야 한다고 언급되었습니다.

# ### 4. 추가 고려사항이나 피드백
# - **업무과량**: 엔지니어들이 만나는 고객 수가 많고, 한 번에 여러 기계를 수리해야 하기에 일정한 업무 배분이 어려워 효율성이 떨어지는 측면도 고려해야 합니다. 이에 대한 개선 방안도 필요합니다.
# - **스트레스 관리**: 고객 평가로 인한 스트레스를 줄이기 위해, 긍정적인 평가 시스템 또는 팀워크 중심의 문화 형성이 필요할 수 있습니다.
# - **계속적인 교육과 업데이트**: 교육 내용은 실제 변화하는 현장 환경이나 기술 발전에 맞추어 지속적으로 업데이트되어야 하는 사항도 강조해야 합니다.
# """

    if uploaded_file_client and uploaded_file_interview:
        with st.status("Processing data...", expanded=True) as status:
            results = analyze_files(uploaded_file_client, uploaded_file_interview)
            status.update(
                label="Process complete!", state="complete", expanded=False
            )
            with col1.container():
                st.markdown("### <클라이언트 요구사항 분석>")
                # st.write(client_content)
                # st.session_state["client_analysis"] = client_content
                st.write(results["client_analysis"])
                st.session_state["client_analysis"] = results["client_analysis"]
            with col2.container():
                st.markdown("### <인터뷰 핵심 내용 정리>")
                # st.write(interview_content)
                # st.session_state["interview_analysis"] = interview_content
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
                    crew = GapAnalysisCrew(
                        client_analysis=st.session_state["client_analysis"],
                        interview_analysis=st.session_state["interview_analysis"]
                    )

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
