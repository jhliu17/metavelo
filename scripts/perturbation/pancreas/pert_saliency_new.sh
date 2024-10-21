export OUTPUT_PATH=outputs/experiment/perturb/pancreas/saliency
export WANDB_API_KEY=YOUR_WANDB_KEY
python perturb.py pancreas-saliency-inverse-loss \
    --pert.perturbation-num 10 \
    --slurm.mode slurm