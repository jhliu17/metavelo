OUTPUT_FOLDER=outputs/eval/pancreas/pert_ode_model_$(date +%Y%m%d_%H%M%S)

python perturb_eval.py --trainer_ckpt_path outputs/train/pancreas/pert_ode_model_20231221_155249/model-final.pt \
    --eval_data_folder datasets/pretrain/pancreas/trajs/sampled_traj_test.npz \
    --model.dim 64 \
    --model.input-dim 668 \
    --pert.model-type trigger \
    --pert.perturbation-num 10 \
    --pert.trigger.replace-num-candidates 32 \
    --pert.trigger.use-optim-eval \
    --trainer.pert-num-steps 500 \
    --trainer.pert-state-step -1 \
    --trainer.train-batch-size 64 \
    --trainer.save-and-sample-every 10 \
    --trainer.num-workers 0 \
    --trainer.data-folder datasets/pretrain/pancreas/trajs/sampled_traj.npz \
    --trainer.output-folder $OUTPUT_FOLDER \
    --trainer.ann_prc_data datasets/pretrain/pancreas/data/pancreas.h5ad \
    --trainer.ann_raw_data datasets/pretrain/pancreas/data/pancreas.h5ad.raw \
    --trainer.deep-velo-model-checkpoint outputs/pretrain/pancreas/model/autoencoder.pth \
    --trainer.deep-velo-model-dim 668 \
    --trainer.deep-velo-scaling-factor 0.8170944342283816 \
    --trainer.deep-velo-intermediate-step 3 \
    --trainer.t-span 0 1 \
    --trainer.t-step 65 \
    --trainer.seq-step 5 \
    --head-trainer.ann-prc-data datasets/pretrain/pancreas/data/pancreas.h5ad \
    --head-trainer.output-folder $OUTPUT_FOLDER/head_model \
    --head-trainer.train-num-steps 3000 \
    --head-trainer.save-and-eval-every 500 \
    --head-trainer.cell-type-list Ductal 'Ngn3 low EP' 'Ngn3 high EP' Pre-endocrine Beta Alpha Delta Epsilon \
    --head-trainer.tgt-cell-type Alpha \
    --wandb.project eval \
    --slurm.mode debug \
    --slurm.slurm-output-folder $OUTPUT_FOLDER/slurm \
    --slurm.cpus-per-task 6