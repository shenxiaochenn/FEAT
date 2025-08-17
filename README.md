
FEAT :monkey_face: <img src="docs/demo.png" width="200px" align="right" />
===========
[![arXiv](https://img.shields.io/badge/Arxiv-2508.04107-b31b1b.svg?logo=arXiv)](http://arxiv.org/abs/2508.07950)

**FEAT is a modular, multi-agent architecture for forensic cause-of-death analysis that transforms heterogeneous inputs into transparent, auditable conclusions.**
*A Planner* ingests case materials (basic demographics, pathological anatomy, toxicology, scene notes) and performs self-discovered task decomposition, sequencing subtasks and routing them to role-specific Local Solvers. 
*Local Solvers* apply tool-augmented ReAct reasoning to generate intermediate findings and rationales for their assigned domains (e.g., pathology, toxicology, clinical history).
*A Reflection & Memory module* monitors progress, critiques outputs, caches evidence, and iteratively refines hypotheses to reduce error propagation. 
*A Global Solver* then consolidates solver outputs using hierarchical retrieval-augmented generation over a curated Chinese-language medicolegal corpus, combined with locally fine-tuned LLMs, to synthesize a long-form analysis and a concise cause-of-death conclusion with evidence traceability. 

## FEAT: A Multi-Agent Forensic AI System with Domain-Adapted Large Language Model for Automated Cause-of-Death Analysis

<div align=center>
<img src="docs/fig1.jpeg" width="800px" />
</div>


## 👀 Updates: 
* 15/08/2025: We are currently updating the code repository of FEAT.

## 🙏 Acknowledgments
This code is developed on the top of [LangChain](https://github.com/langchain-ai/langchain), [LangGraph](https://github.com/langchain-ai/langgraph),[Langsmith](https://github.com/langchain-ai/langsmith-sdk) and [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory)

## ✉️ Contact

Email: chunfeng.lian@xjtu.edu.cn, wzy218@xjtu.edu.cn,   and  shenxiaochen@stu.xjtu.edu.cn  Any kind discussions are welcomed!

---



## 📖 Citation
If our work is useful for your research, please consider cite:
```bibtex
@article{shen2025feat,
  title={FEAT: A Multi-Agent Forensic AI System with Domain-Adapted Large Language Model for Automated Cause-of-Death Analysis},
  author={Shen, Chen and Zhang, Wanqing and Li, Kehan and Huang, Erwen and Bi, Haitao and Fan, Aiying and Shen, Yiwen and Dong, Hongmei and Zhang, Ji and Shao, Yuming and others},
  journal={arXiv preprint arXiv:2508.07950
        
        
        
        
        
        },
  year={2025}
}
```
