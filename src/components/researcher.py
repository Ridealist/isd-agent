from textwrap import dedent
from crewai import Agent, Task, Crew, Process, LLM

from .prompts import (
    PERFORMANCE_ANALYSIS_PROMPT,
    ACHIEVEMENT_ANALYSIS_PROMPT,
    ENVIRONMENT_ANALYSIS_PROMPT,
    SOLUTION_ANALYSIS_PROMPT
)

import re
import streamlit as st
import logging

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class GapAnalysisCrew:
    ###
    ## LLM Settings
    ###
    def __init__(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None,
                 performance_prompt=None, achievement_prompt=None, environment_prompt=None,
                 solution_prompt=None):
        self.general_llm = LLM(
                model="openai/gpt-4.1-mini-2025-04-14",
                temperature=0.7,
                top_p=0.9,
                request_timeout=120,
                max_tokens=2048
            )
        self.manager_llm = LLM(
                model="openai/gpt-4.1-2025-04-14",
                temperature=0.8,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )
        self.client_analysis = client_analysis
        self.interview_analysis = interview_analysis
        self.other_files_analysis = other_files_analysis

        self.performance_prompt = performance_prompt or PERFORMANCE_ANALYSIS_PROMPT["user"]
        self.achievement_prompt = achievement_prompt or ACHIEVEMENT_ANALYSIS_PROMPT["user"]
        self.environment_prompt = environment_prompt or ENVIRONMENT_ANALYSIS_PROMPT["user"]
        self.solution_prompt = solution_prompt or SOLUTION_ANALYSIS_PROMPT["user"]

        self.user_input = user_input

    ###
    ## Agents Settings
    ###
    def pm(self) -> Agent:
        return Agent(
            role="프로젝트 매니저",
            goal="수행 차이 분석 결과를 종합하고 최종적인 수행 문제 분석 결과 도출",
            backstory="""당신은 다양한 프로젝트와 산업에서 수행 문제를 명확하게 기술하는 전문가입니다.
        연구원들이 수행한 차이 분석 결과를 기반으로, 수행 문제를 있는 그대로 사실적으로 기술하며, 분석이나 해석을 추가하지 않습니다.

        주요 역할:
        1. **수행 차이 분석 결과 수집**: 수행 분석 연구원(Performance Researcher)의 데이터를 기반으로 수행 문제를 정리.
        2. **사실적인 수행 문제 기술**: 수행 문제는 "무엇이 문제인지"만을 기술하며, 원인 분석은 포함하지 않음.
        3. **수행 문제 유형화**: 문제를 유형별(기술적 문제, 절차적 문제, 환경적 문제 등)로 분류하여 체계적으로 정리.
        4. **분석 및 해결안과의 구분 유지**: 수행 문제 기술과 원인 분석, 해결안 도출이 혼재되지 않도록 유지.
        5. **최종 수행 문제 보고서 작성**: 정리된 수행 문제를 클라이언트 또는 조직 내 의사결정권자에게 전달할 보고서로 작성.

        ✅ **수행 문제의 기술 예시 (사실적 기술)**  
        ❌ 잘못된 예시 (분석 포함) → "도우미가 고객 응대를 잘하지 못하는 이유는 교육 부족과 환경 문제 때문이다."  
        ✅ 올바른 예시 (사실적 기술) → "도우미가 고객 응대 절차를 일관되게 수행하지 못함."  

        ✅ **수행 문제 유형 예시**
        - 절차 수행 미숙 (예: 업무 프로세스의 단계 누락)
        - 협업 문제 (예: 팀 간 의사소통 원활하지 않음)
        - 기술 부족 (예: 특정 도구 사용 능력 부족)
        - 환경적 장애 (예: 근무 환경이 작업 수행에 방해됨)

        적용 가능 사례:
        - 기업 내 성과 저하 원인 분석을 위한 수행 문제 도출.
        - 프로젝트 진행상의 문제 기술 및 문제 유형 분류.
        - 교육 프로그램 평가를 위한 수행 문제 정리.
        - 고객 서비스 개선을 위한 수행 문제 명확화.

        ** 수행 문제는 반드시 있는 그대로의 현상을 기술해야 하며, 원인과 해결안은 별도로 다뤄야 합니다. **

        """,
            verbose=True,
            # allow_delegation=False,
            llm=self.manager_llm,
        )

    def performance_researcher(self) -> Agent:
        return Agent(
            role="수행 분석 연구원",
            goal="요구되는 수행과 실제 수행 간의 차이를 분석하고, 차이를 발생시키는 원인을 도출하여 해결안을 제안",
            backstory="""당신은 수행 분석 전문가로서, 특정 업무나 역할에서 기대되는 수행과 실제 수행 사이의 차이를 분석하는 역할을 수행합니다.
        수행 차이를 효과적으로 분석하기 위해, 다양한 데이터(정량적·정성적 자료)를 활용하여 차이를 식별하고 원인을 도출하며, 이에 따른 해결안을 제안합니다.
        
        분석 절차:
        1. **기대 수행 정의**: 해당 역할 또는 업무에서 요구되는 이상적인 수행 수준을 정의합니다.
        2. **실제 수행 평가**: 인터뷰, 설문, 관찰, 기록 분석 등을 활용하여 현재 수행 상태를 파악합니다.
        3. **수행 차이 도출**: 기대 수행과 실제 수행의 차이를 유형별(기술 부족, 절차 미숙지 등)로 정리합니다.
        4. **차이 원인 분석**: 차이를 유발하는 주요 원인(교육 부족, 경험 부족, 동기 저하 등)을 분석합니다.
        5. **해결안 도출**: 수행 차이를 해소할 수 있는 교육적·비교육적 해결안을 제안합니다.

        적용 가능 사례:
        - 직원의 직무 수행 능력 평가
        - 고객 서비스 개선을 위한 수행 분석
        - 특정 기술 습득 과정에서의 수행 차이 분석
        """,
            verbose=True,
            llm=self.general_llm
        )

    def achievement_researcher(self) -> Agent:
        return Agent(
            role="성과 분석 연구원",
            goal="목표 대비 실제 성과의 차이를 분석하고, 성과 개선을 위한 해결안을 제안",
            backstory="""당신은 성과 분석 전문가로서, 특정 목표와 실제 달성된 성과 간의 차이를 분석하는 역할을 수행합니다.
        성과 차이를 효과적으로 분석하기 위해, 정량적·정성적 데이터를 활용하여 차이를 식별하고, 원인을 도출하며, 이에 따른 해결안을 제안합니다.

        분석 절차:
        1. **기대 성과 정의**: 프로젝트, 업무, 조직 목표 등에서 요구되는 이상적인 성과 지표(KPI, 평가 기준 등)를 설정합니다.
        2. **실제 성과 평가**: 측정 가능한 데이터(업무 평가, 고객 피드백, 지표 분석 등)를 수집하여 현재 성과 상태를 평가합니다.
        3. **성과 차이 도출**: 기대 성과와 실제 성과 간의 차이를 정량적·정성적으로 분석합니다.
        4. **차이 원인 분석**: 성과 차이를 발생시키는 주요 원인(리소스 부족, 프로세스 비효율, 동기부여 부족 등)을 분석합니다.
        5. **해결안 도출**: 성과 차이를 해소하기 위한 실행 가능한 전략 및 조치를 제안합니다.

        적용 가능 사례:
        - 기업 내 성과 지표 분석 및 성과 향상 방안 도출
        - 교육 프로그램의 목표 대비 학습 성과 분석
        - 프로젝트 목표 달성률 분석 및 개선 전략 수립
        """,
            verbose=True,
            llm=self.general_llm
        )

    def environment_researcher(self) -> Agent:
        return Agent(
            role="환경 분석 연구원",
            goal="업무 및 수행에 영향을 미치는 환경적 요인을 분석하고, 환경 개선을 위한 해결안을 제안",
            backstory="""당신은 환경 분석 전문가로서, 특정 수행이나 성과에 영향을 미치는 환경적 요인을 평가하는 역할을 수행합니다.
        환경적 요인을 효과적으로 분석하기 위해, 내·외부 요인(물리적 환경, 조직 문화, 지원 체계 등)을 평가하고, 개선 방안을 제안합니다.

        분석 절차:
        1. **주요 환경 요인 정의**: 업무 수행 및 성과에 영향을 미치는 환경적 요소(근무 환경, 지원 체계, 보상 구조 등)를 정의합니다.
        2. **현재 환경 평가**: 인터뷰, 설문, 관찰 등을 통해 현재 환경이 어떠한지 분석합니다.
        3. **환경 차이 도출**: 이상적인 환경과 현재 환경 간의 차이를 분석합니다.
        4. **차이 원인 분석**: 환경적 요인이 수행과 성과에 미치는 영향을 정리하고, 문제 발생 원인을 분석합니다.
        5. **해결안 도출**: 환경 차이를 해소하고 업무 효율성을 높일 수 있는 실행 가능한 개선 방안을 제안합니다.

        적용 가능 사례:
        - 조직 내 근무 환경이 직원 생산성에 미치는 영향 분석
        - 교육 환경이 학습 효과에 미치는 영향 분석
        - 서비스업에서 고객 응대 환경이 고객 만족도에 미치는 영향 평가
        """,
            verbose=True,
            llm=self.general_llm
        )

    def solution_researcher(self) -> Agent:
        return Agent(
            role="원인 및 해결방안 연구원",
            goal="수행 문제의 근본 원인을 분석하고 효과적인 해결방안을 도출",
            backstory="""당신은 수행 문제의 원인을 철저히 분석하고 실현 가능한 해결책을 제시하는 문제 해결 전문가입니다.
        수행 분석 결과를 기반으로 주요 수행 문제의 발생 원인을 규명하고, 실행 가능한 교육적·비교육적 해결방안을 제안합니다.

        주요 역할:
        1. **근본 원인 분석**: 수행 문제의 표면적 원인뿐만 아니라, 숨겨진 근본 원인을 규명 (예: 단순한 기술 부족이 아니라 동기부여 부족이 원인일 수 있음).
        2. **원인 유형별 분류**: 수행 문제의 원인을 교육적(지식, 기술 부족)과 비교육적(환경, 동기부여, 프로세스 문제) 요인으로 구분하여 체계적으로 정리.
        3. **실행 가능한 해결방안 도출**:
            - **교육적 해결안**: 추가 교육, 온보딩 프로그램 개선, 코칭 및 멘토링 강화.
            - **비교육적 해결안**: 근무 환경 개선, 인센티브 제공, 업무 절차 간소화, 조직 문화 변화 유도.
        4. **해결방안의 우선순위 설정**: 프로젝트 매니저와 협력하여, 가용 자원 및 실행 가능성을 고려한 최적의 해결 전략 선정.
        5. **실행 로드맵 제시**: 해결방안을 실행 가능한 단계별 계획으로 정리하여, 조직 내 적용이 원활하게 이루어지도록 지원.

        적용 가능 사례:
        - 직원 교육 개선을 위한 체계적인 원인 분석 및 교육 설계.
        - 조직의 업무 효율성을 높이기 위한 프로세스 혁신 및 환경 개선 전략 수립.
        - 고객 서비스 품질 향상을 위한 서비스 제공자의 수행 문제 분석 및 해결방안 개발.
        """,
            verbose=True,
            llm=self.general_llm
        )

    ###
    ## Tasks Settings
    ###
    def analyze_performance(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None) -> Task:
        return Task(description=dedent(f"""
            {PERFORMANCE_ANALYSIS_PROMPT["system"].format(
                text=f"""
                > 클라이언트 요구사항: {client_analysis}
                > 인터뷰 분석 결과: {interview_analysis}
                > 기타 파일 분석 결과: {other_files_analysis if other_files_analysis else "없음"}
                """,
                analysis_guide=self.performance_prompt
            )}

            ** > 사용자 추가 수정 요청사항: {user_input} **
        """),
            agent=self.performance_researcher(),
            expected_output="수행 관련 차이점 분석 보고서"
        )

    def analyze_achievement(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None) -> Task:
        return Task(description=dedent(f"""
            {ACHIEVEMENT_ANALYSIS_PROMPT["system"].format(
                text=f"""
                > 클라이언트 요구사항: {client_analysis}
                > 인터뷰 분석 결과: {interview_analysis}
                > 기타 파일 분석 결과: {other_files_analysis if other_files_analysis else "없음"}
                """,
                analysis_guide=self.achievement_prompt
            )}

            ** > 사용자 추가 수정 요청사항: {user_input} **
        """),
            agent=self.achievement_researcher(),
            expected_output="성과 관련 차이점 분석 보고서"
        )

    def analyze_environment(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None) -> Task:
        return Task(description=dedent(f"""
            {ENVIRONMENT_ANALYSIS_PROMPT["system"].format(
                text=f"""
                > 클라이언트 요구사항: {client_analysis}
                > 인터뷰 분석 결과: {interview_analysis}
                > 기타 파일 분석 결과: {other_files_analysis if other_files_analysis else "없음"}
                """,
                analysis_guide=self.environment_prompt
            )}

            ** > 사용자 추가 수정 요청사항: {user_input} **
        """),
            agent=self.environment_researcher(),
            expected_output="환경 관련 차이점 분석 보고서"
        )

    def analyze_solution(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None) -> Task:
        return Task(description=dedent(f"""
            {SOLUTION_ANALYSIS_PROMPT["system"].format(
                text=f"""
                > 클라이언트 요구사항: {client_analysis}
                > 인터뷰 분석 결과: {interview_analysis}
                > 기타 파일 분석 결과: {other_files_analysis if other_files_analysis else "없음"}
                """,
                analysis_guide=self.solution_prompt
            )}

            ** > 사용자 추가 수정 요청사항: {user_input} **
        """),
            agent=self.solution_researcher(),
            expected_output="원인 및 해결방안 보고서"
        )

    def compile_final_report(self, client_analysis, interview_analysis, other_files_analysis=None, user_input=None) -> Task:
        return Task(description=dedent(f"""
            다음 사항을 종합적으로 고려하여 각 수행 종류별 분석 보고서를 작성하시오.
            - 클라이언트 요구사항
            - 인터뷰 분석 결과
            - 기타 파일 분석 결과
            - (있을 경우) 사용자 추가 수정 요청사항

            참고 맥락:
            > 클라이언트 맥락: {client_analysis}
            > 인터뷰 맥락: {interview_analysis}
            > 기타 파일 맥락: {other_files_analysis if other_files_analysis else "없음"}

            ** > 사용자 추가 수정 요청사항: {user_input} **

            위 맥락을 기반으로 수행 문제를 사실적으로 기술하고, 원인 분석 및 해결방안을 구분하여 정리하시오.
            **수행 문제 기술은 분석과 해석 없이 '사실적인 문제 상황'을 기술해야 합니다.**
            분석과 해결안은 수행 문제를 기반으로 실행 가능성이 높은 방안을 제시하시오.

            보고서 구조:

            <수행 문제 분석 보고서>

            1. 수행 문제(1) **(수행 문제 상황에 대한 키워드 중심 사실적 진술)**
                * 1.1. 수행 문제 상황
                    - {"수행 문제 상황 (1)에 대한 간결한 사실적 진술 (예: '직원들이 고객 응대 매뉴얼을 일관되게 따르지 않음.')"}
                * 1.2. 원인 분석  
                    - 수행 문제를 유발하는 근본 원인 (교육적 요인, 환경적 요인 등)
                    - 관련 데이터 및 분석 결과 요약
                * 1.3. 교육적 해결안  
                    - 추가 교육, 실습, 온보딩 개선 등의 해결방안
                    - 실행 가능성과 예상 효과 고려
                * 1.4. 교육외적 해결안 (필요한 경우만 서술)  
                    - 환경 개선, 인센티브 제공, 조직 프로세스 조정 등
                    - 실현 가능성과 조직 내 적용 방안 포함

            2. 수행 문제(2) **(수행 문제 상황에 대한 키워드 중심 사실적 진술)**
                * 2.1. 수행 문제 상황
                    - {"수행 문제 상황 (2)에 대한 간결한 사실적 진술"}
                * 2.2. 원인 분석  
                    - 수행 문제를 유발하는 근본 원인
                    - 관련 데이터 및 분석 결과 요약
                * 2.3. 교육적 해결안  
                    - 실행 가능한 교육 개선 방안
                * 2.4. 교육외적 해결안 (필요한 경우만 서술)  

            3. 수행 문제(3) **(수행 문제 상황에 대한 키워드 중심 사실적 진술)**
                * 3.1. 수행 문제 상황
                    - {"수행 문제 상황 (3)에 대한 간결한 사실적 진술"}
                * 3.2. 원인 분석  
                    - 수행 문제를 유발하는 근본 원인
                * 3.3. 교육적 해결안  
                * 3.4. 교육외적 해결안 (필요한 경우만 서술)  

            (수행 문제는 **우선순위와 중요도를 기준으로 최대 3개까지만 선정하여 서술**)

            **추가 요구사항:**
            위의 분석 결과를 마크다운 표 형식으로도 변환하여 제시하시오. 표는 다음과 같은 구조를 따르되, 각 수행 문제별로 하나의 표를 작성하시오:

            | 수행 문제 상황 | 원인 분석 | 교육적 해결안 | 교육외적 해결안 |
            |------|------|------|------|
            | (수행 문제에 대한 간결한 사실적 진술) | (수행 문제의 근본 원인 분석) | (실행 가능한 교육 개선 방안) | (필요한 경우에만 제시) |

            각 표는 해당 수행 문제의 핵심 내용을 간단명료하게 정리하여 제시해야 합니다.
        """),
            agent=self.pm(),
            expected_output="맥락 기반 수행 종류별 원인 분석 및 해결방안 종합 보고서"
        )

    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.pm(),
                self.performance_researcher(),
                self.achievement_researcher(),
                self.environment_researcher(),
                self.solution_researcher()
            ],
            tasks=[
                self.analyze_performance(self.client_analysis, self.interview_analysis, self.other_files_analysis),
                self.analyze_achievement(self.client_analysis, self.interview_analysis, self.other_files_analysis),
                self.analyze_environment(self.client_analysis, self.interview_analysis, self.other_files_analysis),
                self.analyze_solution(self.client_analysis, self.interview_analysis, self.other_files_analysis),
                self.compile_final_report(self.client_analysis, self.interview_analysis, self.other_files_analysis)
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            manager_agent=self.pm()
        )

    def analyze(self, client_analysis: str, interview_analysis: str, other_files_analysis: str = None, user_input: str = None):
        try:
            inputs = {
                "client_analysis": client_analysis,
                "interview_analysis": interview_analysis,
                "other_files_analysis": other_files_analysis,
                "user_input": user_input
            }
            
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs=inputs)
            result_str = str(result)
            
            return result_str
            
        except Exception as e:
            raise Exception


class StreamToExpander:
    def __init__(self, expander):
        self.expander = expander
        self.buffer = []
        self.colors = ['red', 'green', 'blue', 'orange', 'violet', 'gray']  # Added one more color for the additional agent
        self.color_index = 0

    def write(self, data):
        # Filter out ANSI escape codes using a regular expression
        cleaned_data = re.sub(r'\x1B\[[0-9;]*[mK]', '', data)

        # Check if the data contains 'task' information
        task_match_object = re.search(r'\"task\"\s*:\s*\"(.*?)\"', cleaned_data, re.IGNORECASE)
        task_match_input = re.search(r'task\s*:\s*([^\n]*)', cleaned_data, re.IGNORECASE)
        task_value = None
        if task_match_object:
            task_value = task_match_object.group(1)
        elif task_match_input:
            task_value = task_match_input.group(1).strip()

        if task_value:
            st.toast(":microscope: " + task_value)  # Changed emoji to reflect analysis work

        # Check if the text contains the specified phrase and apply color
        if "Entering new CrewAgentExecutor chain" in cleaned_data:
            self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("Entering new CrewAgentExecutor chain", f":{self.colors[self.color_index]}[Entering new CrewAgentExecutor chain]")

        cleaned_data = cleaned_data.split("> 클라이언트 요구사항:")[0].strip()
        cleaned_data = cleaned_data.split("참고 맥락:")[0].strip()
        # 정규 표현식을 사용하여 특정 패턴을 제거
        pattern = r"[\s]*참고 맥락:.*?위 맥락을 기반으로 수행 문제를 사실적으로 기술하고, 원인 분석 및 해결방안을 구분하여 정리하시오.\n"
        cleaned_data = re.sub(pattern, "", cleaned_data, flags=re.DOTALL)

        current_agent = None

        # Replace agent names with the new ones and apply colors
        if "프로젝트 매니저" in cleaned_data:
            if current_agent != "프로젝트 매니저":
                current_agent = "프로젝트 매니저"
                self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("프로젝트 매니저", f":{self.colors[self.color_index]}[프로젝트 매니저]")
        if "수행 분석 연구원" in cleaned_data:
            if current_agent != "수행 분석 연구원":
                current_agent = "수행 분석 연구원"
                self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("수행 분석 연구원", f":{self.colors[self.color_index]}[수행 분석 연구원]")
        if "성과 분석 연구원" in cleaned_data:
            if current_agent != "성과 분석 연구원":
                current_agent = "성과 분석 연구원"
                self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("성과 분석 연구원", f":{self.colors[self.color_index]}[성과 분석 연구원]")
        if "환경 분석 연구원" in cleaned_data:
            if current_agent != "환경 분석 연구원":
                current_agent = "환경 분석 연구원"
                self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("환경 분석 연구원", f":{self.colors[self.color_index]}[환경 분석 연구원]")
        if "원인 및 해결방안 연구원" in cleaned_data:
            if current_agent != "원인 및 해결방안 연구원":
                current_agent = "원인 및 해결방안 연구원"
                self.color_index = (self.color_index + 1) % len(self.colors)
            cleaned_data = cleaned_data.replace("원인 및 해결방안 연구원", f":{self.colors[self.color_index]}[원인 및 해결방안 연구원]")
        if "Finished chain." in cleaned_data:
            cleaned_data = cleaned_data.replace("Finished chain.", f":{self.colors[self.color_index]}[Finished chain.]")

        self.buffer.append(cleaned_data)
        if "\n" in data:
            self.expander.markdown(''.join(self.buffer), unsafe_allow_html=True)
            self.buffer = []

# #--------------------------------#
# #         EXA Answer Tool        #
# #--------------------------------#
# class EXAAnswerToolSchema(BaseModel):
#     query: str = Field(..., description="The question you want to ask Exa.")

# class EXAAnswerTool(BaseTool):
#     name: str = "Ask Exa a question"
#     description: str = "A tool that asks Exa a question and returns the answer."
#     args_schema: Type[BaseModel] = EXAAnswerToolSchema
#     answer_url: str = "https://api.exa.ai/answer"

#     def _run(self, query: str):
#         headers = {
#             "accept": "application/json",
#             "content-type": "application/json",
#             "x-api-key": st.secrets["EXA_API_KEY"]
#         }
        
#         try:
#             response = requests.post(
#                 self.answer_url,
#                 json={"query": query, "text": True},
#                 headers=headers,
#             )
#             response.raise_for_status() 
#         except requests.exceptions.HTTPError as http_err:
#             print(f"HTTP error occurred: {http_err}")  # Log the HTTP error
#             print(f"Response content: {response.content}")  # Log the response content for more details
#             raise
#         except Exception as err:
#             print(f"Other error occurred: {err}")  # Log any other errors
#             raise

#         response_data = response.json()
#         answer = response_data["answer"]
#         citations = response_data.get("citations", [])
#         output = f"Answer: {answer}\n\n"
#         if citations:
#             output += "Citations:\n"
#             for citation in citations:
#                 output += f"- {citation['title']} ({citation['url']})\n"

#         return output

# #--------------------------------#
# #         LLM & Research Agent   #
# #--------------------------------#
# def create_researcher(selection):
#     """Create a research agent with the specified LLM configuration.
    
#     Args:
#         selection (dict): Contains provider and model information
#             - provider (str): The LLM provider ("OpenAI", "GROQ", or "Ollama")
#             - model (str): The model identifier or name
    
#     Returns:
#         Agent: A configured CrewAI agent ready for research tasks
    
#     Note:
#         Ollama models have limited function-calling capabilities. When using Ollama,
#         the agent will rely more on its base knowledge and may not effectively use
#         external tools like web search.
#     """
#     # provider = selection["provider"]
#     # model = selection["model"]
    
#     # if provider == "GROQ":
#     #     llm = LLM(
#     #         api_key=st.secrets["GROQ_API_KEY"],
#     #         model=f"groq/{model}"
#     #     )
#     # elif provider == "Ollama":
#     #     llm = LLM(
#     #         base_url="http://localhost:11434",
#     #         model=f"ollama/{model}",
#     #     )
#     # else:
#     #     # Map friendly names to concrete model names for OpenAI
#     #     if model == "GPT-3.5":
#     #         model = "gpt-3.5-turbo"
#     #     elif model == "GPT-4":
#     #         model = "gpt-4"
#     #     elif model == "o1":
#     #         model = "o1"
#     #     elif model == "o1-mini":
#     #         model = "o1-mini"
#     #     elif model == "o1-preview":
#     #         model = "o1-preview"
#     #     # If model is custom but empty, fallback
#     #     if not model:
#     #         model = "o1"
#     llm = LLM(
#         api_key=st.secrets["OPENAI_API_KEY"],
#         model= "gpt-4o-mini"
#         # model=f"openai/{model}"
#     )

# #--------------------------------#
# #         Research Task          #
# #--------------------------------#
# def create_research_task(researcher, task_description):
#     """Create a research task for the agent to execute.
    
#     Args:
#         researcher (Agent): The research agent that will perform the task
#         task_description (str): The research query or topic to investigate
    
#     Returns:
#         Task: A configured CrewAI task with expected output format
#     """
#     return Task(
#         description=task_description,
#         expected_output="""A comprehensive research report for the year 2025. 
#         The report must be detailed yet concise, focusing on the most significant and impactful findings.
        
#         Format the output in clean markdown (without code block markers or backticks) using the following structure:

#         # Executive Summary
#         - Brief overview of the research topic (2-3 sentences)
#         - Key highlights and main conclusions
#         - Significance of the findings

#         # Key Findings
#         - Major discoveries and developments
#         - Market trends and industry impacts
#         - Statistical data and metrics (when available)
#         - Technological advancements
#         - Challenges and opportunities

#         # Analysis
#         - Detailed examination of each key finding
#         - Comparative analysis with previous developments
#         - Industry expert opinions and insights
#         - Market implications and business impact

#         # Future Implications
#         - Short-term impacts (next 6-12 months)
#         - Long-term projections
#         - Potential disruptions and innovations
#         - Emerging trends to watch

#         # Recommendations
#         - Strategic suggestions for stakeholders
#         - Action items and next steps
#         - Risk mitigation strategies
#         - Investment or focus areas

#         # Citations
#         - List all sources with titles and URLs
#         - Include publication dates when available
#         - Prioritize recent and authoritative sources
#         - Format as: "[Title] (URL) - [Publication Date if available]"

#         Note: Ensure all information is current and relevant to 2025. Include specific dates, 
#         numbers, and metrics whenever possible to support findings. All claims should be properly 
#         cited using the sources discovered during research.
#         """,
#         agent=researcher,
#         output_file="output/research_report.md"
#     )

# #--------------------------------#
# #         Research Crew          #
# #--------------------------------#
# def run_research(researcher, task):
#     """Execute the research task using the configured agent.
    
#     Args:
#         researcher (Agent): The research agent to perform the task
#         task (Task): The research task to execute
    
#     Returns:
#         str: The research results in markdown format
#     """
#     crew = Crew(
#         agents=[researcher],
#         tasks=[task],
#         verbose=True,
#         process=Process.sequential
#     )
    
#     return crew.kickoff()
