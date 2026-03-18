import json

def load_jsonl(path):
    with open(path, "r") as f:
        for line in f:
            yield json.loads(line)

def to_set(entities):
    return {(e["start"], e["end"], e["label"]) for e in entities}

def evaluate(gold_path, pred_path):
    tp = fp = fn = 0
    for g, p in zip(load_jsonl(gold_path), load_jsonl(pred_path)):
        g_set = to_set(g["entities"])
        p_set = to_set(p["entities"])
        tp += len(g_set & p_set)
        fp += len(p_set - g_set)
        fn += len(g_set - p_set)

    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return precision, recall, f1

if __name__ == "__main__":
    p, r, f1 = evaluate("data/processed/data_template.json", "data/processed/data_prediction.json")
    print(f"Precision={p:.3f} Recall={r:.3f} F1={f1:.3f}")
