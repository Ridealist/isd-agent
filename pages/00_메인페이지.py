import streamlit as st
import time
import uuid

# 로그인 기능 비활성화 (주석 처리)
# if "logged_in" not in st.session_state:
#     st.session_state["logged_in"] = False

# if "session_id" not in st.session_state:
#     st.session_state["session_id"] = None

# 로그인 없이 바로 접근 가능하도록 설정
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = True  # 항상 로그인된 상태로 설정

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())  # 랜덤 UUID 생성


# Logo
st.logo(
    "https://media.licdn.com/dms/image/v2/C511BAQFHW_naY__2Fg/company-background_10000/company-background_10000/0/1583927014937/iled_lighting_systems_pvt_ltd__cover?e=2147483647&v=beta&t=Y1x2WJMstxhMwG8RDFgTgTQbhYyn6Us6rRGDRtsiaoA",
    link="https://iled.snu.ac.kr/",
    size="large"
)

st.title("🕵️‍♂️ Introducing ISD-Agent")
st.write("ISD 에이전트는 초보 교수설계자들이 ISD를 수행하는데 도움을 주는 LLM 에이전트 기반의 도구입니다.")

# 로그인 기능 비활성화 (주석 처리)
# # st.write("Please log in to continue (username `test`, password `test`).")
# # secrets.toml에서 사용자 정보 가져오기
# users_info = st.secrets["users"]

# username = st.text_input("Username")
# password = st.text_input("Password", type="password")

# if st.button("Log in", type="primary"):
#     if username not in users_info:
#         st.error("Username을 확인해주세요.")
#     else:
#         if password != users_info[username]["password"]:
#             st.error("Password를 확인해주세요.")
#         else:
#             st.session_state.logged_in = True
#             st.session_state["session_id"] = str(users_info[username]["userID"])
#             st.success("로그인 성공!")
#             time.sleep(0.5)
#             st.switch_page("pages/01_요약하기.py")

# 로그인 없이 바로 다음 페이지로 이동 가능
if st.button("시작하기", type="primary"):
    st.switch_page("pages/01_요약하기.py")
