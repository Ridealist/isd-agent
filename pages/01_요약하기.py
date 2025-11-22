# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import magic
import PyPDF2
import io
import logging
import os
import pytz  # Add this import at the top with other imports
import uuid  # Add this import at the top with other imports
import streamlit as st
import sys

from datetime import datetime

from src.components.llm import get_chat_completion
from src.components.prompts import CLIENT_REQUIREMENTS_PROMPT, INTERVIEW_PROMPT, RELATED_DOCUMENTS_PROMPT
from src.components.sidebar import render_sidebar
from src.components.db import DynamoDBManager


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#--------------------------------#
#         Streamlit App          #
#--------------------------------#
# Configure the page
st.set_page_config(
    page_title="ISD Agent",
    page_icon="🕵️",
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

# 로그인 기능 비활성화 (주석 처리)
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False

# 로그인 없이 바로 접근 가능하도록 설정
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True  # 항상 로그인된 상태로 설정

# Initialize UUID for the session if not already present
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "client_analysis" not in st.session_state:
    st.session_state["client_analysis"] = None

if "interview_analysis" not in st.session_state:
    st.session_state["interview_analysis"] = None

if "other_files_analysis" not in st.session_state:
    st.session_state["other_files_analysis"] = None

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


# 로그인 체크 비활성화 (주석 처리)
# if st.session_state["logged_in"]:
# Main layout
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.title("🔍 :red[ISD Agent] 수행 문제 분석 도우미", anchor=False)


    # Add other files prompt to the prompt editing section
    with st.expander("📝 프롬프트 수정", expanded=False):
        st.markdown("### 프롬프트 수정")
        st.markdown("분석에 사용될 프롬프트를 수정할 수 있습니다.")
        
        # Initialize prompt states if not exists
        if "client_prompt" not in st.session_state:
            st.session_state["client_prompt"] = CLIENT_REQUIREMENTS_PROMPT["user"]
        if "interview_prompt" not in st.session_state:
            st.session_state["interview_prompt"] = INTERVIEW_PROMPT["user"]
        if "other_files_prompt" not in st.session_state:
            st.session_state["other_files_prompt"] = RELATED_DOCUMENTS_PROMPT["user"]

        # Add text areas for prompt editing
        st.session_state["client_prompt"] = st.text_area(
            "<클라이언트 요구사항 분석 프롬프트>",
            value=st.session_state["client_prompt"],
            height=200
        )
        
        st.session_state["interview_prompt"] = st.text_area(
            "<인터뷰 분석 프롬프트>",
            value=st.session_state["interview_prompt"],
            height=200
        )

        st.session_state["other_files_prompt"] = st.text_area(
            "<기타 파일 분석 프롬프트>",
            value=st.session_state["other_files_prompt"],
            height=200
        )

    st.subheader("클라이언트 요구사항 파일")
    uploaded_file_client = st.file_uploader(
        label="클라이언트 인터뷰 - **'PDF 파일 형식'만 가능**",
        type="pdf",
        accept_multiple_files=False
    )
    # if uploaded_file_client:
    #     bytes_data = uploaded_file_client.read()
    #     full_text = process_pdf_file(uploaded_file_client)
    #     # st.write("file content:", full_text)
    #     # st.write(bytes_data)

    st.subheader("인터뷰 내용 파일")
    uploaded_file_interview = st.file_uploader(
        label="인터뷰 기록 - **'PDF 파일 형식'만 가능**",
        type='pdf',
        accept_multiple_files=False
    )
    # if uploaded_file_interview:
    #     bytes_data = uploaded_file_interview.read()
    #     full_text = process_pdf_file(uploaded_file_interview)
    #     # st.write("file content:", full_text)
    #     # st.write(bytes_data)

    # Add other files section
    st.subheader("기타 분석 파일")
    uploaded_files_other = st.file_uploader(
        label="기타 분석 파일 - **'PDF 파일 형식'으로 여러 파일 업로드 가능**",
        type='pdf',
        accept_multiple_files=True,
        help="여러 개의 파일을 업로드할 수 있습니다."
    )


    def analyze_files(client_file=None, interview_file=None, other_files=None):
        logger.info("Received analysis request")
        
        # DynamoDB 매니저 초기화
        db_manager = DynamoDBManager()
        # Get current time in KST
        kst = pytz.timezone('Asia/Seoul')
        timestamp = datetime.now(kst).isoformat()
        
        results = {
            "status": "success",
            "client_analysis": None,
            "interview_analysis": None,
            "other_files_analysis": None
        }
        
        # 클라이언트 파일 처리
        if client_file:
            client_content = process_pdf_file(client_file)
            # Combine editable prompt with system template
            client_prompt = CLIENT_REQUIREMENTS_PROMPT["system"].format(
                text=client_content,
                analysis_guide=st.session_state["client_prompt"]
            )
            
            # 사용자 입력 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=timestamp,
                who="user",
                content=client_content,
                context="requirements_analysis"
            )
            
            client_analysis = get_chat_completion(client_prompt)
            results["client_analysis"] = client_analysis
            
            # AI 응답 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=datetime.now(kst).isoformat(),
                who="agent",
                content=client_analysis,
                context="requirements_analysis"
            )
        
        # 인터뷰 파일 처리
        if interview_file:
            interview_content = process_pdf_file(interview_file)
            # Combine editable prompt with system template
            interview_prompt = INTERVIEW_PROMPT["system"].format(
                text=interview_content,
                analysis_guide=st.session_state["interview_prompt"]
            )
            
            # 사용자 입력 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=datetime.now(kst).isoformat(),
                who="user",
                content=interview_content,
                context="interview_analysis"
            )
            
            interview_analysis = get_chat_completion(interview_prompt)
            results["interview_analysis"] = interview_analysis
            
            # AI 응답 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=datetime.now(kst).isoformat(),
                who="agent",
                content=interview_analysis,
                context="interview_analysis"
            )
        
        # 기타 파일 처리 - 모든 파일 내용을 하나로 합침
        if other_files:
            combined_content = ""
            for file in other_files:
                file_content = process_pdf_file(file)
                combined_content += f"\n\n=== {file.name} ===\n{file_content}"
            
            # Combine editable prompt with system template
            other_prompt = RELATED_DOCUMENTS_PROMPT["system"].format(
                text=combined_content,
                analysis_guide=st.session_state["other_files_prompt"]
            )
            
            # 사용자 입력 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=datetime.now(kst).isoformat(),
                who="user",
                content=combined_content,
                context="other_files_analysis"
            )
            
            combined_analysis = get_chat_completion(other_prompt)
            results["other_files_analysis"] = combined_analysis
            
            # AI 응답 저장
            db_manager.insert_chat_data(
                student_id=st.session_state["session_id"],
                timestamp=datetime.now(kst).isoformat(),
                who="agent",
                content=combined_analysis,
                context="other_files_analysis"
            )
        
        return results


    bt_col1, bt_col2, bt_col3 = st.columns([1, 1, 1])
    with bt_col2:
        button_analyze = st.button(label="📝 Summarize Documents", type="primary", use_container_width=True)

    if button_analyze:
        # Check if at least one file is uploaded
        if uploaded_file_client or uploaded_file_interview or (uploaded_files_other and len(uploaded_files_other) > 0):
            with st.status("Processing data...", expanded=True) as status:
                results = analyze_files(uploaded_file_client, uploaded_file_interview, uploaded_files_other)
                status.update(
                    label="Process complete!", state="complete", expanded=False
                )
                st.session_state["analyze_ready"] = True
                st.session_state["client_analysis"] = results["client_analysis"]
                st.session_state["interview_analysis"] = results["interview_analysis"]
                st.session_state["other_files_analysis"] = results["other_files_analysis"]
        else:
            st.warning("⚠️ 분석을 위해 최소한 하나의 파일을 업로드해주세요.")

    # Display existing analysis results
    if st.session_state["client_analysis"] or st.session_state["interview_analysis"] or st.session_state["other_files_analysis"]:
        st.subheader("주요 파일 분석 결과")
        col1, col2 = st.columns([1, 1])
        # Display client analysis if exists
        if st.session_state["client_analysis"]:
            with col1.container():
                client_analysis_update = st.text_area(
                    label="<클라이언트 요구사항 분석>",
                    value=st.session_state["client_analysis"],
                    height=500
                )
                st.session_state["client_analysis"] = client_analysis_update
    
        if st.session_state["interview_analysis"]:
            with col2.container():
                interview_analysis_update = st.text_area(
                    label="<인터뷰 핵심 내용 정리>",
                    value=st.session_state["interview_analysis"],
                    height=500
                )
                st.session_state["interview_analysis"] = interview_analysis_update

        # Display other files analysis if exists
        if st.session_state["other_files_analysis"]:
            st.subheader("기타 파일 분석 결과")
            other_files_analysis_update = st.text_area(
                label="<기타 파일 통합 분석>",
                value=st.session_state["other_files_analysis"],
                height=300
            )
            st.session_state["other_files_analysis"] = other_files_analysis_update

    # Render sidebar and get selection (provider and model)
    selection = render_sidebar()

    # Check if API keys are set based on provider
    if selection["provider"] == "OpenAI":
        if not os.environ.get("OPENAI_API_KEY"):
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started")
            st.stop()

    # # 다음 단계로 버튼
    mov_col1, mov_col2, mov_col3 = st.columns([1, 1, 1])
    with mov_col3:
        if st.session_state["analyze_ready"]:
            if st.button(
                label="다음단계로",
                icon="⏩",
                help="분석하기로 이동하기",
                type="primary",
                use_container_width=True
            ):
                st.switch_page("pages/02_분석하기.py")
# 로그인 체크 비활성화 (주석 처리)
# else:
#     st.error("먼저 로그인을 해주세요!")

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("ISD Agent는 실수를 할 수 있습니다. 응답을 다시 한 번 확인하고 비판적으로 검토해주세요.")