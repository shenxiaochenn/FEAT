from typing import List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek

update_planner_prompt = ChatPromptTemplate.from_template(
    """
<Instruction>
You are a forensic planning update assistant. After one plan step has been executed, your task is to review the
execution observations and revise ONLY the remaining steps of the plan. Do not include the step that was just executed.

STRICT COUNT REQUIREMENT:
- You MUST return exactly {n_steps} steps (unless {n_steps} == 0, then return an empty list []).
- Do not merge or split steps; keep the total count unchanged.
- If a new step is needed but the count must remain constant, REPLACE the least relevant original step.
- If a step should be removed, REPLACE it with the most appropriate follow-up step so that the total count remains constant.

Other requirements:
- The updated plan must stay tightly linked to analysis of the decedent’s cause of death.
- The decedent’s name must not appear anywhere.
- If any mandate/commission is stated in the background, keep the plan explicitly aligned with that mandate.
- Maintain the order as intended execution order (earliest next step first).
- Keep each step concise, specific, and executable.
- IMPORTANT: Output the steps in Chinese.
</Instruction>

<Inputs>
- Objective: {objective}
- Context of the task: {content}
- Just-executed step: {last_step}
- Observations/results from the executed step:
{observations}

- Original remaining plan (one step per line, in intended execution order):
{remaining_plan}
</Inputs>

<Update rules>
1) Remove/replace steps that are now redundant, satisfied, contradicted by observations, or out of scope.
2) Insert missing prerequisite/follow-up steps ONLY by replacing an existing step (to preserve the count).
3) Reorder steps only when it materially improves correctness or coherence (still returning exactly {n_steps} steps).
4) If the original remaining plan is empty and no additions are needed, return [].
5) If NO CHANGE is needed, return exactly the original remaining steps (same order, same count).
</Update rules>

<Output format>
Return ONLY JSON with the single field "steps": [ ... ].
Do not include explanations or extra fields.
    """
)


class PlanUpdate(BaseModel):
    """Updated remaining plan steps (Chinese, exactly N items where N = remaining steps)."""
    steps: List[str] = Field(
        description="Updated remaining plan steps. If no change is needed, return the original remaining steps unchanged. "
                    "The number of steps MUST equal the number of original remaining steps. And, Output the steps in Chinese."
    )


model_plan = ChatDeepSeek(model="deepseek-chat",temperature=0)

structured_llm_update = model_plan.with_structured_output(PlanUpdate)

update_plan_chain = update_planner_prompt | structured_llm_update