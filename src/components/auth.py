"""Shared entry-code authentication for the Streamlit application."""

import hashlib
import hmac
import os
import uuid

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def get_entry_code():
    code = os.environ.get("ENTRY_CODE")
    if code is None:
        try:
            code = st.secrets.get("ENTRY_CODE")
        except StreamlitSecretNotFoundError:
            return None
    return code if isinstance(code, str) and code.strip() else None


def is_authenticated():
    code = get_entry_code()
    if not code:
        return False
    # Changing the configured code also invalidates existing sessions.
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    return hmac.compare_digest(
        st.session_state.get("_entry_code_digest", ""), digest
    )


def logout():
    # Clear uploads and analysis results along with authentication.
    st.session_state.clear()


def render_login():
    st.title("🔑 ISD-Agent 입장")
    st.write("안내받은 입장코드를 입력해주세요.")
    code = get_entry_code()
    if not code:
        st.error("입장코드가 설정되지 않았습니다. 관리자에게 문의해주세요.")
        return

    with st.form("entry_code_form", clear_on_submit=True):
        entered_code = st.text_input("입장코드", type="password")
        submitted = st.form_submit_button("입장하기", type="primary")

    if submitted:
        if not entered_code:
            st.error("입장코드를 입력해주세요.")
        elif hmac.compare_digest(entered_code.encode("utf-8"), code.encode("utf-8")):
            st.session_state.clear()
            st.session_state["_entry_code_digest"] = hashlib.sha256(
                code.encode("utf-8")
            ).hexdigest()
            st.session_state["session_id"] = str(uuid.uuid4())
            st.rerun()
        else:
            st.error("입장코드가 올바르지 않습니다. 다시 확인해주세요.")
