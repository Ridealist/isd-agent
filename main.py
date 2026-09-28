import streamlit as st

from src.components.auth import is_authenticated, logout, render_login

st.set_page_config(
    page_title="ISD-Agent", page_icon="🕵️‍♂️", layout="wide",
    initial_sidebar_state="expanded",
)

# Register protected pages only after authentication, including for direct URLs.
if is_authenticated():
    st.sidebar.button("나가기", on_click=logout)
    st.sidebar.caption("나가면 현재 작업 내용이 초기화됩니다.")
    pages = {
        "🕵️‍♂️ ISD-Agent": [
            st.Page("pages/00_메인페이지.py", title="🏠 메인 페이지"),
            st.Page("pages/01_요약하기.py", title="📝 에이전트 요약"),
            st.Page("pages/02_분석하기.py", title="📊 에이전트 분석"),
            st.Page("pages/03_정리하기.py", title="📑 보고서 정리"),
        ],
    }
else:
    if "_entry_code_digest" in st.session_state:
        logout()
    pages = [st.Page(render_login, title="입장코드", default=True)]

pg = st.navigation(pages)
pg.run()
