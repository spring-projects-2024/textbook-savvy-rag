#!/bin/bash

#SBATCH --job-name="run_file"
#SBATCH --account=3144860
#SBATCH --partition=gpu
#SBATCH --gpus=1
#SBATCH --output=/home/3144860/wiki/wiki-savvy-rag/out/%x_%j.out # %x gives job name and %j gives job id
#SBATCH --error=/home/3144860/wiki/wiki-savvy-rag/err/%x_%j.er
#SBATCH --nodelist=gnode02
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --qos=normal


cd /home/3144860/wiki/wiki-savvy-rag

source /home/3144860/miniconda3/bin/activate nlp

conda info --envs

python3 scripts/benchmark/mmlu.py --config_path "configs/llm_vm.yaml" --log_answers True --k_shot 0 --use_rag 1 --inference_type "naive" --n_docs_retrieved 3 --n_samples 500

conda deactivate
