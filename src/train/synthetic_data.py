from pathlib import Path
import torch
import torch.nn as nn
import numpy as np

from tqdm import tqdm

from torch.optim import Adam
from torch.utils.data import TensorDataset, DataLoader, random_split
from dataclasses import dataclass, field
from torch.distributions import Normal
from typing import List, Tuple
from .base import BaseTrainer
from ..utils import divisible_by, cycle_dataloader


@dataclass
class SyntheticDataClassifierTrainerConfig:
    # data folder
    data_folder: str

    # output folder
    output_folder: str = "outputs"

    # synthetic dataset name
    synthetic_dataset_name: str = "nonlinear_additive"

    # overwrite synthetic dataset
    overwrite_synthetic_dataset: bool = False

    # model lr
    train_lr: float = 1e-4

    # morel adam
    adam_betas: Tuple[float, float] = (0.9, 0.99)

    # train step
    train_num_steps: int = 1000

    # model training batch size
    train_batch_size: int = 64

    # model evaluation batch size
    eval_batch_size: int = 64

    # eval and save model every
    save_and_eval_every: int = 1000

    # model num type list
    num_type_list: List[str] = field(default_factory=lambda: ["0", "1"])

    # target num type
    tgt_num_type: str = "1"

    # synthetic data size
    synthetic_data_size: int = 10000

    # synthetic data feature dim
    synthetic_data_feature_dim: int = 3

    # training set ratio
    train_set_ratio: float = 0.8

    # hidden dim
    hidden_dim: int = 64

    # device
    num_workers: int = 0

    use_cuda: bool = True

    seed: int = 2024


def get_synthetic_data(dataset_name: str, datasize: int, feature_dim: int):
    normal = Normal(torch.tensor([0.0]), torch.tensor([1.0]))
    X = normal.sample((datasize, feature_dim)).squeeze(-1)

    if dataset_name == "nonlinear_additive":
        y = torch.exp(X[:, 0] + X[:, 1] * X[:, 2])
    elif dataset_name == "orange_skin_additive":
        y = torch.exp(X[:, 0] + X[:, 1] * X[:, 2])
    else:
        raise ValueError(f"Unknown synthetic dataset: {dataset_name}")

    prob_1 = y / (1 + y)
    prob_0 = 1 - prob_1
    y = torch.stack([prob_0, prob_1], dim=1)
    return X, y


class SyntheticDataClassifierTrainer(BaseTrainer):
    def __init__(
        self,
        model: nn.Module,
        *,
        args: SyntheticDataClassifierTrainerConfig,
        has_wandb_writer: bool = False,
    ):
        super().__init__(args.output_folder, has_wandb_writer=has_wandb_writer)

        # device setting
        self.use_cuda = args.use_cuda

        # train
        self.args = args
        self.num_type_dict = {k: v for v, k in enumerate(args.num_type_list)}
        self.tgt_ind = self.num_type_dict[args.tgt_num_type]
        self.train_batch_size = args.train_batch_size
        self.eval_batch_size = args.eval_batch_size
        self.save_and_eval_every = args.save_and_eval_every
        self.seed = args.seed

        train_dataset, eval_dataset, test_dataset = self.build_datasets(
            args.data_folder, args.train_set_ratio
        )
        dataloader_worker = args.num_workers
        self.dl = cycle_dataloader(
            DataLoader(
                train_dataset,
                batch_size=self.train_batch_size,
                shuffle=True,
                num_workers=dataloader_worker,
            )
        )
        self.eval_dl = DataLoader(
            eval_dataset,
            batch_size=self.eval_batch_size,
            shuffle=False,
            num_workers=dataloader_worker,
        )
        self.test_dl = DataLoader(
            test_dataset,
            batch_size=self.eval_batch_size,
            shuffle=False,
            num_workers=dataloader_worker,
        )

        # model
        self.model = model.to(self.device)
        self.opt = Adam(
            self.model.parameters(), lr=args.train_lr, betas=args.adam_betas
        )

        # step counter state
        self.step = 0
        self.train_num_steps = args.train_num_steps

    def get_state(self):
        state = {
            "step": self.step,
            "model": self.model.state_dict(),
            "opt": self.opt.state_dict(),
        }
        return state

    def load_state(self, state):
        self.model.load_state_dict(state["model"])
        self.step = state["step"]
        self.opt.load_state_dict(state["opt"])

    @property
    def device(self):
        return torch.device("cuda") if self.use_cuda else torch.device("cpu")

    @property
    def global_step(self) -> int:
        return self.step

    def build_datasets(self, root, train_set_ratio):
        n, d = self.args.synthetic_data_size, self.args.synthetic_data_feature_dim

        dataset_cache = Path(root) / f"{self.args.synthetic_dataset_name}_n{n}_d{d}.pt"
        if dataset_cache.exists() and not self.args.overwrite_synthetic_dataset:
            X, y = torch.load(dataset_cache)
        else:
            X, y = get_synthetic_data(self.args.synthetic_dataset_name, n, d)
            dataset_cache.parent.mkdir(parents=True, exist_ok=True)
            torch.save((X, y), dataset_cache)

        synthetic_dataset = TensorDataset(X, y)
        generator = torch.Generator().manual_seed(self.seed)
        train_size = int(train_set_ratio * len(synthetic_dataset))
        test_size = len(synthetic_dataset) - train_size
        train_dataset, test_dataset = random_split(
            synthetic_dataset, [train_size, test_size], generator
        )

        train_size = int(train_set_ratio * len(train_dataset))
        eval_size = len(train_dataset) - train_size
        train_dataset, eval_dataset = random_split(
            train_dataset, [train_size, eval_size], generator
        )

        return train_dataset, eval_dataset, test_dataset

    @staticmethod
    @torch.inference_mode()
    def eval_acc(
        model: nn.Module,
        dataloader: DataLoader,
        device: torch.DeviceObjType,
        tgt_ind: int = None,
    ):
        model.eval()

        pred_labels = []
        true_labels = []
        for data in dataloader:
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)

            outputs = model(inputs)
            _, pred = torch.max(outputs, 1)
            _, labels = torch.max(labels, 1)

            pred_labels.append(pred.numpy(force=True))
            true_labels.append(labels.numpy(force=True))

        pred_arr = np.concatenate(pred_labels)
        true_arr = np.concatenate(true_labels)
        acc_over_all = np.mean(pred_arr == true_arr).item()

        acc_over_tgt = 0.0
        if tgt_ind is not None:
            acc_over_tgt = np.mean(
                pred_arr[true_arr == tgt_ind] == true_arr[true_arr == tgt_ind]
            ).item()

        results = {
            "acc_over_all": acc_over_all,
            "acc_over_tgt": acc_over_tgt,
        }
        return results

    @torch.inference_mode()
    def eval_during_training(self):
        eval_results = self.eval_acc(
            self.model, self.eval_dl, self.device, tgt_ind=self.tgt_ind
        )
        self.model.train()
        return eval_results

    def train(self):
        self.model.train()

        with tqdm(initial=self.step, total=self.train_num_steps) as pbar:
            while self.step < self.train_num_steps:
                in_x, in_y = next(self.dl)
                in_x = in_x.to(self.device)
                in_y = in_y.to(self.device)
                logit = self.model(in_x)
                label = torch.argmax(in_y, dim=1)

                criterion = nn.CrossEntropyLoss()
                loss = criterion(logit, label)
                loss.backward()

                self.opt.step()
                self.opt.zero_grad()
                pbar.set_description(f"loss: {loss.item():.4f}")
                self.log({"loss": loss.item()}, section="num_type_cls_train")

                if self.step != 0 and divisible_by(self.step, self.save_and_eval_every):
                    log_results = self.eval_during_training()
                    self.log(log_results, section="num_type_cls_eval")
                    milestone = self.step // self.save_and_eval_every
                    self.save(milestone)

                self.step += 1
                pbar.update(1)

        log_results = self.eval_acc(
            self.model, self.test_dl, self.device, tgt_ind=self.tgt_ind
        )
        self.log(log_results, section="num_type_cls_test")
        self.save("final")
        print("synthetic classifier training complete")
