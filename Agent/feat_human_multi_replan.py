import os
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]="lsv2_xxxxxxxxx"
os.environ["LANGCHAIN_PROJECT"]="xxxxxxxxx"
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxxx"
os.environ["OPENAI_BASE_URL"] = "https:xxxxxxxxx"
os.environ["DEEPSEEK_API_KEY"] = "sk-xxxxxxxxx"
os.environ["TAVILY_API_KEY"] = "tvly-xxxxxxxxx"

from typing import List, Annotated, TypedDict,Optional
from plan import plan_chain,select_chain,adapt_chain,plan_chain_2
from replan import update_plan_chain
from abstract import  abstract_chain,tidy_chain
from  analysis_note import  analysis_chain,reanalysis_chain,conclusion,conclusion_chain,human_chain
from langchain_core.messages import HumanMessage
from router import router_chain
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from utils import forensic_chain,reflexion_chain,retriever_reference,agent_executor_graph,medicine_model
from execute import execute_chain
import operator
import argparse
import itertools
from collections import Counter
from langchain_community.document_loaders import Docx2txtLoader
import re
import copy





def get_args_parser():
    parser = argparse.ArgumentParser('foundation-forensic-agent', add_help=False)
    parser.add_argument('--data_path', default='', type=str,
                        help='Please specify path to the test data.')

    parser.add_argument('--out_path', default='./tmp.txt', type=str,
                        help='Please specify path to the output data.')

    return parser



class Forensic(TypedDict):
    input: str
    content: str
    plan: List[str]
    old_plan:str
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
    human: str
    ana_note_human: Optional[str]

###########################################################################

def plan_step(state: Forensic):
    pp_all =[]
    for index in range(4):
        if index==0:
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

    return {"old_plan": "\n".join(combined_list),"plan": plan_new.steps,"abstract": context_abstract}

###########################################################################

def grade_step(state: Forensic):

    res = router_chain.invoke({"question": state["plan"][0], "context": state["content"]})

    return {"score": res.binary_score,"web_query": res.search_query,"now_plan": state["plan"][0]}

###########################################################################

def search_step(state: Forensic):


    search_result = agent_executor_graph.invoke({"messages": [HumanMessage(content=state["web_query"])]})


    return {"web_res": search_result["messages"][-1].content}

###########################################################################


def execute_step(state: Forensic):

    ##############################
    forensic_book = forensic_chain.invoke(state["plan"][0])
    ##By default, all processes should employ forensic pathology reference texts to enrich the infusion of specialized domain knowledge
    ##############################


    if state["score"].lower() == "yes":
        all_reference = forensic_book
    elif state["score"].lower() == "no":
        all_reference = tidy_chain.invoke(state["web_res"]+"\n\n ** Forensic domain knowledge book **: \n\n"+ forensic_book)
    else:
        print("wrong!!!!!!!")

    if len(state["obs_result"]) == 0:
        obs_inf = "None"
    else:
        obs_inf_ = "\n-".join(text for text in state["obs_result"])
        obs_inf = tidy_chain.invoke(obs_inf_)
    ###

    current_step = state["plan"][0]

    exe_ = execute_chain.invoke({"plan":current_step,"context":state["content"],"content":all_reference,"observed":obs_inf})

    state["plan"].pop(0)

    # Prepare inputs for the update chain
    observations_new = "\n- " + "\n- ".join(exe_.execute_result) if exe_.execute_result else "None"
    observations_old = "\n- " + "\n- ".join(state["obs_result"]) if state["obs_result"] else "None"
    observations_joined = observations_old +observations_new
    remaining_plan_str = "\n".join(state["plan"]) if state["plan"] else ""

    # Prepare inputs for update
    original_remaining = [s for s in state["plan"] if isinstance(s, str) and s.strip()]
    n_steps = len(original_remaining)

    # If there is nothing left, you can skip the update call entirely.
    if n_steps == 0:
        updated_plan = []

    else:
        upd = update_plan_chain.invoke({
            "objective": state["input"],
            "content": state["content"],
            "last_step": current_step,
            "observations": observations_joined,
            "remaining_plan": remaining_plan_str,
            "n_steps": n_steps,
        })

        # Defensive post-processing to GUARANTEE the count matches n_steps

        model_steps = [s.strip() for s in getattr(upd, "steps", []) if isinstance(s, str) and s.strip()]

        if len(model_steps) > n_steps:
            model_steps = model_steps[:n_steps]  # truncate
        elif len(model_steps) < n_steps:
            model_steps += original_remaining[len(model_steps):n_steps]

        updated_plan = model_steps


    if len(updated_plan)==0:
        replan="false"
    else:
        replan = "true"

    return {"plan": updated_plan,"obs_result": exe_.execute_result,"replan":replan,"F_book":forensic_book,"obs_inf":[obs_inf]}

###########################################################################

def reflexion_step(state: Forensic):

    reflexion_result = reflexion_chain.invoke({"context":state["content"],"discovered": "\n\n-".join(text for text in state["obs_result"])})

    results = []
    for index in range(len(reflexion_result.search_queries)):
        #forensic_book = forensic_chain.invoke(reflexion_result.search_queries[index])
        med = medicine_model.invoke(reflexion_result.search_queries[index])
        #forensic_knowledge = tidy_chain.invoke(forensic_book + "\n\n" + med)
        forensic_knowledge = tidy_chain.invoke(med)
        exe_ = execute_chain.invoke(
            {"plan": reflexion_result.search_queries[index], "context": state["content"], "content": forensic_knowledge, "observed": "None"})
        results.extend(exe_.execute_result)


    return {"reflexion_result":results,"re_search":reflexion_result.search_queries}

###########################################################################


### H-RAG


def top_two_frequent_elements(lst):
    if len(lst) < 2:
        return lst
    counter = Counter(lst)
    return [item for item, count in counter.most_common(2)]


def find_fewshot_step(state: Forensic):
    l1 = []
    l2 = []
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

############################################

def analysis_step(state: Forensic):

    obs_all = "\n-".join(text for text in state["obs_result"])
    obs_all_tidy = tidy_chain.invoke(obs_all)
    obs_all_tidy2 = tidy_chain.invoke("\n\n-".join(text for text in state["obs_inf"] if text != "None"))
    observed = obs_all_tidy2 + "\n\n-" + obs_all_tidy

    supplements = tidy_chain.invoke("\n-".join(text for text in state["reflexion_result"]))

    ana_note = analysis_chain.invoke({"fewshot": state["examples"], "context": state["content"], "obs_result": observed,"supplements": supplements})

    ana_note_new = reanalysis_chain.invoke(ana_note.analytical_note)

    return {"ana_note": ana_note.analytical_note, "ana_note_new": ana_note_new.Revised}



def analysis_human_step(state: Forensic):

    if state.get('ana_note_human') == None:

        ana_note = human_chain.invoke(
            {"context": state["ana_note_new"], "human": state["human"], "fewshot": state["examples"]})

        ana_note = ana_note.Revised

    else:

        ana_note = human_chain.invoke(
            {"context": state["ana_note_human"], "human": state["human"], "fewshot": state["examples"]})

        ana_note = ana_note.Revised


    return {"ana_note_human":ana_note}


def conclusion_step(state: Forensic):

    if state.get('ana_note_human') == None :

        list_c = conclusion(state["ana_note_new"])

        candidate = "\n\n".join(text for text in list(set(list_c)))

        ana_con = conclusion_chain.invoke({"context":state["ana_note_new"],"candicate": "\n".join(text for text in list_c)})

    else:
        list_c = conclusion(state["ana_note_human"])

        candidate = "\n\n".join(text for text in list(set(list_c)))

        ana_con = conclusion_chain.invoke(
            {"context": state["ana_note_human"], "candicate": "\n".join(text for text in list_c)})


    return {"ana_con": ana_con.analytical_con,"candidate":candidate}

def human_feedback(state: Forensic):
    """ No-op node that should be interrupted on """
    pass


def should_continue(state: Forensic):
    """ Return the next node to execute """

    # Check if human feedback
    human_analyst_feedback = state.get('human', None)
    if human_analyst_feedback:
        return "human_analysis"

    # Otherwise conclusion
    return "conclusion"


def should_execute(state: Forensic):

    if state["score"].lower() == "yes":
        return "execute"
    else:
        return "search"


def should_end(state: Forensic):
    if state["replan"].lower() == "false":
        return "reflexion"
    elif state["replan"].lower() == "true":
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

    workflow.add_conditional_edges("route",
                                   should_execute,
                                   {
                                       "execute": "execute",
                                       "search": "search"
                                   }
                                   )
    workflow.add_edge("search", "execute")

    workflow.add_conditional_edges("execute",
                                   should_end,
                                   {"route": "route",
                                    "reflexion": "reflexion"})

    workflow.add_edge("reflexion", "example")

    workflow.add_edge("example", "analysis")

    workflow.add_edge("analysis", "human_feedback")

    workflow.add_conditional_edges("human_feedback", should_continue, ["human_analysis", "conclusion"])

    workflow.add_edge("human_analysis", "human_feedback")


    workflow.add_edge("conclusion", END)
    memory = MemorySaver()

    app = workflow.compile(interrupt_before=["human_feedback"], checkpointer=memory)
    return app


def main(args):

    if args.data_path.endswith(".docx"):
        loader = Docx2txtLoader(args.data_path)
        data = loader.load()
        text = data[0].page_content
    elif args.data_path.endswith(".txt"):
        with open(args.data_path, "r", encoding="utf-8") as file:
            text = file.read()
    else:
        raise ValueError(f"文件名 '{args.data_path}' 请检查文件名！")
    text_shift = re.sub(r'\t|\n', '', text)

    if "XXX" in text_shift or "XX" in text_shift:

        text_shift = text_shift.replace("XXX", "小明").replace("XX", "小明")

    context = text_shift


    inputs = {"input": " You're a seasoned forensic expert. Your task is to review the provided information and explain the cause of death. Ensure your analysis is detailed and considers all available data.", "content": context}
    app = make_graph()
    thread = {"configurable": {"thread_id": "1","recursion_limit":100}}
    for output in app.stream(inputs, thread):
        for key, value in output.items():

            if key == "planner":
                old_plan=value["old_plan"]
                new_plan = "\n".join(text for text in value["plan"])
                print("\nplan:\n\n",new_plan, flush=True)
                abstr = value["abstract"]
                txt_all = "abstract: "+ abstr + "\n\n" + "old_plan：\n" + old_plan + "\n\n" + "new_plan：\n" + new_plan
                with open(args.out_path, 'w') as f:
                    f.write(txt_all)
            elif key == "route":
                print("\nNow:\n\n",value["now_plan"], flush=True)

            elif key =="search":
                tt = "\nSearch_contents:\n\n" + value["web_res"]
                print(tt, flush=True)
                with open(args.out_path, 'a') as f:
                    f.write(tt)


            elif key == "execute":
                tt = "\nResults:\n\n" + "\n".join(text for text in value["obs_result"])
                reflex_ = "\nSummary:\n\n" + "\n".join(text for text in value["obs_inf"])
                print(tt, flush=True)
                with open(args.out_path, 'a') as f:
                    f.write(tt)
                    f.write(reflex_)
            elif key == "reflexion":
                tt = "\nsearch_result:\n\n" + "\n".join(text for text in value["reflexion_result"])
                search = "\nsearch:\n\n" + "\n".join(text for text in value["re_search"])
                print(search, flush=True)
                print(tt, flush=True)
                with open(args.out_path, 'a') as f:
                    f.write(search)
                    f.write(tt)

            elif key == "example":
                few_shot = "\nfew_shot_examples:\n\n" + value["examples"]
                #print(few_shot, flush=True)
                with open(args.out_path, 'a') as f:
                    f.write(few_shot)

            elif key == "analysis":

                analysis = "\n original_analysis:\n\n" + value["ana_note"] + "\n\n update_analysis:\n\n" + value["ana_note_new"]

                print(analysis, flush=True)
                with open(args.out_path, 'a') as f:
                    f.write(analysis)


    while True:
        user_approval = input("你想要修改的地方？如果没有就填no/否: ")
        if user_approval.lower() == "no" or user_approval =="否":
            app.update_state(thread, {"human" : None}, as_node="human_feedback")
            for output in app.stream(None, thread):
                for key, value in output.items():
                    if key == "conclusion":

                        conclusion = "\n\n condidate_conclusion:\n\n" + value["candidate"] + "\n\n final_conclusion:\n\n" + \
                                     value["ana_con"]

                        print(conclusion, flush=True)
                        with open(args.out_path, 'a') as f:
                            f.write(conclusion)
            break

        else:
            app.update_state(thread, {"human" : user_approval}, as_node="human_feedback")
            for output in app.stream(None, thread):
                for key, value in output.items():
                    if key == "conclusion":

                        conclusion = "\n condidate_conclusion:\n\n" + value["candidate"] + "\n\n final_conclusion:\n\n" + \
                                     value["ana_con"]

                        print(conclusion, flush=True)
                        with open(args.out_path, 'a') as f:
                            f.write(conclusion)
                    elif key == "human_analysis":

                        analysis = "\n human_change_analysis:\n\n" + value["ana_note_human"]

                        print(analysis, flush=True)

                        with open(args.out_path, 'a') as f:
                            f.write(analysis)



if __name__ == '__main__':
    parser = argparse.ArgumentParser('foundation-model', parents=[get_args_parser()])
    args = parser.parse_args()
    main(args)
