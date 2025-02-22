from typing import Type
from textwrap import dedent
from crewai import Agent, Task, Crew, Process, LLM
# from crewai_tools import BaseTool
from exa_py import Exa

import re
import requests
import streamlit as st
import os

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class GapAnalysisCrew:
    ###
    ## LLM Settings
    ###
    def __init__(self, client_analysis, interview_analysis):
        self.general_llm = LLM(
                model="openai/gpt-4o-mini", # call model by provider/model_name
                temperature=0.7,
                top_p=0.9,
                request_timeout=120
            )
        self.manager_llm = LLM(
                model="openai/o1-mini", # call model by provider/model_name
                temperature=0.8,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stop=["END"],
                seed=42
            )
        self.client_analysis = client_analysis
        self.interview_analysis = interview_analysis

    ###
    ## Agents Settings
    ###
    def pm(self) -> Agent:
        return Agent(
            role="프로젝트 매니저",
            goal="차이 분석 프로세스를 감독하고 고품질 결과물 보장",
            backstory="""당신은 요구사항 분석과 차이 식별에 전문성을 가진 경험 많은 프로젝트 매니저입니다.
            연구 활동을 지휘하고 발견사항을 실행 가능한 통찰력으로 종합하는 데 탁월합니다.""",
            verbose=True,
            # allow_delegation=True,
            llm=self.manager_llm
        )

    def performance_researcher(self) -> Agent:
        return Agent(
            role="수행 분석 연구원",
            goal="수행 관련 차이 분석",
            backstory="""당신은 프로젝트 수행과 관련된 차이를 분석하는 전문가입니다.
            프로젝트 진행 과정, 방법론, 실행 상의 차이점을 식별하고 분석합니다.""",
            verbose=True,
            llm=self.general_llm
        )

    def achievement_researcher(self) -> Agent:
        return Agent(
            role="성과 분석 연구원",
            goal="성과 관련 차이 분석",
            backstory="""당신은 성과 지표와 달성도를 분석하는 전문가입니다.
            목표 대비 실제 성과의 차이를 정량적, 정성적으로 분석합니다.""",
            verbose=True,
            llm=self.general_llm
        )

    def environment_researcher(self) -> Agent:
        return Agent(
            role="환경 분석 연구원",
            goal="환경 관련 차이 분석",
            backstory="""당신은 프로젝트에 영향을 미치는 환경적 요인을 분석하는 전문가입니다.
            내/외부 환경 요인들이 미치는 영향과 차이점을 분석합니다.""",
            verbose=True,
            llm=self.general_llm
        )

    def solution_researcher(self) -> Agent:
        return Agent(
            role="원인 및 해결방안 연구원",
            goal="원인 분석 및 해결방안 도출",
            backstory="""당신은 문제의 근본 원인을 파악하고 실현 가능한 해결책을 제시하는 전문가입니다.
            차이가 발생한 원인을 분석하고 실질적인 해결방안을 제시합니다.""",
            verbose=True,
            llm=self.general_llm
        )

    ###
    ## Tasks Settings
    ###
    # def identify_task(self, agent, origin, cities, interests, range):
    #     return Task(description=dedent(f"""
    #         Analyze and select the best city for the trip based
    #         on specific criteria such as weather patterns, seasonal
    #         events, and travel costs. This task involves comparing
    #         multiple cities, considering factors like current weather
    #         conditions, upcoming cultural or seasonal events, and
    #         overall travel expenses.

    #         Your final answer must be a detailed
    #         report on the chosen city, and everything you found out
    #         about it, including the actual flight costs, weather
    #         forecast and attractions.
    #         {self.__tip_section()}

    #         Traveling from: {origin}
    #         City Options: {cities}
    #         Trip Date: {range}
    #         Traveler Interests: {interests}
    #       """),
    #         expected_output="A detailed report on the chosen city with flight costs, weather forecast, and attractions.",
    #         agent=agent)

    def analyze_performance(self, client_analysis, interview_analysis) -> Task:
        return Task(description=dedent(f"""
            "클라이언트 요구사항"과 "인터뷰 분석 결과"를 비교하여 수행 관련 차이를 분석하시오.
            - 프로젝트 진행 방식의 차이
            - 실행 과정상의 차이
            - 방법론적 차이

            > 클라이언트 요구사항: {client_analysis}
            > 인터뷰 분석 결과: {interview_analysis}
        """),
            agent=self.performance_researcher(),
            expected_output="수행 관련 차이점 분석 보고서"
        )

    def analyze_achievement(self, client_analysis, interview_analysis) -> Task:
        return Task(description=dedent(f"""
            "클라이언트 요구사항"과 "인터뷰 분석 결과"를 비교하여 성과 관련 차이를 분석하시오.
            - 목표 대비 실제 성과
            - 정량적/정성적 차이
            - KPI 달성도 차이

            > 클라이언트 요구사항: {client_analysis}
            > 인터뷰 분석 결과: {interview_analysis}
        """),
            agent=self.achievement_researcher(),
            expected_output="성과 관련 차이점 분석 보고서"
        )

    def analyze_environment(self, client_analysis, interview_analysis) -> Task:
        return Task(description=dedent(f"""
            "클라이언트 요구사항"과 "인터뷰 분석 결과"를 비교하여 환경 관련 차이를 분석하시오.
            - 내부 환경 요인 차이
            - 외부 환경 요인 차이
            - 환경적 제약사항 차이

            > 클라이언트 요구사항: {client_analysis}
            > 인터뷰 분석 결과: {interview_analysis}
        """),
            agent=self.environment_researcher(),
            expected_output="환경 관련 차이점 분석 보고서"
        )

    def analyze_solution(self, client_analysis, interview_analysis) -> Task:
        return Task(description=dedent(f"""
            앞선 분석 결과들을 검토하여 원인과 해결방안을 도출하시오.
            - 차이 발생의 근본 원인
            - 실현 가능한 해결방안
            - 우선순위 및 실행 계획

            > 클라이언트 요구사항: {client_analysis}
            > 인터뷰 분석 결과: {interview_analysis}
        """),
            agent=self.solution_researcher(),
            expected_output="원인 및 해결방안 보고서"
        )

    # def compile_final_report(self, client_analysis, interview_analysis) -> Task:
    #     return Task(description=dedent(f"""
    #         모든 분석 결과를 종합하여 최종 보고서를 작성하시오.
    #         - 각 영역별 주요 차이점
    #         - 핵심 원인 분석
    #         - 권장 해결방안
    #         - 실행 계획

    #         > 클라이언트 요구사항: {client_analysis}
    #         > 인터뷰 분석 결과: {interview_analysis}
    #     """),
    #         agent=self.pm(),
    #         expected_output="최종 차이 분석 보고서"
    #     )

    def compile_final_report(self, client_analysis, interview_analysis) -> Task:
        return Task(description=dedent(f"""
            클라이언트 요구사항과 인터뷰 분석 결과를 종합적 맥락으로 고려하여 각 수행 종류별 분석 보고서를 작성하시오.

            참고 맥락:
            > 클라이언트 맥락: {client_analysis}
            > 인터뷰 맥락: {interview_analysis}

            위 맥락을 기반으로 각 수행 종류별로 다음 구조에 따라 분석하시오:

            1. 수행의 종류(1): {"수행 문제 상황 (1)에 대한 한 문장 설명"}
                * 1.1. 원인 분석
                * 1.2. 교육적 해결안
                * 1.3. 교육외적 해결안 (있을 경우만 서술 / 없을 경우 제외)

            2. 수행의 종류(2): {"수행 문제 상황 (2)에 대한 한 문장 설명"}
                * 2.1. 원인 분석
                * 2.2. 교육적 해결안
                * 2.3. 교육외적 해결안  (있을 경우만 서술 / 없을 경우 제외)            
            ...

            (수행 종류는 우선 순위와 중요도를 기준으로 최대 3개까지만 서술)
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
                self.analyze_performance(self.client_analysis, self.interview_analysis),
                self.analyze_achievement(self.client_analysis, self.interview_analysis),
                self.analyze_environment(self.client_analysis, self.interview_analysis),
                self.analyze_solution(self.client_analysis, self.interview_analysis),
                self.compile_final_report(self.client_analysis, self.interview_analysis)
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            manager_agent=self.pm()
        )

    def analyze(self, client_analysis: str, interview_analysis: str): # , message_queue):
        try:
            inputs = {
                "client_analysis": client_analysis,
                "interview_analysis": interview_analysis
            }
            
            crew_instance = self.crew()
            
            # # 각 에이전트의 작업 진행상황을 메시지로 전달
            # for agent in crew_instance.agents:
            #     await message_queue.put({
            #         "agent_name": agent.role,
            #         "message": f"{agent.role}이(가) 분석을 시작합니다."
            #     })
            
            result = crew_instance.kickoff(inputs=inputs)
            result_str = str(result)
            
            # # 최종 결과 전달
            # await message_queue.put({
            #     "agent_name": "PM",
            #     "message": "분석이 완료되었습니다.",
            #     "report": result_str
            # })
            
            return result_str
            
        except Exception as e:
            # await message_queue.put({
            #     "agent_name": "System",
            #     "message": f"분석 중 오류가 발생했습니다: {str(e)}"
            # })
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
        # 정규 표현식을 사용하여 특정 패턴을 제거
        pattern = r"[\s]*참고 맥락:.*?위 맥락을 기반으로 각 수행 종류별로 다음 구조에 따라 분석하시오:\n"
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
