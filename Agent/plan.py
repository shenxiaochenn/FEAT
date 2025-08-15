from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek


planner_prompt = ChatPromptTemplate.from_template(
"""

<Instruction>

You are a forensic science professor tasked with conducting a coroner’s analysis.  
Please develop a **plan of action** that addresses this task within the given **context of the task**.  
The plan must be tightly linked to the analysis of the decedent’s cause of death.  
The name of the decedent must not appear anywhere in the plan.  
Present the plan as bullet points (maximum 4).  
**Do NOT** attempt to execute the plan.

</Instruction>

<Considerations for the Plan>

- **Comprehensive pathological autopsy findings:**  
  Summarize and analyze every pathological observation described in the autopsy report, including chronic and acute conditions. Pay particular attention to pre-existing diseases and key organ-specific pathological changes.  
- **Correlation of clinical diagnoses with autopsy results:**  
  Compare pre-mortem hospital records with post-mortem findings—especially classical pathological alterations—and evaluate other clinically documented conditions that may relate to death, such as shock (traumatic, infectious, hemorrhagic, anaphylactic), cutaneous injuries (e.g., electrical marks), intracranial diseases (cranial trauma, intracerebral hemorrhage, subarachnoid hemorrhage, brain-stem hemorrhage), cardiac disease (myocarditis, coronary artery disease, myocardial infarction), pulmonary disease (pneumonia), and suppurative peritonitis.  
- **Relationship between trauma and intrinsic disease:**  
  Assess the potential interplay between trauma (ante-mortem or post-mortem) and intrinsic disease. Analyze how injuries may have exacerbated underlying pathological processes.  
- **Causal inference:**  
  Examine the role of accidents in the chain of events leading to death. Evaluate whether external forces could have precipitated, triggered, or directly contributed to death, while considering accidental manners such as high-level falls, poisoning, asphyxia (ligature strangulation), drowning, electrocution, and fatal burns.  
- **Synthesis and integration:**  
  Integrate all foregoing information to identify the immediate and contributing causes of death.


</Considerations for the Plan>

<Example>

- **Review the autopsy report and case background records:** … Focus on system-by-system changes and their potential interactions with intrinsic diseases…  
- **In-depth analysis of disease progression and acute decompensation:** … Consider long-term effects of intrinsic diseases and the acute impact of trauma… Evaluate accident scenarios such as high-level falls, poisoning, asphyxia, drowning, electrocution (electrical marks, skin alterations), and fatal burns…  
- **Assess the influence of trauma on intrinsic disease:** … Determine whether trauma, iatrogenic factors, or other circumstances could have precipitated or aggravated pre-existing disease…  
- **Integrated analysis and drafting of conclusions:** … Clarify causal relationships between the accident and disease processes, and specify the principal cause of death and any contributing factors…


</Example>

<context of the task>

{content}

</context of the task>

<task> 

1. {objective}
2. If any mandate or commission is stated in the task background, the plan must be explicitly aligned with that mandate or requirement.

</task> 


"""


)

# prompt from langchain
select_prompt = hub.pull("hwchase17/self-discovery-select")
adapt_prompt = hub.pull("hwchase17/self-discovery-adapt")


class Plan(BaseModel):
    """a plan of action,up to 4 steps, to address the task, and provide the output in Chinese."""

    steps: List[str] = Field(
        description="“Outline the distinct procedural steps to be followed (up to four), with each step presented as a separate list element, and provide the output in Chinese."
    )

### model
model_plan =ChatOpenAI(model="o4-mini", temperature=0)
model_plan_2 = ChatDeepSeek(model="deepseek-chat",temperature=0.3)
model_adapt_2 =ChatOpenAI(model="gpt-5-mini", temperature=0)
model_adapt =ChatOpenAI(model="gpt-5")


### chain
structured_llm_plan = model_plan.with_structured_output(Plan)
structured_llm_plan_2 = model_plan_2.with_structured_output(Plan)
plan_chain = planner_prompt | structured_llm_plan
plan_chain_2 = planner_prompt | structured_llm_plan_2


select_chain = select_prompt | model_adapt | StrOutputParser()

structured_llm_plan_turbo = model_adapt_2.with_structured_output(Plan)

adapt_chain = adapt_prompt | structured_llm_plan_turbo


