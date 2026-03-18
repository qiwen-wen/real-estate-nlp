import json

from scripts.entity_extractor import EntityExtractor 

def generate_predictions(template_path, prediction_path):
    extractor = EntityExtractor()
    
    with open(template_path, 'r', encoding='utf-8') as fin, \
         open(prediction_path, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            data = json.loads(line)
            text = data["text"]
            
            predicted_spans = extractor.extract_spans(text)

            prediction_record = {
                "id": data["id"],
                "text": text,
                "entities": predicted_spans
            }
            
            fout.write(json.dumps(prediction_record) + '\n')

if __name__ == "__main__":
    template_file = "data/processed/data_template.jsonl"
    prediction_file = "data/processed/data_prediction.jsonl"
    
    print("starting...")
    generate_predictions(template_file, prediction_file)
    print("stored data into：", prediction_file)
    
    print("\n--- start caculation ---")
    from scripts.evaluate_entity import evaluate
    p, r, f1 = evaluate(template_file, prediction_file)
    print(f"Precision = {p:.3f}")
    print(f"Recall    = {r:.3f}")
    print(f"F1 Score  = {f1:.3f}")