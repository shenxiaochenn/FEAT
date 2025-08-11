CUDA_VISIBLE_DEVICES=4,5 API_PORT=8003 python src/api.py  --model_name_or_path baichuan-inc/Baichuan-M1-14B-Instruct \
	--trust_remote_code True\
	--template baichuan2\

