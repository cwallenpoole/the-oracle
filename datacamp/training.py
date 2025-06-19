import torch
from trl import SFTTrainer
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments

from textwrap import textwrap
from tabulate import tabulate

train_dataset = load_dataset("tatsu-lab/alpaca", split="train")
print(train_dataset)

pandas_format = train_dataset.to_pandas()
# print(tabulate(pandas_format, headers = 'keys', tablefmt = 'psql'))

# print(pandas_format.head())

for index in range(3):
   print("---"*15)
   print("Instruction:\n{}".format(textwrap.fill(pandas_format.iloc[index]["instruction"],    
       width=50)))
   print("Output:  \n       {}".format(textwrap.fill(pandas_format.iloc[index]["output"],  
       width=50)))
   print("Text: \n       {}".format(textwrap.fill(pandas_format.iloc[index]["text"],  
       width=50)))
