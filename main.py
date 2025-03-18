import streamlit as st


pages = {
    "🕵️‍♂️ ISD-Agent": [
        st.Page("pages/00_메인페이지.py", title="🔑 시스템 로그인"),  
        st.Page("pages/01_요약하기.py", title="📝 에이전트 요약"), 
        st.Page("pages/02_분석하기.py", title="📊 에이전트 분석"),
        st.Page("pages/03_정리하기.py", title="📑 보고서 정리"),
    ],
}

pg = st.navigation(pages)
pg.run()
