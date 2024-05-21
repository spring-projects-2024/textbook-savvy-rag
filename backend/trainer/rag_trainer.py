from torch.optim import AdamW
from torch.utils.data import DataLoader

from backend.benchmark.utils import load_yahoo_answers, load_mmlu
from jepa.trainer.trainer import Trainer
from backend.model.rag_handler import RagHandler
import torch
from torch import nn
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    get_linear_schedule_with_warmup,
    BatchEncoding,
)
from peft import LoraConfig, TaskType, get_peft_model
from peft.utils import prepare_model_for_kbit_training


# class RagCriterionOld(nn.Module):
#     """
#     For use with forward_single_query_multiple_docs and compute_probabilities_for_training.
#     """

#     def __init__(self):
#         super().__init__()
#         self.cross_entropy_from_log_proba = nn.NLLLoss(reduction="mean")

#     def forward(self, output: dict, batch: dict) -> dict:
#         """
#         :param output: dict with keys "probas", "answer_mask"
#         :param batch: dict with keys "answer_tokens"
#         """
#         probas = output["probas"]
#         log_probas = torch.log(probas)
#         target = batch["answer_tokens"]
#         loss = self.cross_entropy_from_log_proba(log_probas, target)  # TODO: check
#         return {"loss": loss}


class RagCriterion(nn.Module):
    def __init__(self):
        super().__init__()
        self.cross_entropy = nn.CrossEntropyLoss(reduction="mean")

    def forward(self, output: dict, batch: dict) -> dict:
        """
        :param output: dict with keys "logits", "answer_lengths"
        :param batch: dict with keys "targets"
        """
        logits = output["logits"]  # (batch_size, max_len, vocab_size)
        targets = batch["targets"]  # list of tensors of different lengths
        answer_lengths = output["answer_lengths"]  # (batch_size,)
        loss = 0
        for logits_one_query, answer_length, answer_tokens in zip(
            logits, answer_lengths, targets["input_ids"]
        ):
            assert (
                len(answer_tokens) == answer_length
            ), f"{len(answer_tokens)}  {answer_length}"
            loss += self.cross_entropy(
                logits_one_query[-answer_length - 1 : -1, :], answer_tokens
            )
        loss /= len(answer_lengths)
        return {"loss": loss}


class RagTrainer(Trainer):
    def __init__(self, model: RagHandler, **kwargs):
        super().__init__(model, **kwargs)
        # torch.compile(model.llm.model)  # artigianale. commentalo per spegnerlo

    def train_step(self, batch: dict) -> dict:
        answers = batch["answer"]
        tokenized_answers: BatchEncoding = self.model.llm.tokenizer(
            answers, padding=False, return_tensors="pt"
        )  # BatchEncoding object

        token_answ = {
            "input_ids": tokenized_answers["input_ids"],
            "attention_mask": tokenized_answers["attention_mask"],
        }

        batch["targets"] = token_answ

        return super().train_step(batch)


def prepare_for_qlora(model: AutoModelForCausalLM) -> AutoModelForCausalLM:
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=8,
        target_modules=[
            "q_proj",
            "o_proj",
            "k_proj",
            "v_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        lora_alpha=16,
        lora_dropout=0.1,
    )
    model = get_peft_model(model, lora_config)
    return model


if __name__ == "__main__":
    print(torch.cuda.is_available())

    rag_handler = RagHandler(
        model_name="Minami-su/Qwen1.5-0.5B-Chat_llamafy",
        device="cpu",
        use_qlora=False,
        llm_generation_config=None,
        llm_kwargs=None,
        # tokenizer_kwargs=tokenizer_kwargs,
        # faiss_kwargs=faiss_kwargs,
    )

    batch_size = 1

    train_data = load_yahoo_answers(subset="stem")
    train_loader = DataLoader(train_data, batch_size=batch_size)
    test_data = load_mmlu(split="validation", subset="stem")
    test_loader = DataLoader(test_data, batch_size=batch_size)
    train_metadata = {
        "id": "yahoo_answers",
        "use_as": "train",
        "num_samples": len(train_data),
    }

    optimizer = AdamW(rag_handler.llm.model.parameters())
    criterion = RagCriterion()
    num_training_steps = 20_000  # todo: change
    num_warmup_steps = int(0.1 * num_training_steps)
    scheduler = get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps,
    )

    train_config = {
        "model": rag_handler,
        "optimizer": optimizer,
        "criterion": criterion,
        "train_loader": train_loader,
        "train_metadata": train_metadata,
        "test_loader": test_loader,
        "max_epochs": 1,
        "device": "cpu",
        "scheduler": scheduler,
        "log_to_wandb": False,
        "log_interval": 1,
        "checkpoint_interval": 1,
        "checkpoint_root_dir": "../checkpoints",
        "seed": 42,
        "wandb_project": "ajdoasjda",
        "compile_model": False,
    }

    print("Training...")

    rag_trainer = RagTrainer(**train_config)
    rag_trainer.train()
