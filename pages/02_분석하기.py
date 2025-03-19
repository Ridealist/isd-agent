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
import streamlit as st

from datetime import datetime

from src.components.sidebar import render_sidebar
from src.components.researcher import GapAnalysisCrew, StreamToExpander
from src.components.db import DynamoDBManager


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

if "final_report" not in st.session_state:
    st.session_state["final_report"] = None


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
            if st.session_state["is_end"] and st.session_state["final_report"]:
                with st.expander(label="✅ Analysis completed!", expanded=False):
                    st.markdown(st.session_state["final_report"])
            else:
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
    #                         final_report = """
    # # 해결방안 종합 보고서

    # ## 1. 수행 문제(1) 고객 응대 능력 부족

    # ### 1.1. 수행 문제 상황
    # 서비스센터 엔지니어들이 고객 응대 시 필요한 기술 및 소통 능력을 충분히 발휘하지 못하여, 고객 평가 점수가 일관되게 낮게 나타남.

    # ### 1.2. 원인 분석
    # - **교육적 요인**: 기존의 고객 응대 교육이 실제 현장 상황을 반영하지 못하고 형식적으로 진행되어, 엔지니어들이 실질적인 응대 기술을 습득하지 못함.
    # - **환경적 요인**: 고객 평가가 성과급과 직접 연결되어 있어 엔지니어들이 높은 스트레스를 경험, 이는 고객 응대 시 집중력 저하로 이어짐.
    # - **개인적 요인**: 신입 엔지니어에 대한 현장 교육 부족으로 인해, 실무에 필요한 소통 능력이 초기부터 제대로 배양되지 않음.

    # ### 1.3. 교육적 해결안
    # - **맞춤형 교육 프로그램 개발**: 개인별로 부족한 소통 능력과 기술적 역량을 파악하여, 개별화된 교육 커리큘럼을 제공.
    # - **롤플레잉 및 상황별 훈련 강화**: 실제 고객 응대 상황을 시뮬레이션하는 롤플레잉 세션을 도입하여, 실전 감각을 향상시킴.
    # - **지속적인 피드백 시스템 도입**: 교육 과정 후 엔지니어들의 응대 실습을 평가하고 즉각적인 피드백을 제공하여 지속적인 개선을 유도.

    # ### 1.4. 교육외적 해결안
    # - **스트레스 관리 프로그램 시행**: 정기적인 심리 상담 및 스트레스 관리 워크숍을 통해 엔지니어들의 심리적 부담을 경감.
    # - **인센티브 제도 개선**: 긍정적인 고객 평가에 대한 추가 인센티브를 제공하여, 긍정적인 동기 부여를 강화.

    # ## 2. 수행 문제(2) 교육의 비효율성

    # ### 2.1. 수행 문제 상황
    # 기존의 고객 응대 교육이 현장 상황을 충분히 반영하지 못해, 엔지니어들이 교육 내용을 실제 업무에 적용하기 어려움.

    # ### 2.2. 원인 분석
    # - **교육 내용의 부적합성**: 현장에서의 구체적인 문제 상황과 일치하지 않는 일반적인 교육 내용으로 인해 실효성이 낮음.
    # - **교육 방식의 한계**: 이론 중심의 강의식 교육만으로는 실제 응대 상황에서 필요한 실습이 부족함.
    # - **교육 참여의 제약**: 모든 서비스센터 직원이 참여할 수 있는 유연한 교육 일정 및 방식이 부족하여, 일관된 교육 효과를 거두지 못함.

    # ### 2.3. 교육적 해결안
    # - **현장 경험 반영 교육 커리큘럼 설계**: 현장에서 자주 발생하는 사례를 반영한 실무 중심의 교육 자료 개발.
    # - **혼합 학습 방식 도입**: 온라인과 오프라인을 병행한 혼합 학습 방식을 도입하여, 각 직원의 일정에 맞추어 유연하게 교육 참여를 가능하게 함.
    # - **실습 중심의 워크숍 개최**: 이론 교육 후 실제 응대 상황을 재현한 실습 워크숍을 주기적으로 개최하여, 실전 능력 향상 도모.

    # ### 2.4. 교육외적 해결안
    # - **교육 효과성 평가 기준 마련**: 교육 후 고객 만족도 지수와 엔지니어 피드백을 기반으로 교육 효과를 체계적으로 평가하고, 이를 바탕으로 교육 내용을 지속적으로 개선.
    # - **경쟁사 비교 분석을 통한 차별화**: 경쟁사의 교육 프로그램과 비교 분석을 실시하여, 차별화된 교육 콘텐츠 및 방식을 개발.

    # ## 3. 수행 문제(3) 단발성 교육의 한계

    # ### 3.1. 수행 문제 상황
    # 현재 진행되는 교육이 일회성으로 이루어져, 지속적이고 맞춤형 교육이 부족하여 엔지니어들의 서비스 역량 향상에 한계가 있음.

    # ### 3.2. 원인 분석
    # - **지속적인 교육 프로그램 부재**: 일회성 교육 후 지속적인 팔로업이 없어, 교육 효과가 시간이 지남에 따라 감소함.
    # - **맞춤형 교육의 부재**: 개별 엔지니어의 필요에 맞춘 맞춤형 교육이 제공되지 않아, 전체적인 교육의 효율성이 저하됨.
    # - **평가 및 피드백 시스템 미비**: 교육 후 성과를 측정하고 피드백을 제공하는 체계가 마련되지 않아, 교육의 지속적 개선이 어려움.

    # ### 3.3. 교육적 해결안
    # - **지속적인 교육 프로그램 도입**: 정기적인 교육 세션을 계획하여, 지속적인 학습과 역량 강화를 지원.
    # - **맞춤형 학습 경로 제공**: 각 엔지니어의 역량과 필요에 따라 개인화된 학습 경로를 설정하고, 이에 맞는 교육 콘텐츠를 제공.
    # - **교육 후 성과 추적 및 피드백 시스템 구축**: 교육 후 엔지니어들의 성과를 지속적으로 추적하고, 정기적인 피드백을 통해 교육의 효과성을 높임.

    # ### 3.4. 교육외적 해결안
    # - **커뮤니티 및 멘토링 프로그램 운영**: 엔지니어들 간의 지식 공유와 경험 전수를 위한 커뮤니티 및 멘토링 프로그램을 운영하여, 지속적인 학습 환경을 조성.
    # - **기술 및 서비스 트렌드 업데이트**: 최신 기술 및 서비스 트렌드를 반영한 교육 내용을 지속적으로 업데이트하여, 변화하는 현장 환경에 적응할 수 있도록 지원.

    # ## 결론
    # 본 보고서는 클라이언트의 요구사항과 인터뷰 분석 결과를 기반으로 서비스센터 직원들의 주요 수행 문제를 도출하고, 각각의 문제에 대한 원인 분석과 교육적 및 교육외적 해결 방안을 제시하였습니다. 이를 통해 효과적인 교육 프로그램 개발과 지속적인 서비스 향상을 도모할 수 있을 것입니다.
    # """

                            st.session_state["final_report"] = final_report

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
                            # Initialize DynamoDB manager
                            db_manager = DynamoDBManager()
                            # Get current time in KST
                            kst = pytz.timezone('Asia/Seoul')
                            timestamp = datetime.now(kst).isoformat()

                            with st.container(height=500, border=False):
                                sys.stdout = StreamToExpander(st)
                                crew = GapAnalysisCrew(
                                    client_analysis=st.session_state["client_analysis"],
                                    interview_analysis=st.session_state["interview_analysis"],
                                    user_input=user_input
                                )
                                
                                # 사용자 입력을 추가 파라미터로 전달
                                final_report = crew.analyze(
                                    st.session_state["client_analysis"],
                                    st.session_state["interview_analysis"],
                                    user_input=user_input
                                )
                                
                                st.session_state["final_report"] = final_report

                                # Save analysis results to DynamoDB
                                db_manager.insert_chat_data(
                                    student_id=st.session_state["session_id"],
                                    timestamp=timestamp,
                                    who="agent",
                                    content=str(final_report),
                                    context="gap_analysis_reanalyzed"
                                )

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
else:
    st.error("먼저 로그인을 해주세요!")

# Add footer
st.divider()
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("Made with ❤️ using [CrewAI](https://crewai.com) and [Streamlit](https://streamlit.io)")