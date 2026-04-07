'''Evaluation helpers for span-level entity extraction results stored in JSONL files.'''

import json


def load_jsonl(path):
    '''Yield one parsed JSON object per line from a JSONL file.'''
    with open(path, 'r', encoding='utf-8') as file_obj:
        for line in file_obj:
            yield json.loads(line)


def to_set(entities):
    '''Convert entity dicts into hashable tuples for set comparison.'''
    return {(entity['start'], entity['end'], entity['label']) for entity in entities}


def evaluate(gold_path, pred_path):
    '''Compute precision, recall, and F1 based on exact span/label matches.'''
    tp = fp = fn = 0
    for gold_item, pred_item in zip(load_jsonl(gold_path), load_jsonl(pred_path)):
        gold_set = to_set(gold_item['entities'])
        pred_set = to_set(pred_item['entities'])
        tp += len(gold_set & pred_set)
        fp += len(pred_set - gold_set)
        fn += len(gold_set - pred_set)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return precision, recall, f1


if __name__ == '__main__':
    '''Run standalone evaluation against the default processed JSONL files.'''
    precision, recall, f1 = evaluate(
        'data/processed/data_template.jsonl',
        'data/processed/data_prediction.jsonl'
    )
    print(f'Precision={precision:.3f} Recall={recall:.3f} F1={f1:.3f}')
