import streamlit as st


pages = {
    "수행 과제 분석 Agent": [
        st.Page("pages/01_요구분석.py", title="요구분석"), 
        st.Page("pages/02_과제분석.py", title="과제분석"),
        # st.Page("pages/히스토리.py", title="히스토리"),  
    ],
}

pg = st.navigation(pages)
pg.run()
