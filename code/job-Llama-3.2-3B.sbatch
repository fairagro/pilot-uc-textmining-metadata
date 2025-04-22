#!/bin/bash
#SBATCH --partition=mlgpu_devel
#SBATCH --time=1:00:00
#SBATCH --gpus=1
#SBATCH --ntasks=1



module load CUDA/12.6.0


source ~/.bashrc
conda init
conda deactivate 
conda activate Llama

python NER_Prompting_text-Llama-3.2-3B.py