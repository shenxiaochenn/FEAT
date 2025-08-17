from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek



# Prompt
system = """

<Instruction>

You are a forensic science expert. Your task is to assess the implementability of a given program in the current context.

</Instruction>

<Requirements>

Provide a binary rating of "Yes" or "No."

"Yes" indicates that the plan can be implemented as is.
"No" indicates that the plan requires further external search.

If the rating is "No," provide a query for the external search on the Internet. 
The query should be centered around the cause of death of the deceased and should address the detailed issues related to the cause of death.
The query must be English.
If the rating is "Yes," The query is "no external search is needed".

</Requirements>

"""


answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "User plan: \n\n {question} \n\n Given context: {context}"),
    ]
)



model = ChatDeepSeek(model="deepseek-chat",temperature=0)

class Router(BaseModel):
    """Binary score and query to be searched."""

    binary_score: str = Field(description="plan can be implemented, 'yes' or 'no'")
    search_query: str = Field(description="the query to be searched. The query must be English.")


structured_llm_grader = model.with_structured_output(Router)



router_chain = answer_prompt | structured_llm_grader
