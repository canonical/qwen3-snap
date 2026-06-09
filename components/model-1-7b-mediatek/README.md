The model files for MediaTek npu are not added in git repo.

Please follow this instruction to download the model:
1. Download [model-1-7b-mediatek.tar.gz](https://drive.google.com/file/d/1s_7j-H6qmAWL46HKVVq9XTXN_oV0FvkP/view?usp=sharing)
2. unpack 2048c and tokenizer from model-1-7b-mediatek.tar.gz into this folder:
   ```
   tar -zxf model-1-7b-mediatek.tar.gz -C qwen3-snap/components/model-1-7b-mediatek
   ```

You are expected to have these files:
```
2048c/
├── dynamic_tflite_output_128t2048c_0.dla
└── dynamic_tflite_output_1t2048c_0.dla
tokenizer/
├── added_tokens.yaml
├── embedding_int16.bin
├── merges.txt
└── vocab.txt
```