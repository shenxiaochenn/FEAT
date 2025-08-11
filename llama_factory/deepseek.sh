CUDA_VISIBLE_DEVICES=6,7 API_PORT=8002 python src/api.py  --model_name_or_path deepseek-ai/DeepSeek-R1-Distill-Llama-8B \
	--adapter_name_or_path saves/deepseek/checkpoint-5500 \
	--template deepseek3\
	--finetuning_type lora

