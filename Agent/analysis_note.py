
from langchain_core.prompts import ChatPromptTemplate,PromptTemplate,HumanMessagePromptTemplate, SystemMessagePromptTemplate,AIMessagePromptTemplate
from pydantic import BaseModel, Field
from openai import OpenAI
from langchain_deepseek import ChatDeepSeek


analysis_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
              ("You are a professor of forensic pathology specializing in analyzing death cases."),
              HumanMessagePromptTemplate.from_template("""
              
            <Instruction>
            
            Compose a cause-of-death analysis note based on the provided case details.
            It is essential to carefully differentiate between the causative and direct causes of death in forensic investigations. 
            Specifically, determining whether trauma serves as the precipitating factor or the primary cause of death is a critical distinction that requires thorough analysis. 
            This distinction has significant implications for the legal and medical understanding of the case. Therefore, conclusions regarding the cause of death must be drawn with utmost caution, ensuring that all factors, including underlying medical conditions, pre-existing vulnerabilities, and the role of external trauma, are fully considered. 
            Rigorous, evidence-based reasoning is necessary to prevent premature or biased conclusions, as this determination influences both clinical and forensic outcomes.
            
            </Instruction>
            
            <Guidelines for Writing the Analysis Note>
            
            **1. Autopsy Findings**:
            
            Summarize the key pathological features or injuries observed during the autopsy.
            Provide a concise description of the location and nature of these findings (e.g., fractures, tissue damage, organ changes), using 3-4 sentences.
            
            **2. Cause of Death Analysis**:
            
            Analyze the direct or indirect connection between these pathological features or injuries and the cause of death.
            Discuss how external factors (e.g., surgery, accidents, violence) might relate to these injuries or pathological conditions.
            
            **3. Pathological Background and Death Correlation**:
            
            Consider the patient's medical history and lifestyle to discuss how pre-existing health conditions influenced the death.
            Evaluate the role of chronic diseases or existing health issues in the death.
            
            **4. Supplementary Test Results**:
            
            Mention any forensic tests performed (e.g., toxicology, histology).
            Explain how these results support or challenge the preliminary cause of death analysis.
            
            **5. Conclusion and Inference**:
            
            Clearly summarize the relationship between the autopsy findings and the cause of death.
            Provide a final forensic opinion based on a comprehensive analysis of the autopsy and supplementary test results.
            Ensure your analysis is thorough, specific, and clearly outlines the scientific rationale and logical reasoning behind each step.
            
            **6. Additional Instructions**:
            
            The output should be a continuous paragraph without subheadings or bullet points.
            Ensuring the use of precise medical terminology for professional accuracy.
            Maintain objectivity and scientific rigor, avoiding any speculative language (e.g., "might," "likely," "possibly").
            
            
            *** Ensure that the structure, format, and expression match the given Examples as similar as possible.***
            The output should be in Chinese.
            
            </Guidelines for Writing the Analysis Note>        
            
            <Context of this Case>
            
            {context}
            
            </Context of this Case>
            
            <Observed Findings>
            
            {obs_result}
            
            </Observed Findings>
            
            <Supplementary Information>
                                    
            {supplements}
            
            </Supplementary Information>
            
            <Examples>
            
            {fewshot}
            
            </Examples>   
                                 

            
              """)
              ],

)

reanalysis_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
              ("You are a professor of forensic pathology specializing in analyzing death cases."),
              HumanMessagePromptTemplate.from_template("""

            <Instruction>

            Your task is to enhance the following statement used for a cause-of-death analysis, making it more scientifically rigorous and detailed. 
            First, review the provided example, which illustrates how to make a well-constructed cause-of-death analysis statement(Revised[good example] vs Original[bad example]). 
            Then, revise the given statement with the same level of rigor, particularly focusing on the method of analyzing injury relationships as shown in the example. 
            The revised statement should be in Chinese and limited to 400 words.
            Revised Statements must not contain words such as maybe（可能） or perhaps（也许）.etc.
            Revised Statements must be rigorously affirmative.            
            It is essential to carefully differentiate between the causative and direct causes of death in forensic investigations. 
            Specifically, determining whether trauma serves as the precipitating factor or the primary cause of death is a critical distinction that requires thorough analysis. 
            This distinction has significant implications for the legal and medical understanding of the case. 
            Therefore, conclusions regarding the cause of death must be drawn with utmost caution, ensuring that all factors, including underlying medical conditions, pre-existing vulnerabilities, and the role of external trauma, are fully considered. 
            Rigorous, evidence-based reasoning is necessary to prevent premature or biased conclusions, as this determination influences both clinical and forensic outcomes.

            </Instruction>

            <Example>

            Original: 

            根据法医学解剖检验结果，龚安文的主要病理特征包括肺部水肿、心脏功能不全及脑部循环障碍。尸检未发现明显外部创伤，毒物分析排除中毒可能。肺部水肿伴随心脏脂肪组织增生及心肌纤维波浪状改变，明确指向心源性肺水肿，导致急性呼吸衰竭和心功能不全。脑部血管扩张和淤血显示存在脑部循环障碍，进一步加重多器官功能不全。尸体上的陈旧瘢痕和电极印痕表明生前曾经历心肺复苏，提示心肺功能异常。结合死者生前健康状况和临床记录，需确认是否存在未被诊断的心脏疾病。综合分析，龚安文的死亡主要由心源性肺水肿引发的急性呼吸衰竭和心功能不全导致，脑部循环障碍和多器官功能不全为促成因素。建议进一步调查其生前医疗记录，以确认具体死亡原因。

            Revised:

            对龚安文的尸体进行系统法医学解剖检验主要发现有：出血性肺炎，肺重度水肿；其余主要脏器主要呈淤血、水肿、自溶改变；系统法医学尸体检验未发现致命性损伤。系统毒物分析，体内未检出上述常见毒物。本例肺部病变主要为个别大叶的出血性炎症，根据其病变特征分析，符合大叶性肺炎早期病变（充血水肿期），病变剧烈可致病人急性重度导致休克或因肺水肿引起急性致命性呼吸衰竭。

            Original:

            对王淑婵尸体进行系统法医学解剖检验，并结合医院病历，主要发现如下：2021年9月9日，死者因交通事故导致多发性创伤，具体包括肝左叶裂伤、胰腺显著水肿及左肺严重感染。临床上，死者接受了肝破裂修补术，但术后继发急性胰腺炎及肺部感染，最终导致多器官功能衰竭。尸检结果显示：左胸腔内有大量积液，肝左叶裂伤术后形成坏死区，胰腺组织水肿，符合急性胰腺炎的病理表现。组织病理学检验进一步证实：肺部存在感染，肝内胆汁淤积并伴有左叶坏死，胰腺周围脂肪组织内可见少量红细胞渗出。系统毒物检验未发现常见毒物，排除中毒可能性。综合分析，死者因交通事故导致的多发性创伤是其死亡的根本原因，继发的急性胰腺炎及肺部感染是直接导致多器官功能衰竭的因素。交通事故所致的损伤与多器官功能衰竭之间存在明确的因果关系，死者的死亡符合因交通事故引发的多发性创伤继发急性胰腺炎及肺部感染，最终导致多器官功能衰竭的病理过程。

            Revised: 

            对王淑婵尸体进行系统法医学解剖检验并结合医院病历，主要发现有：2021-09-09因交通事故致肝破裂，临床行肝破裂修补+肝胃带止血+腹腔灌洗术，术后继发肝左叶胆汁瘤伴急性胰腺炎，局限性腹膜炎，肺部感染等，行腹腔动脉及肠系膜上动脉造影术+肝总动脉栓塞术，于2021-11-17死亡。尸检见：左胸腔大量胸腔积液；肝左叶裂伤术后，巨大腹腔囊肿形成，腹壁结缔组织多发坏死。组织病理学检验见：肺部感染，肝内胆汁淤积并左叶干酪样坏死，局限性腹膜炎等。系统毒物检验未发现上述常见毒物。本例死者符合因交通事故受伤致肝破裂，修补术后继发外伤性肝左叶胆汁瘤伴急性胰腺炎，局限性腹膜炎，肺部感染等，导致多器官功能衰竭而死亡。

            Original: 

            对死者唐志有的尸体进行系统法医学解剖检验，并结合医院病历进行综合分析，主要发现如下：死者在与姚舜业争吵后出现急性腹痛，入院后被初步诊断为空腔脏器穿孔，并接受了回肠穿孔修补术。术后，患者出现感染性休克和严重脓毒血症，最终导致多脏器功能衰竭。尸检显示腹部有手术缝合切口及大量黄绿色脓性分泌物，明确提示严重腹腔感染。病理检验证实多个器官存在炎症和损伤，支持感染性休克为主要死亡原因。毒物分析未发现毒物，排除了中毒可能性。法医学分析指出，腹部外伤是导致回肠穿孔的直接原因，进而引发严重感染和并发症，最终导致死亡。综合分析，唐志有的死亡与腹部外伤直接相关，腹部外伤是其死亡的直接原因，强调了及时医疗干预的重要性。

            Revised: 

            对死者唐志有尸体进行系统法医学解剖检验主要发现有：外伤性小肠破裂继发弥漫性化脓性腹膜炎、脓毒血症，临床给予小肠修补术、抗感染、止血、补液等治疗。尸体解剖见：腹腔感染：腹腔内大量黄绿色脓性分泌物，腹腔脏器被膜大量脓苔附着并广泛粘连，小肠破口周围组织水肿，破口边缘间断缝合结扎线部分脱落。组织病理学检验多脏器呈非特异性水肿等改变。系统毒物检验未发现上述常见毒物。继发性腹膜炎是指因腹部损伤引起腹腔脏器破裂或腹壁开放性创口等导致的腹膜炎。急性腹膜炎时，腹膜呈弥漫性化脓性炎症，可导致感染性中毒性休克，引起多脏器功能衰竭死亡。本例死者系因小肠外伤性破裂，继发腹腔感染、弥漫性化脓性腹膜炎致感染中毒性休克而死亡；外伤性小肠破裂是其死亡的根本原因。

            </Example>

            <This Case>

            Original:

            {context}

            </This Case>


              """)
              ],

)

human_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
              ("You are a professor of forensic pathology specializing in analyzing death cases."),
              HumanMessagePromptTemplate.from_template("""

            <Instruction>

            Your task is to refine and enhance the following cause-of-death analysis based on existing feedback, making it more scientific, rigorous, and fluent. 
            Please ensure the revised text is written in Chinese and does not exceed 400 characters. 
            You may refer to the example format below for guidance:

            <\Instruction>


            <example>

            {fewshot}

            </example>


            <Original analytical note>

            {context}

             <\Original analytical note>

            <human feedback>

            {human}

            </human feedback>


              """)
              ],

)

conclusion_prompt = ChatPromptTemplate(
    messages=[SystemMessagePromptTemplate.from_template
              ("You are a professor of forensic pathology specializing in analyzing death cases."),
              HumanMessagePromptTemplate.from_template("""

            <Instruction>

             Your task is to select the most appropriate conclusion from a set of candidate conclusions based on a detailed analysis of the case. Follow these steps:

             1. **Review the Analysis**: Carefully read and understand the provided analysis of the case, focusing on the key facts, evidence, and findings.
             2. **Evaluate Candidate Conclusions**: Assess each candidate conclusion against the analysis. Identify which conclusion most accurately aligns with the evidence and facts presented.
             3. **Formulate the Final Conclusion**: Choose the candidate conclusion that best explains the cause of death in a clear, concise, and definitive manner. Avoid any speculative language (e.g., "may," "might," "could").
             4. **Language Requirement**: Provide your final conclusion in Chinese.

            </Instruction>

            <Analysis of the Case>

             {context}

            </Analysis of the Case>

            <Candidate Conclusions>


            {candicate}


            </Candidate Conclusions>



              """)
              ],

)





class Analytical_note(BaseModel):
    """ Complete content of the analytical note (Refer to similar examples of expression whenever possible.)"""

    analytical_note: str = Field(description="analytical note of the given case")

class Analytical_revised(BaseModel):
    """ Complete content of the Revised analytical note """

    Revised: str = Field(description="Revised Statement of analytical note,The presentation should be scientifically rigorous and fluent.")


class Conclusion_analysis(BaseModel):
    """ Content of the analytical conclusion """

    analytical_con: str = Field(description="analytical conclusion,usually one short sentence.")


model= ChatDeepSeek(model="deepseek-chat",temperature=0)


## Collaborative Summarization

structured_llm_analysis = model.with_structured_output(Analytical_note)
analysis_chain = analysis_prompt | structured_llm_analysis


structured_llm_revised = model.with_structured_output(Analytical_revised)
reanalysis_chain = reanalysis_prompt | structured_llm_revised


## human-in-the-loop

human_chain = human_prompt | structured_llm_revised



## conclusion

structured_llm_conclusion = model.with_structured_output(Conclusion_analysis)
conclusion_chain = conclusion_prompt | structured_llm_conclusion




#####  local Forensic-LLM

def conclusion(ana):
    client = OpenAI(api_key="EMPTY", base_url="http://0.0.0.0:8002/v1/")
    tmp = ana +"\n 请根据此分析说明总结鉴定意见"
    messages = [{"role": "system", "content": "你是一个经验丰富的法医病理医生。"},
                {"role": "user", "content": tmp}
                ]
    l_conclusion=[]
    for i in range(30):
        response = client.chat.completions.create(
            model="zhenyuan",
            messages=messages,
            stream=False,
        )
        l_conclusion.append(response.choices[0].message.content)
    return l_conclusion
