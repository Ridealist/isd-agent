import streamlit as st

from src.components.manual import render_manual

# Logo
st.logo(
    "https://media.licdn.com/dms/image/v2/C511BAQFHW_naY__2Fg/company-background_10000/company-background_10000/0/1583927014937/iled_lighting_systems_pvt_ltd__cover?e=2147483647&v=beta&t=Y1x2WJMstxhMwG8RDFgTgTQbhYyn6Us6rRGDRtsiaoA",
    link="https://iled.snu.ac.kr/",
    size="large"
)

st.title("🕵️‍♂️ Introducing ISD-Agent")
st.write("ISD 에이전트는 초보 교수설계자들이 ISD를 수행하는데 도움을 주는 LLM 에이전트 기반의 도구입니다.")

if st.button("시작하기", type="primary"):
    st.switch_page("pages/01_요약하기.py")

render_manual()
