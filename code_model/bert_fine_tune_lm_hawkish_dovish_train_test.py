import os
import sys
from time import time, sleep
import pandas as pd
from transformers import BertForSequenceClassification, BertTokenizerFast, RobertaTokenizerFast, RobertaForSequenceClassification, AutoTokenizer, AutoModelForSequenceClassification, XLNetForSequenceClassification, XLNetTokenizerFast
from transformers import XLMRobertaTokenizerFast, XLMRobertaForSequenceClassification, AutoModelForMaskedLM
import torch
from torch.utils.data import TensorDataset, DataLoader
import torch.optim as optim
from sklearn.metrics import f1_score
import numpy as np

sys.path.append('..')

def train_lm_hawkish_dovish(gpu_numbers: str, train_data_path: str, test_data_path: str, language_model_to_use: str, seed: int, batch_size: int, learning_rate: float, save_model_path: str):
    """
    Description: Run experiment over particular batch size, learning rate and seed
    """
    # set gpu
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_numbers)
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print("Device assigned: ", device)

    # load training data
    data_df = pd.read_excel(train_data_path)
    sentences = data_df['sentence'].to_list()
    labels = data_df['label'].to_numpy()

    # load test data
    data_df_test = pd.read_excel(test_data_path)
    sentences_test = data_df_test['sentence'].to_list()
    labels_test = data_df_test['label'].to_numpy()

    # load tokenizer
    try:
        if language_model_to_use == 'bert':
            tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'roberta':
            tokenizer = RobertaTokenizerFast.from_pretrained('roberta-base', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'flangroberta':
            tokenizer = AutoTokenizer.from_pretrained('SALT-NLP/FLANG-Roberta', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'finbert':
            tokenizer = BertTokenizerFast(vocab_file='../finbert-uncased/FinVocab-Uncased.txt', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'flangbert':
            tokenizer = BertTokenizerFast.from_pretrained('SALT-NLP/FLANG-BERT', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'bert-large':
            tokenizer = BertTokenizerFast.from_pretrained('bert-large-uncased', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'roberta-large':
            tokenizer = RobertaTokenizerFast.from_pretrained('roberta-large', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'pretrain_roberta':
            tokenizer = AutoTokenizer.from_pretrained("../pretrained_roberta_output", do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'xlnet':
            tokenizer = XLNetTokenizerFast.from_pretrained("xlnet-base-cased", do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'xlm-roberta-base':
            tokenizer = XLMRobertaTokenizerFast.from_pretrained("xlm-roberta-base", do_lower_case=True,
                                                                do_basic_tokenize=True)
        elif language_model_to_use == 'xlm-roberta-large':
            tokenizer = XLMRobertaTokenizerFast.from_pretrained("xlm-roberta-large", do_lower_case=True,
                                                                do_basic_tokenize=True)
        else:
            return -1
    except Exception as e:
        print(e)
        sleep(600)
        if language_model_to_use == 'bert':
            tokenizer = BertTokenizerFast.from_pretrained('bert-base-uncased', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'roberta':
            tokenizer = RobertaTokenizerFast.from_pretrained('roberta-base', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'flangroberta':
            tokenizer = AutoTokenizer.from_pretrained('SALT-NLP/FLANG-Roberta', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'finbert':
            tokenizer = BertTokenizerFast(vocab_file='../finbert-uncased/FinVocab-Uncased.txt', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'flangbert':
            tokenizer = BertTokenizerFast.from_pretrained('SALT-NLP/FLANG-BERT', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'bert-large':
            tokenizer = BertTokenizerFast.from_pretrained('bert-large-uncased', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'roberta-large':
            tokenizer = RobertaTokenizerFast.from_pretrained('roberta-large', do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'pretrain_roberta':
            tokenizer = AutoTokenizer.from_pretrained("../pretrained_roberta_output", do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'xlnet':
            tokenizer = XLNetTokenizerFast.from_pretrained("xlnet-base-cased", do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'xlm-roberta-base':
            tokenizer = XLMRobertaTokenizerFast.from_pretrained("xlm-roberta-base", do_lower_case=True, do_basic_tokenize=True)
        elif language_model_to_use == 'xlm-roberta-large':
            tokenizer = XLMRobertaTokenizerFast.from_pretrained("xlm-roberta-large", do_lower_case=True, do_basic_tokenize=True)
        else:
            return -1

    max_length = 0
    sentence_input = []
    labels_output = []
    for i, sentence in enumerate(sentences):
        if isinstance(sentence, str):
            tokens = tokenizer(sentence)['input_ids']
            sentence_input.append(sentence)
            max_length = max(max_length, len(tokens))
            labels_output.append(labels[i])
        else:
            pass
    max_length=256
    if language_model_to_use == 'flangroberta':
        max_length=128
    tokens = tokenizer(sentence_input, return_tensors='pt', padding=True, truncation=True, max_length=max_length)
    labels = np.array(labels_output)

    input_ids = tokens['input_ids']
    attention_masks = tokens['attention_mask']
    labels = torch.LongTensor(labels)
    dataset = TensorDataset(input_ids, attention_masks, labels)
    val_length = int(len(dataset) * 0.2)
    train_length = len(dataset) - val_length
    print(f'Train Size: {train_length}, Validation Size: {val_length}')
    experiment_results = []
    
    # assign seed to numpy and PyTorch
    torch.manual_seed(seed)
    np.random.seed(seed) 

    # select language model
    try: 
        if language_model_to_use == 'bert':
            model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3).to(device)
        elif language_model_to_use == 'roberta':
            model = RobertaForSequenceClassification.from_pretrained('roberta-base', num_labels=3).to(device)
        elif language_model_to_use == 'flangroberta':
            model = AutoModelForSequenceClassification.from_pretrained('SALT-NLP/FLANG-Roberta', num_labels=3).to(device)
        elif language_model_to_use == 'finbert':
            model = BertForSequenceClassification.from_pretrained('../finbert-uncased/model', num_labels=3).to(device)
        elif language_model_to_use == 'flangbert':
            model = BertForSequenceClassification.from_pretrained('SALT-NLP/FLANG-BERT', num_labels=3).to(device)
        elif language_model_to_use == 'bert-large':
            model = BertForSequenceClassification.from_pretrained('bert-large-uncased', num_labels=3).to(device)
        elif language_model_to_use == 'roberta-large':
            model = RobertaForSequenceClassification.from_pretrained('roberta-large', num_labels=3).to(device)
        elif language_model_to_use == 'pretrain_roberta':
            model = AutoModelForSequenceClassification.from_pretrained("../pretrained_roberta_output", num_labels=3).to(device)
        elif language_model_to_use == 'xlnet':
            model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased", num_labels=3).to(device)
        elif language_model_to_use == 'xlm-roberta-base':
            model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-base", num_labels=3).to(device)
        elif language_model_to_use == 'xlm-roberta-large':
            model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-large", num_labels=3).to(device)
        else:
            return -1
    except:
        sleep(600)
        if language_model_to_use == 'bert':
            model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3).to(device)
        elif language_model_to_use == 'roberta':
            model = RobertaForSequenceClassification.from_pretrained('roberta-base', num_labels=3).to(device)
        elif language_model_to_use == 'flangroberta':
            model = AutoModelForSequenceClassification.from_pretrained('SALT-NLP/FLANG-Roberta', num_labels=3).to(device)
        elif language_model_to_use == 'finbert':
            model = BertForSequenceClassification.from_pretrained('../finbert-uncased/model', num_labels=3).to(device)
        elif language_model_to_use == 'flangbert':
            model = BertForSequenceClassification.from_pretrained('SALT-NLP/FLANG-BERT', num_labels=3).to(device)
        elif language_model_to_use == 'bert-large':
            model = BertForSequenceClassification.from_pretrained('bert-large-uncased', num_labels=3).to(device)
        elif language_model_to_use == 'roberta-large':
            model = RobertaForSequenceClassification.from_pretrained('roberta-large', num_labels=3).to(device)
        elif language_model_to_use == 'pretrain_roberta':
            model = AutoModelForSequenceClassification.from_pretrained("../pretrained_roberta_output", num_labels=3).to(device)
        elif language_model_to_use == 'xlnet':
            model = XLNetForSequenceClassification.from_pretrained("xlnet-base-cased", num_labels=3).to(device)
        elif language_model_to_use == 'xlm-roberta-base':
            model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-base", num_labels=3).to(device)
        elif language_model_to_use == 'xlm-roberta-large':
            model = XLMRobertaForSequenceClassification.from_pretrained("xlm-roberta-large", num_labels=3).to(device)
        else:
            return -1

    # create train-val split
    train, val = torch.utils.data.random_split(dataset=dataset, lengths=[train_length, val_length])
    dataloaders_dict = {'train': DataLoader(train, batch_size=batch_size, shuffle=True), 'val': DataLoader(val, batch_size=batch_size, shuffle=True)}
    print(train_length, val_length)
    # select optimizer
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate)
    max_num_epochs = 100
    max_early_stopping = 7
    early_stopping_count = 0
    best_ce = float('inf')
    best_accuracy = float('-inf')
    best_f1 = float('-inf')

    eps = 1e-2

    epoch_result_train = []
    epoch_result_val = []
    epoch_result = []

    print("max num epochs:%d" % max_num_epochs)

    for epoch in range(max_num_epochs):
        print("epoch(%d)" % epoch)
        if (early_stopping_count >= max_early_stopping):
            break
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
                early_stopping_count += 1
            else:
                model.eval()
            
            curr_ce = 0
            curr_accuracy = 0
            curr_ce_train = 0
            curr_accuracy_train = 0
            actual = torch.tensor([]).long().to(device)
            pred = torch.tensor([]).long().to(device)
            actual_train = torch.tensor([]).long().to(device)
            pred_train = torch.tensor([]).long().to(device)

            for input_ids, attention_masks, labels in dataloaders_dict[phase]:
                input_ids = input_ids.to(device)
                attention_masks = attention_masks.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(input_ids = input_ids, attention_mask = attention_masks, labels=labels)
                    loss = outputs.loss
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                        curr_ce_train += loss.item() * input_ids.size(0)
                        curr_accuracy_train += torch.sum(torch.max(outputs.logits, 1)[1] == labels).item()
                        actual_train = torch.cat([actual_train, labels], dim=0)
                        pred_train = torch.cat([pred_train, torch.max(outputs.logits, 1)[1]], dim=0)
                    else:
                        curr_ce += loss.item() * input_ids.size(0)
                        curr_accuracy += torch.sum(torch.max(outputs.logits, 1)[1] == labels).item()
                        actual = torch.cat([actual, labels], dim=0)
                        pred= torch.cat([pred, torch.max(outputs.logits, 1)[1]], dim=0)
            if phase== 'train':
                curr_ce_train = curr_ce_train / len(train)
                curr_accuracy_train = curr_accuracy_train / len(train)
                currF1_train = f1_score(actual_train.cpu().detach().numpy(), pred_train.cpu().detach().numpy(), average='weighted')
                epoch_result_train.append([curr_ce_train, curr_accuracy_train, currF1_train])

            if phase == 'val':
                curr_ce = curr_ce / len(val)
                curr_accuracy = curr_accuracy / len(val)
                currF1 = f1_score(actual.cpu().detach().numpy(), pred.cpu().detach().numpy(), average='weighted')
                epoch_result_val.append([curr_ce, curr_accuracy, currF1])
                if curr_ce <= best_ce - eps:
                    best_ce = curr_ce
                    early_stopping_count = 0
                if curr_accuracy >= best_accuracy + eps:
                    best_accuracy = curr_accuracy
                    early_stopping_count = 0
                if currF1 >= best_f1 + eps:
                    best_f1 = currF1
                    early_stopping_count = 0
                print("Val CE: ", curr_ce)
                print("Val Accuracy: ", curr_accuracy)
                print("Val F1: ", currF1)
                print("Early Stopping Count: ", early_stopping_count)
    
    ## ------------------testing---------------------
    sentence_input_test = []
    labels_output_test = []
    for i, sentence in enumerate(sentences_test):
        if isinstance(sentence, str):
            tokens = tokenizer(sentence)['input_ids']
            sentence_input_test.append(sentence)
            labels_output_test.append(labels_test[i])
        else:
            pass

    tokens_test = tokenizer(sentence_input_test, return_tensors='pt', padding=True, truncation=True, max_length=max_length)
    labels_test = np.array(labels_output_test)

    input_ids_test = tokens_test['input_ids']
    attention_masks_test = tokens_test['attention_mask']
    labels_test = torch.LongTensor(labels_test)
    dataset_test = TensorDataset(input_ids_test, attention_masks_test, labels_test)

    dataloaders_dict_test = {'test': DataLoader(dataset_test, batch_size=batch_size, shuffle=True)}
    test_ce = 0
    test_accuracy = 0
    actual = torch.tensor([]).long().to(device)
    pred = torch.tensor([]).long().to(device)
    for input_ids, attention_masks, labels in dataloaders_dict_test['test']:
        input_ids = input_ids.to(device)
        attention_masks = attention_masks.to(device)
        labels = labels.to(device)   
        optimizer.zero_grad()   
        with torch.no_grad():
            outputs = model(input_ids = input_ids, attention_mask = attention_masks, labels=labels)
            loss = outputs.loss
            test_ce += loss.item() * input_ids.size(0)
            test_accuracy += torch.sum(torch.max(outputs.logits, 1)[1] == labels).item()
            actual = torch.cat([actual, labels], dim=0)
            pred = torch.cat([pred, torch.max(outputs.logits, 1)[1]], dim=0)
    test_ce = test_ce / len(dataset_test)
    test_accuracy = test_accuracy/ len(dataset_test)
    test_f1 = f1_score(actual.cpu().detach().numpy(), pred.cpu().detach().numpy(), average='weighted')
    experiment_results = [seed, learning_rate, batch_size, best_ce, best_accuracy, best_f1, test_ce, test_accuracy, test_f1]
    for train, valid in zip(epoch_result_train, epoch_result_val):
        combined_result = train + valid
        epoch_result.append(combined_result)

    df_epoch_results = pd.DataFrame(epoch_result, columns=['Loss_train', 'Accuracy_train', 'F1_train', 'Loss_valid', 'Accuracy_valid', 'F1_valid'])

    # save model
    if save_model_path != None:
        save_path = save_model_path + language_model_to_use + data_category + '-' + str(seed) + '-' + str(learning_rate) + '-' + str(batch_size)
        model.save_pretrained(save_path)
        tokenizer.save_pretrained(save_path)
        df_epoch_results.to_excel(save_path + "/epoch_results.xlsx", index=True)

    return experiment_results


def train_lm_price_change_experiments(gpu_numbers: str, train_data_path_prefix: str, test_data_path_prefix: str, language_model_to_use: str, data_category: str):
    """
    Description: Run experiments over different batch sizes, learning rates and seeds to find best hyperparameters
    """
    results = []
    seeds = [5768, 78516, 944601]
    batch_sizes = [32, 16, 8, 4]
    learning_rates = [1e-4, 1e-5, 1e-6, 1e-7]
    count = 0
    save_model_path = "../model_data/final_model"
    checkpoint_save_path = "../model_data/checkpoint"
    import json
    if os.path.exists(checkpoint_save_path):
        last_saved_data = json.load(open(checkpoint_save_path))
        print("Loading from checkpoint successfully, seeds: %d, batch_size: %d, learning_rate: %f" % (seeds[last_saved_data["seed"]],
                                                                                                      batch_sizes[last_saved_data["batch_size"]],
                                                                                                      learning_rates[last_saved_data["learning_rate"]]))
    else:
        last_saved_data = {"seed": 0, "batch_size": 0, "learning_rate": 0}
        print("No checkpoint found, start from the beginning.")

    print("Start Training, Language Model:%s, Data Category:%s" % (language_model_to_use, data_category))
    i = last_saved_data["seed"]
    j = last_saved_data["batch_size"]
    k = last_saved_data["learning_rate"]

    while i < len(seeds):
        while j < len(batch_sizes):
            while k < len(learning_rates):

                seed = seeds[i]
                batch_size = batch_sizes[j]
                learning_rate = learning_rates[k]
                count += 1
                print(f'Experiment {count} of {len(seeds) * len(batch_sizes) * len(learning_rates)}:')
                print("Seed: %d, Batch Size: %d, Learning Rate: %f" % (seed, batch_size, learning_rate))
                
                train_data_path = train_data_path_prefix + "-" + str(seed) + ".xlsx"
                test_data_path = test_data_path_prefix + "-" + str(seed) + ".xlsx"

                save_path = save_model_path + language_model_to_use + data_category + '-' + str(seed) + '-' + str(learning_rate) + '-' + str(batch_size)
                print(save_path)
                results.append(train_lm_hawkish_dovish(gpu_numbers, train_data_path, test_data_path, language_model_to_use, seed, batch_size, learning_rate, save_model_path))
                df = pd.DataFrame(results, columns=["Seed", "Learning Rate", "Batch Size", "Val Cross Entropy", "Val Accuracy", "Val F1 Score", "Test Cross Entropy", "Test Accuracy", "Test F1 Score"])
                if os.path.exists("../grid_search_results_repro") == False:
                    os.mkdir("../grid_search_results_repro")
                df.to_excel(f'../grid_search_results_repro/final_{data_category}_{language_model_to_use}.xlsx',
                            index=False)

                last_saved_data["seed"] = i
                last_saved_data["batch_size"] = j
                last_saved_data["learning_rate"] = k

                # write to file
                with open(checkpoint_save_path, 'w') as outfile:
                    json.dump(last_saved_data, outfile, indent=4)

                print("Save Checkpoint:[%d, %d, %f] successfully." % (seed, batch_size, learning_rate))
                k += 1
            j += 1
            k = 0
        i += 1
        j = 0
        k = 0


if __name__=='__main__':
    save_model_path = "../model_data/final_model"
    start_t = time()

    # experiments
    for language_model_to_use in ["roberta", "roberta-large", "bert", "bert-large", "finbert", "flangbert", "flangroberta", "xlnet", "xlm-roberta-base"]: #["xlnet", "pretrain_roberta"]:#
        for data_category in ["lab-manual-combine", "lab-manual-sp", "lab-manual-mm", "lab-manual-pc", "lab-manual-mm-split", "lab-manual-pc-split", "lab-manual-sp-split", "lab-manual-split-combine"]:
            train_data_path_prefix = "../training_data/test-and-training/training_data/" + data_category + "-train"
            test_data_path_prefix = "../training_data/test-and-training/test_data/" + data_category + "-test"
            train_lm_price_change_experiments(gpu_numbers="0", train_data_path_prefix=train_data_path_prefix, test_data_path_prefix=test_data_path_prefix, language_model_to_use=language_model_to_use, data_category=data_category)
    

    '''
    # save model
    seed = 944601
    language_model_to_use = "roberta-large"
    train_data_path = "../training_data/test-and-training/training_data/lab-manual-split-combine-train" + "-" + str(seed) + ".xlsx"
    test_data_path = "../training_data/test-and-training/test_data/lab-manual-split-combine-test" + "-" + str(seed) + ".xlsx"
    output = train_lm_hawkish_dovish(gpu_numbers="0", train_data_path=train_data_path, test_data_path=test_data_path, 
    language_model_to_use=language_model_to_use, seed=944601, batch_size=4, learning_rate=1e-6, save_model_path=save_model_path)
    print(output)
    '''
    
    print((time() - start_t)/60.0)