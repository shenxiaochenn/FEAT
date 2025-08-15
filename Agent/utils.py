from typing import Annotated
from langchain_core.tools import tool
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from chat_agent_executor import  create_react_agent
from langchain_deepseek import ChatDeepSeek


prompt_book = hub.pull("pwoc517/more-crafted-rag-prompt")
forensic_book=Chroma(embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),persist_directory="/home/wangzhenyuan/report/forensic_book_1104/")
retriever_book = forensic_book.as_retriever(search_kwargs={"k": 4})

def format_docs_book(docs):
    return "\n\n".join(doc.page_content for doc in docs)


model = ChatDeepSeek(model="deepseek-chat",temperature=0)


###  forensic domain knowledge tool
forensic_chain = (
    {"context": retriever_book | format_docs_book, "question": RunnablePassthrough()}
    | prompt_book
    | model
    | StrOutputParser()
)
forensic_book = forensic_chain.as_tool(
    name="Forensic_pathology_books", description="Given a text passage, retrieve relevant knowledge pertaining to forensic pathology."
)

### web_search  tool
search = TavilySearchResults(max_results=2)


### pubmed  tool
Pubmed = PubmedQueryRun()



### mdeical model tool
base_url_ = "http://0.0.0.0:8003/v1/"
client_ = OpenAI(api_key="EMPTY", base_url=base_url_)

@tool
def medicine_model(text: Annotated[str, "Specific issues related to medicine"]) -> str:
    """ Answer common medical-related questions."""
    messages = [{"role": "system", "content": "You are an experienced forensic pathologist. Please provide scientifically rigorous and concise answers to the following specific questions. Think step by step!"},
                {"role": "user", "content": text}
                ]

    response = client_.chat.completions.create(
        model="zhenyuan",
        messages=messages,
        stream=False,
    )
    return response.choices[0].message.content


#############################################

tools = [forensic_book,medicine_model,Pubmed,search]

agent_executor_graph = create_react_agent(model, tools)

#############################################




#### reflexion #####


class Reflection_and_Search(BaseModel):
    """Critique, Reflect, and Recommend Search Queries."""

    missing: str = Field(description="Critique of what is missing.")
    shortcoming: str = Field(description="Critique of what needs to improve.")
    search_queries: list[str] = Field(
        description="1-2 search queries(Chinese) for researching improvements to address the critique of your current discovered & analyzed results."
    )

reflexion_prompt = ChatPromptTemplate.from_template(
"""
<Instruction>

You're a seasoned forensic expert tasked with critically evaluating the findings of a complex case.

1. Critique and Reflect: Rigorously review the discovered and analyzed results based on the task and the specific context of this case. Identify any gaps, inconsistencies, or areas where the analysis could be improved. Be stringent in your critique to ensure maximum enhancement and reliability of the results.
2. Recommend Search Queries: Suggest targeted search queries that could be used to gather additional information. These queries should aim to fill in the gaps, verify findings, and strengthen the overall analysis. Ensure the recommendations are specific, actionable, and directly relevant to the case context.

</Instruction>

<Task>

In relation to the case mandate (if any) or specific commission requirements (if any), systematically explore and analyze in detail all factors potentially associated with the decedent’s cause of death.

</Task>

<Context of this Case>

{context}

</Context of this Case>

<Discovered & Analyzed Results>

{discovered}

</Discovered & Analyzed Results>

Note: Search Queries must be Chinese.
"""
)
model_re = ChatOpenAI(model="o4-mini", temperature=0)
reflexion_chain = reflexion_prompt | model_re.with_structured_output(Reflection_and_Search)



################### H-RAG
reference=Chroma(embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),persist_directory="/home/wangzhenyuan/report/analytical_note_1104/")
retriever_reference = reference.as_retriever(search_kwargs={"k": 1})
