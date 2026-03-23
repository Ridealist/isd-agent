# Handle SQLite for ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except (ImportError, KeyError):
    pass

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import logging
import os
import pytz
import sys
import streamlit as st

from datetime import datetime

from src.components.sidebar import render_sidebar
from src.components.researcher import GapAnalysisCrew, StreamToExpander
# [DISABLED] AWS DynamoDB 연동 import
# DynamoDBManager: 분석 결과를 DynamoDB/S3에 저장하는 클래스 (src/components/db.py 참고)
# 재활성화 시 아래 주석 해제 및 start_research/reanalyze 블록 내 db_manager 호출 코드 주석 해제 필요
# from src.components.db import DynamoDBManager
from src.components.prompts import (
    PERFORMANCE_ANALYSIS_PROMPT,
    ACHIEVEMENT_ANALYSIS_PROMPT,
    ENVIRONMENT_ANALYSIS_PROMPT,
    SOLUTION_ANALYSIS_PROMPT
)


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

if "other_files_analysis" not in st.session_state:
    st.session_state["other_files_analysis"] = None

if "final_report" not in st.session_state:
    st.session_state["final_report"] = None

# Initialize prompt states if not exists
if "performance_prompt" not in st.session_state:
    st.session_state["performance_prompt"] = PERFORMANCE_ANALYSIS_PROMPT["user"]
if "achievement_prompt" not in st.session_state:
    st.session_state["achievement_prompt"] = ACHIEVEMENT_ANALYSIS_PROMPT["user"]
if "environment_prompt" not in st.session_state:
    st.session_state["environment_prompt"] = ENVIRONMENT_ANALYSIS_PROMPT["user"]
if "solution_prompt" not in st.session_state:
    st.session_state["solution_prompt"] = SOLUTION_ANALYSIS_PROMPT["user"]


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

# 로그인 기능 비활성화 (주석 처리)
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False

# 로그인 없이 바로 접근 가능하도록 설정
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True  # 항상 로그인된 상태로 설정

if "analyze_ready" not in st.session_state:
    st.session_state["analyze_ready"] = False

if "is_end" not in st.session_state:
    st.session_state["is_end"] = False


# 로그인 체크 비활성화 (주석 처리)
# if st.session_state["logged_in"]:
# Main layout
col1, col2, col3 = st.columns([1, 10, 1])
with col2:
    st.title("🔍 :red[ISD Agent] 수행 문제 분석 도우미", anchor=False)

    with st.expander("See Summarization"):
        prev_col1, prev_col2 = st.columns([1, 1])

        with prev_col1.container():
            if st.session_state["client_analysis"]:
                st.markdown("### <클라이언트 요구사항 분석>")
                st.write(st.session_state["client_analysis"])
        with prev_col2.container():
            if st.session_state["interview_analysis"]:
                st.markdown("### <인터뷰 핵심 내용 정리>")
                st.write(st.session_state["interview_analysis"])
        
        if st.session_state["other_files_analysis"]:
            st.markdown("### <기타 파일 통합 분석>")
            st.write(st.session_state["other_files_analysis"])

    # Add prompt editing section
    with st.expander("📝 프롬프트 수정", expanded=False):
        st.markdown("### 프롬프트 수정")
        st.markdown("분석에 사용될 프롬프트를 수정할 수 있습니다.")
        
        performance_prompt_update = st.text_area(
            label="<수행 분석 프롬프트>",
            value=st.session_state["performance_prompt"],
            height=200
        )
        st.session_state["performance_prompt"] = performance_prompt_update

        achievement_prompt_update = st.text_area(
            label="<성과 분석 프롬프트>",
            value=st.session_state["achievement_prompt"],
            height=200
        )
        st.session_state["achievement_prompt"] = achievement_prompt_update

        environment_prompt_update = st.text_area(
            label="<환경 분석 프롬프트>",
            value=st.session_state["environment_prompt"],
            height=200
        )
        st.session_state["environment_prompt"] = environment_prompt_update

        solution_prompt_update = st.text_area(
            label="<원인 및 해결방안 분석 프롬프트>",
            value=st.session_state["solution_prompt"],
            height=200
        )
        st.session_state["solution_prompt"] = solution_prompt_update

    # Render sidebar and get selection (provider and model)
    selection = render_sidebar()

    # Check if API keys are set based on provider
    if selection["provider"] == "OpenAI":
        if not os.environ.get("OPENAI_API_KEY"):
            st.warning("⚠️ Please enter your OpenAI API key in the sidebar to get started")
            st.stop()

    if st.session_state["analyze_ready"]:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            start_research = st.button("🚀 Start Analysis", use_container_width=True, type="primary")

        if start_research:
            if st.session_state["is_end"] and st.session_state["final_report"]:
                with st.expander(label="✅ Analysis completed!", expanded=False):
                    st.markdown(st.session_state["final_report"])
            else:
                with st.status("🏗️ **Agents at work...**", state="running", expanded=True) as status:
                    try:
                        # [DISABLED] AWS DynamoDB 세션 초기화 (최초 분석)
                        # GapAnalysis 시작 시 DynamoDB 매니저 및 KST 타임스탬프 초기화
                        # db_manager = DynamoDBManager()
                        # kst = pytz.timezone('Asia/Seoul')
                        # timestamp = datetime.now(kst).isoformat()

                        with st.container(height=500, border=False):
                            sys.stdout = StreamToExpander(st)
                            crew = GapAnalysisCrew(
                                client_analysis=st.session_state["client_analysis"],
                                interview_analysis=st.session_state["interview_analysis"],
                                other_files_analysis=st.session_state["other_files_analysis"],
                                performance_prompt=st.session_state["performance_prompt"],
                                achievement_prompt=st.session_state["achievement_prompt"],
                                environment_prompt=st.session_state["environment_prompt"],
                                solution_prompt=st.session_state["solution_prompt"],
                            )

                            final_report = crew.analyze(
                                st.session_state["client_analysis"],
                                st.session_state["interview_analysis"],
                                st.session_state["other_files_analysis"],
                            )

                            st.session_state["final_report"] = final_report

                            # [DISABLED] S3 업로드 + DynamoDB 저장: GapAnalysis 최종 보고서
                            # db_manager.insert_chat_data(
                            #     student_id=st.session_state["session_id"],
                            #     timestamp=timestamp,
                            #     who="agent",
                            #     content=str(final_report),
                            #     context="gap_analysis"
                            # )

                        status.update(label="✅ Analysis completed!", state="complete", expanded=False)
                        st.session_state["is_end"] = True

                    except Exception as e:
                        status.update(label="❌ Error occurred", state="error")
                        st.error(f"An error occurred: {str(e)}")
                        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
                        st.stop()
        
        # 분석 결과가 있을 때만 결과와 재분석 옵션 표시
        if st.session_state["is_end"] and st.session_state["final_report"]:
            # 결과 표시
            with st.container(height=500, border=True):
                st.markdown(st.session_state["final_report"])
            
            # 사용자 입력 섹션
            st.markdown("### 분석에 추가할 내용이 있으신가요?")
            st.markdown("아래에 추가 정보나 특정 관점에서 분석을 원하시는 내용을 입력해주세요.")
            user_input = st.text_area(
                "추가 분석 지시사항",
                placeholder="예시: 교육 효과를 높이기 위한 방법에 중점을 두고 분석해주세요 / 신입 직원 교육에 초점을 맞춰주세요",
                height=100
            )

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                reanalyze = st.button("🔄 Re-Analysis", use_container_width=True)

            # 사용자 입력으로 다시 분석하기 버튼이 클릭되었을 때
            if reanalyze:
                if not user_input:
                    st.error("추가 분석 지시사항을 입력해주세요.")
                else:
                    with st.status("🔄 **Reanalyzing with your input...**", state="running", expanded=True) as status:
                        try:
                            # [DISABLED] AWS DynamoDB 세션 초기화 (재분석)
                            # 재분석 시작 시 DynamoDB 매니저 및 KST 타임스탬프 초기화
                            # db_manager = DynamoDBManager()
                            # kst = pytz.timezone('Asia/Seoul')
                            # timestamp = datetime.now(kst).isoformat()

                            with st.container(height=500, border=False):
                                sys.stdout = StreamToExpander(st)
                                crew = GapAnalysisCrew(
                                    client_analysis=st.session_state["client_analysis"],
                                    interview_analysis=st.session_state["interview_analysis"],
                                    other_files_analysis=st.session_state["other_files_analysis"],
                                    user_input=user_input,
                                    performance_prompt=st.session_state["performance_prompt"],
                                    achievement_prompt=st.session_state["achievement_prompt"],
                                    environment_prompt=st.session_state["environment_prompt"],
                                    solution_prompt=st.session_state["solution_prompt"],
                                )
                                
                                # 사용자 입력을 추가 파라미터로 전달
                                final_report = crew.analyze(
                                    st.session_state["client_analysis"],
                                    st.session_state["interview_analysis"],
                                    st.session_state["other_files_analysis"],
                                    user_input=user_input
                                )
                                
                                st.session_state["final_report"] = final_report

                                # [DISABLED] S3 업로드 + DynamoDB 저장: GapAnalysis 재분석 보고서
                                # db_manager.insert_chat_data(
                                #     student_id=st.session_state["session_id"],
                                #     timestamp=timestamp,
                                #     who="agent",
                                #     content=str(final_report),
                                #     context="gap_analysis_reanalyzed"
                                # )

                            status.update(label="✅ Reanalysis completed!", state="complete", expanded=True)

                        except Exception as e:
                            status.update(label="❌ Error occurred", state="error")
                            st.error(f"An error occurred: {str(e)}")
                            st.stop()

    # 다음 단계로 버튼
    mov_col1, mov_col2, mov_col3 = st.columns([1, 1, 1])
    with mov_col1:
        if st.button(
            label="이전단계로",
            icon="⏪",
            type="primary",
            use_container_width=True
        ):
            st.switch_page("pages/01_요약하기.py")

    if st.session_state["is_end"] and st.session_state["final_report"]:
        with mov_col3:
            if st.session_state["analyze_ready"]:
                if st.button(
                    label="다음단계로",
                    icon="⏩",
                    type="primary",
                    use_container_width=True
                ):
                    st.switch_page("pages/03_정리하기.py")
# 로그인 체크 비활성화 (주석 처리)
# else:
#     st.error("먼저 로그인을 해주세요!")

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("Made with ❤️ using [CrewAI](https://crewai.com) and [Streamlit](https://streamlit.io)")