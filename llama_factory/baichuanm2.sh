CUDA_VISIBLE_DEVICES=0,1,2 API_PORT=8004 python src/api.py  --model_name_or_path baichuan-inc/Baichuan-M2-32B \
	--trust_remote_code True\
	--template qwen\
