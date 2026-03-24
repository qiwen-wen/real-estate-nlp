'''Prediction runner that applies the entity extractor and evaluates results.'''

import json

try:
    from scripts.data_extractor.entity_extractor import EntityExtractor
    from scripts.data_extractor.evaluate_entity import evaluate
except ModuleNotFoundError:
    from entity_extractor import EntityExtractor
    from evaluate_entity import evaluate


def generate_predictions(template_path, prediction_path):
    '''Read template JSONL, extract entity spans, and write prediction JSONL.'''
    extractor = EntityExtractor()

    with open(template_path, 'r', encoding='utf-8') as source, open(
        prediction_path,
        'w',
        encoding='utf-8'
    ) as target:
        for line in source:
            data = json.loads(line)
            text = data['text']
            predicted_spans = extractor.extract_spans(text)

            prediction_record = {
                'id': data['id'],
                'text': text,
                'entities': predicted_spans
            }
            target.write(json.dumps(prediction_record) + '\n')


def main():
    '''Run end-to-end extraction and print evaluation metrics for default files.'''
    template_file = 'data/processed/data_template.jsonl'
    prediction_file = 'data/processed/data_prediction.jsonl'

    print('starting...')
    generate_predictions(template_file, prediction_file)
    print('stored data into:', prediction_file)

    print('\n--- start calculation ---')
    precision, recall, f1 = evaluate(template_file, prediction_file)
    print(f'Precision = {precision:.3f}')
    print(f'Recall    = {recall:.3f}')
    print(f'F1 Score  = {f1:.3f}')


if __name__ == '__main__':
    '''Execute the default extraction pipeline when run as a script.'''
    main()
