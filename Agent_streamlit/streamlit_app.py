import streamlit as st
import os, io, re
from uuid import uuid4

# Bring environment from secrets (no hard-coded keys)
if "env" in st.secrets:
    os.environ.update(st.secrets["env"])

from langchain_community.document_loaders import Docx2txtLoader
from agent_pipeline.pipeline import (
    make_graph, initial_inputs, continue_without_changes, continue_with_changes
)

st.set_page_config(page_title="Forensic Agent (Streamlit)", layout="wide")
st.title("Forensic Agent Demo")

def read_context_from_upload(uploaded):
    if uploaded is None:
        return ""
    name = uploaded.name.lower()
    if name.endswith(".docx"):
        with open("uploaded.docx", "wb") as f:
            f.write(uploaded.getbuffer())
        loader = Docx2txtLoader("uploaded.docx")
        data = loader.load()
        text = data[0].page_content
    elif name.endswith(".txt"):
        text = uploaded.read().decode("utf-8", errors="ignore")
    else:
        raise ValueError("Please upload a .docx or .txt file.")
    text_shift = re.sub(r"\t|\n", "", text)
    if "XXX" in text_shift or "XX" in text_shift:
        text_shift = text_shift.replace("XXX", "小明").replace("XX", "小明")
    return text_shift

# Session state init
if "app" not in st.session_state:
    st.session_state.app = make_graph()
if "thread" not in st.session_state:
    st.session_state.thread = {"configurable": {"thread_id": str(uuid4()), "recursion_limit": 100}}
if "log" not in st.session_state:
    st.session_state.log = []
if "awaiting_feedback" not in st.session_state:
    st.session_state.awaiting_feedback = False
if "export_text" not in st.session_state:
    st.session_state.export_text = io.StringIO()

uploaded = st.file_uploader("Upload a .docx or .txt case file (or skip and use the demo sample)", type=["docx", "txt"])
demo = st.checkbox("Use demo sample (ignore upload)", value=False)

user_objective = st.text_area(
    "Task instruction",
    "You're a seasoned forensic expert. Your task is to review the provided information and explain the cause of death. "
    "Ensure your analysis is detailed and considers all available data.",
    height=100,
)

#st.caption("Mock chains active: **%s**" % ("Yes" if using_mocks() else "No"))

def render_event_and_collect(key, value):
    if key == "planner":
        new_plan = "\n".join(value["plan"])
        st.subheader("Plan")
        st.code(new_plan)
        st.session_state.export_text.write(f"\nplan:\n\n{new_plan}\n")
        st.session_state.export_text.write(
            f"abstract: {value['abstract']}\n\nold_plan:\n{value['old_plan']}\n\nnew_plan:\n{new_plan}\n"
        )
    elif key == "route":
        st.markdown(f"**Now:** {value['now_plan']}")
    elif key == "search":
        st.expander("Search contents", expanded=False).write(value["web_res"])
        st.session_state.export_text.write("\nSearch_contents:\n\n" + value["web_res"] + "\n")
    elif key == "execute":
        st.expander("Results", expanded=True).write("\n".join(value["obs_result"]))
        st.expander("Summary", expanded=False).write("\n".join(value["obs_inf"]))
        st.session_state.export_text.write("\nResults:\n\n" + "\n".join(value["obs_result"]) + "\n")
        st.session_state.export_text.write("\nSummary:\n\n" + "\n".join(value["obs_inf"]) + "\n")
    elif key == "reflexion":
        st.expander("Reflexion search queries", expanded=False).write("\n".join(value["re_search"]))
        st.expander("Reflexion results", expanded=False).write("\n".join(value["reflexion_result"]))
        st.session_state.export_text.write("\nsearch:\n\n" + "\n".join(value["re_search"]) + "\n")
        st.session_state.export_text.write("\nsearch_result:\n\n" + "\n".join(value["reflexion_result"]) + "\n")
    elif key == "example":
        st.expander("Few-shot examples", expanded=False).write(value["examples"])
        st.session_state.export_text.write("\nfew_shot_examples:\n\n" + value["examples"] + "\n")
    elif key == "analysis":
        st.subheader("Analysis")
        st.code(value["ana_note"])
        st.subheader("Updated analysis")
        st.code(value["ana_note_new"])
        st.session_state.export_text.write(
            "\n original_analysis:\n\n" + value["ana_note"] + "\n\n update_analysis:\n\n" + value["ana_note_new"] + "\n"
        )
    elif key == "human_analysis":
        st.subheader("Human-revised analysis")
        st.code(value["ana_note_human"])
        st.session_state.export_text.write("\n human_change_analysis:\n\n" + value["ana_note_human"] + "\n")
    elif key == "conclusion":
        st.subheader("Conclusions")
        st.code("Candidate conclusions:\n\n" + value["candidate"])
        st.code("Final conclusion:\n\n" + value["ana_con"])
        st.session_state.export_text.write(
            "\n condidate_conclusion:\n\n" + value["candidate"] + "\n\n final_conclusion:\n\n" + value["ana_con"] + "\n"
        )

def stream_once(gen):
    placeholder = st.empty()
    for output in gen:
        for key, value in output.items():
            st.session_state.log.append((key, value))
            with placeholder.container():
                render_event_and_collect(key, value)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Run to human feedback"):
        try:
            if demo:
                context = open("sample_data/case.txt", "r", encoding="utf-8").read()
            else:
                context = read_context_from_upload(uploaded)
                if not context:
                    st.warning("Please upload a .docx or .txt file, or enable demo sample.")
                    st.stop()
            inputs = initial_inputs(context, user_objective)
            gen = st.session_state.app.stream(inputs, st.session_state.thread)
            stream_once(gen)
            st.session_state.awaiting_feedback = True
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    if st.session_state.export_text.getvalue():
        st.download_button(
            "Download current transcript",
            data=st.session_state.export_text.getvalue().encode("utf-8"),
            file_name="report.txt",
            mime="text/plain",
        )

#st.divider()
st.markdown("---")

if st.session_state.awaiting_feedback:
    st.markdown("### Human feedback")
    with st.form("human_feedback_form"):
        fb = st.text_area(
            "Where would you like to make changes? If none, click **Finalize** or enter 'no' / '否'.",
            height=160,
        )
        c1, c2 = st.columns(2)
        apply_btn = c1.form_submit_button("Apply changes")
        finalize_btn = c2.form_submit_button("Finalize (no changes)")

    if finalize_btn or (fb or "").strip().lower() in {"no", "否"}:
        st.info("Finalizing without changes...")
        gen = continue_without_changes(st.session_state.app, st.session_state.thread)
        stream_once(gen)
        st.session_state.awaiting_feedback = False
    elif apply_btn:
        if not fb.strip():
            st.warning("Please enter what to change, or click Finalize.")
        else:
            st.info("Applying your changes...")
            gen = continue_with_changes(st.session_state.app, st.session_state.thread, fb)
            stream_once(gen)
            # Graph may pause again at human_feedback; keep flag True
