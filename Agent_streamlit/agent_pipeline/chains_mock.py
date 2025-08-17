from types import SimpleNamespace
from typing import List
import random

class _PlanMock:
    def invoke(self, args):
        steps = [
            "Extract key facts from context",
            "Assess potential causes (trauma, toxicity, disease)",
            "Cross-reference with domain knowledge",
            "Synthesize preliminary analysis",
            "Prepare candidate conclusions"
        ]
        random.shuffle(steps)
        return SimpleNamespace(steps=steps)

class _SelectMock:
    def invoke(self, args):
        return "Extract key facts\nAssess potential causes\nSynthesize"

class _AdaptMock:
    def invoke(self, args):
        steps = [
            "Summarize scene/autopsy/tox findings",
            "Evaluate poisoning likelihood",
            "Evaluate trauma/disease likelihood",
            "Draft analysis and uncertainties"
        ]
        return SimpleNamespace(steps=steps)

class _AbstractMock:
    def invoke(self, args):
        return "Concise abstract of provided case context."

class _TidyMock:
    def invoke(self, text):
        return text if isinstance(text, str) else str(text)

class _RouterMock:
    def invoke(self, args):
        # Randomly decide to web-search or not
        binary = random.choice(["yes", "no"])
        query = "sedative-hypnotics overdose signs in autopsy"
        return SimpleNamespace(binary_score=binary, search_query=query)

class _AgentExecMock:
    def invoke(self, args):
        return {"messages": [SimpleNamespace(content="(mocked web search results)")]}    

class _ForensicBookMock:
    def invoke(self, plan_item):
        return "Forensic pathology reference entry for: " + str(plan_item)

class _ExecuteMock:
    def invoke(self, args):
        return SimpleNamespace(execute_result=[
            "Observed: pulmonary edema consistent with sedative overdose.",
            "Observed: coronary atherosclerosis mild; less likely primary cause."
        ])

class _ReflexionMock:
    def invoke(self, args):
        return SimpleNamespace(search_queries=[
            "Interaction between antihypertensives and sedatives",
            "Toxic levels thresholds for common hypnotics"
        ])

class _RetrieverMock:
    class Doc:
        def __init__(self, page_content: str):
            self.page_content = page_content
    def invoke(self, query):
        return [self.Doc(f"参考案例：{query} —— 示例分析片段。")]

class _MedicineMock:
    def invoke(self, query):
        return f"(medical knowledge about: {query})"

class _AnalysisMock:
    def invoke(self, args):
        note = "Preliminary analysis: tox more likely than trauma/disease; await confirmatory tox."
        return SimpleNamespace(analytical_note=note)

class _ReanalysisMock:
    def invoke(self, note):
        return SimpleNamespace(Revised=note + " Revised with structured formatting.")

class _HumanMock:
    def invoke(self, args):
        ctx = args.get("context","")
        fb  = args.get("human","")
        return SimpleNamespace(Revised=ctx + "\n(Human incorporated changes: " + fb + ")")

def _conclusion(note: str) -> List[str]:
    return ["Acute sedative-hypnotic intoxication", "Cardiac event (less likely)"]

class _ConclusionChainMock:
    def invoke(self, args):
        return SimpleNamespace(analytical_con="Final: Acute sedative-hypnotic intoxication (pending confirmatory tox).")

# Export names to mirror real modules
plan_chain = _PlanMock()
plan_chain_2 = _PlanMock()
select_chain = _SelectMock()
adapt_chain = _AdaptMock()

abstract_chain = _AbstractMock()
tidy_chain = _TidyMock()

router_chain = _RouterMock()
agent_executor_graph = _AgentExecMock()

forensic_chain = _ForensicBookMock()
execute_chain = _ExecuteMock()

reflexion_chain = _ReflexionMock()
retriever_reference = _RetrieverMock()
medicine_model = _MedicineMock()

analysis_chain = _AnalysisMock()
reanalysis_chain = _ReanalysisMock()
human_chain = _HumanMock()
conclusion = _conclusion
conclusion_chain = _ConclusionChainMock()
