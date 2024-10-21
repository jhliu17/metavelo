from src.model.ode import RNAVeloNetConfig
from src.train.cell_type_cls import (
    CellTypeClassifierTrainerConfig,
)
from src.trainer.metavelo import PerturbationTrainerConfig
from src.slurm import SlurmConfig
from src.pert import (
    PertModuleConfig,
    SubsetSamplingPertModuleConfig,
    SAGEPertModuleConfig,
    LIMEPertModuleConfig,
    FIMAPPertModuleConfig,
    CXPlainPertModuleConfig,
    PermutationPertModuleConfig,
    SaliencyPertModuleConfig,
    ApproximationPertModuleConfig,
)
from src.pert.cxplain.train import CXPlainTrainerConfig
from configs.utils import get_output_path

output_path: str = get_output_path()

trainer_ckpt_path = (
    "outputs/experiment/train/dentategyrus/ode_model_all_20240122_154741/model-3.pt"
)

model = RNAVeloNetConfig(dim=64, input_dim=1087)

head_trainer = CellTypeClassifierTrainerConfig(
    dataset_name="dentategyrus",
    ann_prc_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad",
    train_num_steps=3000,
    save_and_eval_every=500,
    cell_type_list=[
        "CA",
        "CA2-3-4",
        "GlialProg",
        "Granule",
        "ImmAstro",
        "Granule",
        "Nbl1",
        "Nbl2",
        "OPC",
        "RadialGlia",
        "RadialGlia2",
        "nIPC",
    ],
    tgt_cell_type="CA",
    output_folder=f"{output_path}/head_model",
)

head_trainer_inverse = CellTypeClassifierTrainerConfig(
    dataset_name="dentategyrus",
    ann_prc_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad",
    train_num_steps=3000,
    save_and_eval_every=500,
    cell_type_list=[
        "CA",
        "CA2-3-4",
        "GlialProg",
        "Granule",
        "ImmAstro",
        "Granule",
        "Nbl1",
        "Nbl2",
        "OPC",
        "RadialGlia",
        "RadialGlia2",
        "nIPC",
    ],
    tgt_cell_type="Granule",
    output_folder=f"{output_path}/head_model",
)

binary_head_trainer = CellTypeClassifierTrainerConfig(
    dataset_name="dentategyrus",
    ann_prc_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad",
    train_num_steps=3000,
    save_and_eval_every=500,
    cell_type_list=[
        "CA",
        "Granule",
    ],
    tgt_cell_type="CA",
    output_folder=f"{output_path}/head_model",
)

binary_head_trainer_inverse = CellTypeClassifierTrainerConfig(
    dataset_name="dentategyrus",
    ann_prc_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad",
    train_num_steps=3000,
    save_and_eval_every=500,
    cell_type_list=[
        "CA",
        "Granule",
    ],
    tgt_cell_type="Granule",
    output_folder=f"{output_path}/head_model",
)

perturb_trainer = PerturbationTrainerConfig(
    pert_num_steps=3000,
    pert_state_step=-1,
    train_batch_size=64,
    save_and_sample_every=1000,
    num_workers=4,
    dataset_name="dentategyrus",
    output_folder=output_path,
    t_span=(0, 1),
    t_step=65,
    seq_step=5,
    data_folder="datasets/pretrain/dentategyrus/trajs/sampled_traj_train.npz",
    eval_data_folder="datasets/pretrain/dentategyrus/trajs/sampled_traj_val.npz",
    test_data_folder="datasets/pretrain/dentategyrus/trajs/sampled_traj_test.npz",
    ann_prc_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad",
    ann_raw_data="datasets/pretrain/dentategyrus/data/dentategyrus.h5ad.raw",
    starting_cell_type="Nbl2",
    train_only_starting_cell_type_data=True,
    cell_type_ratio_keys=["Granule", "CA"],
    deep_velo_model_checkpoint="datasets/pretrain/dentategyrus/model/autoencoder.pth",
    deep_velo_model_dim=1087,
    deep_velo_scaling_factor=1.2588072545606313,
    deep_velo_intermediate_step=3,
)

slurm = SlurmConfig(
    mode="slurm",
    cpus_per_task=4,
    node_list="laniakea",
    slurm_output_folder=f"{output_path}/slurm",
)

subset_sampling_pert = PertModuleConfig(
    model_type="subset_sampling",
    perturbation_num=10,
    subset_sampling=SubsetSamplingPertModuleConfig(
        use_scheduler=False,
        lr=1e-3,
        tau=0.1,
        tau_start=2,
        tau_anneal_steps=3000,
        tau_scheduler_name="linear",
        hard=False,
        sampler_pert_type="parameterized_subset_sampling",
        sampler_type="subset_topk",
        parameterized_embedding_dim=128,
        parameterized_hidden_dim=64,
        optimizer_name="Adam",
    ),
)


subset_sampling_subset_sampler_pert = PertModuleConfig(
    model_type="subset_sampling",
    perturbation_num=10,
    subset_sampling=SubsetSamplingPertModuleConfig(
        use_scheduler=False,
        lr=1e-3,
        tau=0.1,
        tau_start=2,
        tau_anneal_steps=3000,
        tau_scheduler_name="linear",
        hard=False,
        sampler_pert_type="parameterized_subset_sampling",
        sampler_type="subset",
        parameterized_embedding_dim=128,
        parameterized_hidden_dim=64,
        optimizer_name="Adam",
    ),
)

sage_pert = PertModuleConfig(
    model_type="sage",
    perturbation_num=10,
    sage=SAGEPertModuleConfig(
        batch_size=128, n_permutations=25600, detect_convergence=False
    ),
)

lime_pert = PertModuleConfig(
    model_type="lime",
    perturbation_num=10,
    lime=LIMEPertModuleConfig(
        mask_type="random",
        neighbor_size=1024,
        neighbor_feat_num=120000,
        feature_selection="auto",
        distance_metric="cosine",
    ),
)

cxplain_pert = PertModuleConfig(
    model_type="cxplain",
    perturbation_num=10,
    cxplain=CXPlainPertModuleConfig(
        mask_type="sequence",
        batch_size=128,
        trainer_config=CXPlainTrainerConfig(
            model_type="mlp",
            batch_size=128,
            epoch=500,
            early_stopping_patience=10,
            num_layers=4,
            num_units=1087,
            learning_rate=5e-4,
            downsample_factors=2,
        ),
    ),
)

fimap_pert = PertModuleConfig(
    model_type="fimap",
    perturbation_num=10,
    fimap=FIMAPPertModuleConfig(
        tau=0.5,
        regularization_weight=1e-1,
        lr=1e-3,
        optimizer_name="Adam",
    ),
)

permutation_pert = PertModuleConfig(
    model_type="permutation",
    perturbation_num=10,
    permutation=PermutationPertModuleConfig(
        trigger_pert_type="trigger_perturbation",
    ),
)

saliency_pert = PertModuleConfig(
    model_type="saliency",
    perturbation_num=10,
    saliency=SaliencyPertModuleConfig(
        smooth_input=False, trigger_pert_type="trigger_perturbation"
    ),
)

smooth_saliency_pert = PertModuleConfig(
    model_type="saliency",
    perturbation_num=10,
    saliency=SaliencyPertModuleConfig(
        smooth_input=True, smooth_number=64, trigger_pert_type="trigger_perturbation"
    ),
)

approximation_pert = PertModuleConfig(
    model_type="approximation",
    perturbation_num=10,
    saliency=ApproximationPertModuleConfig(
        smooth_input=False, trigger_pert_type="trigger_perturbation"
    ),
)

permutation_test_pert = PertModuleConfig(
    model_type="permutation",
    perturbation_num=10,
    permutation=PermutationPertModuleConfig(
        trigger_pert_type="trigger_perturbation",
        strategy="permutation",
        permutation_iter_num=16,
    ),
)

mean_importance_pert = PertModuleConfig(
    model_type="permutation",
    perturbation_num=10,
    permutation=PermutationPertModuleConfig(
        trigger_pert_type="trigger_perturbation",
        strategy="mean",
    ),
)

feature_ablation_pert = PertModuleConfig(
    model_type="permutation",
    perturbation_num=10,
    permutation=PermutationPertModuleConfig(
        trigger_pert_type="trigger_perturbation",
        strategy="ablation",
    ),
)