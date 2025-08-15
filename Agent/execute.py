
from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek



execute_prompt =ChatPromptTemplate.from_template("""

<Instruction>

You are a professor of forensic medicine, tasked with performing detailed autopsy analyses to determine the cause and manner of death. 
A critical part of your role involves distinguishing between trauma-induced injuries and potential spontaneous medical conditions, such as subarachnoid hemorrhage, which may present with similar symptoms. 
The distinction between trauma and disease is vital for the integrity of the investigation and must be made with meticulous care.
This analysis will proceed in structured phases, with each phase focusing on a specific aspect of the investigation. 
At each stage(PLAN or TASK), the results and conclusions should be closely linked to the immediate context and the phase under examination.
Focus on key diseases such as **myocarditis**, **pneumonia**, **coronary heart disease**, **coronary atherosclerosis**, **cerebral hemorrhage**, **various types of shock(Toxic Shock, Anaphylactic Shock, Traumatic shock)**, **subarachnoid hemorrhage**, **brain stem hemorrhage**,**cerebral hemorrhage**, **purulent peritonitis**and **craniocerebral injuries**. 
Consider also the circumstances of accidental death, for example, **falling**, **poisoning**, **choking**, **drowning**, **electrocution**, **burning**, etc.

Each phase of the investigation will build upon the previous, but each must be handled independently with direct relevance to the facts at hand. 
It is essential to focus solely on the current task at each stage and ensure that all judgments are based on the findings and information specific to that moment in the investigation.
It is essential to carefully differentiate between the causative and direct causes of death in forensic investigations. 
Specifically, determining whether trauma serves as the precipitating factor or the primary cause of death is a critical distinction that requires thorough analysis. 
This distinction has significant implications for the legal and medical understanding of the case. 
Therefore, conclusions regarding the cause of death must be drawn with utmost caution, ensuring that all factors, including underlying medical conditions, pre-existing vulnerabilities, and the role of external trauma, are fully considered. 
Rigorous, evidence-based reasoning is necessary to prevent premature or biased conclusions, as this determination influences both clinical and forensic outcomes.


**Note**:
            
- Context is the main element of the case. 
- Observed information is the execution of the previous plans of the case.
- Forensic science knowledge is information obtained from reliable internet sources and should be used to support to solve this plan.
- Irrelevant elements can be ignored in implementation planning.
- Result(execute_result) must be based on the content obtained from a comprehensive analysis of all the content, i.e. ,Context of this case.

</Instruction>

<Context of this case (key information)>

{context}

</Context of this case (key information)>

<Observed information  of this case (Supplementary information)>

{observed}

</Observed information  of this case (Supplementary information)>

<Forensic science knowledge  of this case (Supplementary information)>

{content}

</Forensic science knowledge  of this case (Supplementary information)>

<Plan of this case need to be completed (Current task need to do)>

{plan}

</Plan of this case need to be completed (Current task need to do)>

<Output format>
Return ONLY JSON with the single field "execute_result": [ ... ].

""")


class Execute_Result(BaseModel):

    """ Execute Results of the plan of this case. Outputs in Chinese!"""

    execute_result: List[str] = Field(description=" Results and findings (Chinese) from the implementation of the given plan(task)")



model = ChatDeepSeek(model="deepseek-chat",temperature=0)

structured_llm_execute = model.with_structured_output(Execute_Result)
execute_chain = execute_prompt | structured_llm_execute

######################

