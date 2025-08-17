import operator
import re
from typing import List, Annotated, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Try to import user's real modules first; otherwise fallback to mocks.
from langchain_core.messages import HumanMessage
from agent_pipeline.plan import plan_chain, select_chain, adapt_chain, plan_chain_2
from agent_pipeline.abstract import abstract_chain, tidy_chain
from agent_pipeline.analysis_note import analysis_chain, reanalysis_chain, conclusion, conclusion_chain, human_chain
from agent_pipeline.router import router_chain
from agent_pipeline.utils import forensic_chain, reflexion_chain, retriever_reference, agent_executor_graph, medicine_model
from agent_pipeline.execute import execute_chain



class Forensic(TypedDict):
    input: str
    content: str
    plan: List[str]
    old_plan: str
    abstract: str
    score: str
    web_query: str
    web_res: str
    obs_result: Annotated[List[str], operator.add]
    replan: str
    examples: str
    ana_note: str
    ana_note_new: str
    ana_con: str
    F_book: str
    now_plan: str
    candidate: str
    obs_inf: Annotated[List[str], operator.add]
    re_search: List[str]
    reflexion_result: List[str]
    human: Optional[str]
    ana_note_human: Optional[str]

# ---------------- Nodes ----------------
def plan_step(state: Forensic):
    import copy, itertools
    pp_all = []
    for index in range(4):
        if index == 0:
            plan = plan_chain.invoke({"content": state["content"], "objective": state["input"]})
            pp_all.append(copy.deepcopy(plan.steps))
        else:
            plan = plan_chain_2.invoke({"content": state["content"], "objective": state["input"]})
            pp_all.append(copy.deepcopy(plan.steps))
    combined_list = [item for group in itertools.zip_longest(*pp_all) for item in group if item is not None]
    context_abstract = abstract_chain.invoke({"context": state["content"]})
    sel = select_chain.invoke({"task_description": (state["input"] + "\n\n" + "Context of the task: \n\n\n" + context_abstract),
                               "reasoning_modules": "\n".join(combined_list)})
    plan_new = adapt_chain.invoke(
        {"task_description": (state["input"] + "\n\n" + "Context of the task: \n\n\n" + context_abstract), "selected_modules": sel})
    return {"old_plan": "\n".join(combined_list), "plan": plan_new.steps, "abstract": context_abstract}

def grade_step(state: Forensic):
    res = router_chain.invoke({"question": state["plan"][0], "context": state["content"]})
    return {"score": res.binary_score, "web_query": res.search_query, "now_plan": state["plan"][0]}

def search_step(state: Forensic):
    search_result = agent_executor_graph.invoke({"messages": [HumanMessage(content=state["web_query"])]})
    return {"web_res": search_result["messages"][-1].content}

def execute_step(state: Forensic):
    forensic_book = forensic_chain.invoke(state["plan"][0])
    if str(state["score"]).lower() == "yes":
        all_reference = forensic_book
    elif str(state["score"]).lower() == "no":
        all_reference = tidy_chain.invoke(state["web_res"] + "\n\n ** Forensic domain knowledge book **: \n\n" + forensic_book)
    else:
        all_reference = forensic_book
    if len(state.get("obs_result", [])) == 0:
        obs_inf = "None"
    else:
        obs_inf_ = "\n-".join(text for text in state["obs_result"])
        obs_inf = tidy_chain.invoke(obs_inf_)
    exe_ = execute_chain.invoke({"plan": state["plan"][0], "context": state["content"], "content": all_reference, "observed": obs_inf})
    # pop first plan item
    state["plan"].remove(state["plan"][0])
    replan = "false" if len(state["plan"]) == 0 else "true"
    return {"obs_result": exe_.execute_result, "replan": replan, "F_book": forensic_book, "obs_inf": [obs_inf]}

def reflexion_step(state: Forensic):
    reflexion_result_ = reflexion_chain.invoke({"context": state["content"], "discovered": "\n\n-".join(text for text in state["obs_result"])})
    results = []
    for index in range(len(reflexion_result_.search_queries)):
        med = medicine_model.invoke(reflexion_result_.search_queries[index])
        forensic_knowledge = tidy_chain.invoke(med)
        exe_ = execute_chain.invoke(
            {"plan": reflexion_result_.search_queries[index], "context": state["content"], "content": forensic_knowledge, "observed": "None"})
        results.extend(exe_.execute_result)
    return {"reflexion_result": results, "re_search": reflexion_result_.search_queries}

# H-RAG helpers
def top_two_frequent_elements(lst):
    from collections import Counter
    if len(lst) < 2:
        return lst
    counter = Counter(lst)
    return [item for item, count in counter.most_common(2)]

def find_fewshot_step(state: Forensic):
    l1, l2 = [], []
    for i in range(len(state["obs_result"])):
        data = retriever_reference.invoke(state["obs_result"][i])[0]
        data_example = "分析说明：" + re.sub(r'\t|\n', '', data.page_content)
        l1.append(data_example[:-1])
    for j in range(len(state["obs_inf"])):
        if state["obs_inf"][j] != "None":
            data = retriever_reference.invoke(state["obs_inf"][j])[0]
            data_example = "分析说明：" + re.sub(r'\t|\n', '', data.page_content)
            l2.append(data_example[:-1])
    fewshot_s = top_two_frequent_elements(l1)
    fewshot_l = top_two_frequent_elements(l2)
    fewshot = "\n\n".join(list(set(fewshot_s + fewshot_l)))
    return {"examples": fewshot}

def analysis_step(state: Forensic):
    obs_all = "\n-".join(text for text in state["obs_result"])
    obs_all_tidy = tidy_chain.invoke(obs_all)
    obs_all_tidy2 = tidy_chain.invoke("\n\n-".join(text for text in state["obs_inf"] if text != "None"))
    observed = (obs_all_tidy2 + "\n\n-" + obs_all_tidy) if obs_all_tidy2 else obs_all_tidy
    supplements = tidy_chain.invoke("\n-".join(text for text in state["reflexion_result"]))
    ana_note = analysis_chain.invoke({"fewshot": state["examples"], "context": state["content"], "obs_result": observed, "supplements": supplements})
    ana_note_new = reanalysis_chain.invoke(ana_note.analytical_note)
    return {"ana_note": ana_note.analytical_note, "ana_note_new": ana_note_new.Revised}

def analysis_human_step(state: Forensic):
    if state.get('ana_note_human') is None:
        ana_note = human_chain.invoke({"context": state["ana_note_new"], "human": state["human"], "fewshot": state["examples"]})
        ana_note = ana_note.Revised
    else:
        ana_note = human_chain.invoke({"context": state["ana_note_human"], "human": state["human"], "fewshot": state["examples"]})
        ana_note = ana_note.Revised
    return {"ana_note_human": ana_note}

def conclusion_step(state: Forensic):
    if state.get('ana_note_human') is None:
        list_c = conclusion(state["ana_note_new"])
        candidate = "\n\n".join(text for text in list(set(list_c)))
        ana_con = conclusion_chain.invoke({"context": state["ana_note_new"], "candicate": "\n".join(text for text in list_c)})
    else:
        list_c = conclusion(state["ana_note_human"])
        candidate = "\n\n".join(text for text in list(set(list_c)))
        ana_con = conclusion_chain.invoke({"context": state["ana_note_human"], "candicate": "\n".join(text for text in list_c)})
    return {"ana_con": ana_con.analytical_con, "candidate": candidate}

def human_feedback(state: Forensic):
    pass

def should_continue(state: Forensic):
    human_analyst_feedback = state.get('human', None)
    if human_analyst_feedback:
        return "human_analysis"
    return "conclusion"

def should_execute(state: Forensic):
    return "execute" if str(state["score"]).lower() == "yes" else "search"

def should_end(state: Forensic):
    if str(state["replan"]).lower() == "false":
        return "reflexion"
    elif str(state["replan"]).lower() == "true":
        return "route"

def make_graph():
    workflow = StateGraph(Forensic)
    workflow.add_node("planner", plan_step)
    workflow.add_node("route", grade_step)
    workflow.add_node("search", search_step)
    workflow.add_node("execute", execute_step)
    workflow.add_node("reflexion", reflexion_step)
    workflow.add_node("example", find_fewshot_step)
    workflow.add_node("analysis", analysis_step)
    workflow.add_node("human_feedback", human_feedback)
    workflow.add_node("human_analysis", analysis_human_step)
    workflow.add_node("conclusion", conclusion_step)
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "route")
    workflow.add_conditional_edges("route", should_execute, {"execute": "execute", "search": "search"})
    workflow.add_edge("search", "execute")
    workflow.add_conditional_edges("execute", should_end, {"route": "route", "reflexion": "reflexion"})
    workflow.add_edge("reflexion", "example")
    workflow.add_edge("example", "analysis")
    workflow.add_edge("analysis", "human_feedback")
    workflow.add_conditional_edges("human_feedback", should_continue, ["human_analysis", "conclusion"])
    workflow.add_edge("human_analysis", "human_feedback")
    workflow.add_edge("conclusion", END)
    memory = MemorySaver()
    app = workflow.compile(interrupt_before=["human_feedback"], checkpointer=memory)
    return app

# Convenience helpers used by Streamlit UI
def initial_inputs(context: str, objective: str):
    return {"input": objective, "content": context}

def continue_without_changes(app, thread):
    app.update_state(thread, {"human": None}, as_node="human_feedback")
    return app.stream(None, thread)

def continue_with_changes(app, thread, feedback: str):
    app.update_state(thread, {"human": feedback}, as_node="human_feedback")
    return app.stream(None, thread)


