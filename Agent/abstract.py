from langchain_core.prompts import ChatPromptTemplate,HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek

abstract_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
        ("You're an experienced professor of forensic pathology and you've done multiple autopsies."),
              HumanMessagePromptTemplate.from_template("""
              <Instruction>

              Extract key findings(positive&negative) from the given context related to the cause of death of the deceased. Only provide the extracted content. Be as detailed as possible.
              
              </Instruction>
              
              <Context>

              {context}
              
              </Context>
              
              <Extraction Guidelines>

              - Extract the purpose or specifics of the examination request.
              - Extract key background information on the case.
              - Extract details of the injury as well as the disease.
              - Extract findings(positive&negative) related to the cause or manner of death.
              - Extract findings(positive&negative) related to autopsy and histopathological examination results.
              - Pay special attention to descriptions of the brain, heart, and lungs, and retain original wording.
              - Pay attention to the toxicological screening results.
              - Pay attention to the circumstances of the deceased and preexisting diseases and injuries.
              - Summarize significant pathological changes in other organs(both positive and negative findings).
              - Output Chinese.
              
              </Extraction Guidelines>
              

        """)
              ],

)

tidy_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
              ("You're a seasoned forensic expert."),
              HumanMessagePromptTemplate.from_template("""

              <Instruction>

              Your task is to merge the following sentences into a single, coherent paragraph that flows naturally and maintains a logical sequence of ideas. 
              Retain only the essential information, eliminate redundancy, and disregard irrelevant details.
              Keep only the key information that is clearly relevant to the determination of the cause of death and summarize and streamline the passage as much as possible. 
              Output no more than 400 words (Chinese).

              </Instruction>

              <Context>

              {context}

              </Context>


              """)
              ],

)


#  model
model = ChatOpenAI(model="o4-mini", temperature=0)
model_abstract = ChatDeepSeek(model="deepseek-chat",temperature=0)


# chain
abstract_chain = abstract_prompt | model_abstract | StrOutputParser()
tidy_chain = tidy_prompt | model | StrOutputParser()
