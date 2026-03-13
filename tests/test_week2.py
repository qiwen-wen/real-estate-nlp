import pandas as pd
from scripts.text_cleaning import TextCleaner
import unittest
class TestTextCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = TextCleaner()
    def test_remove_html(self):
        self.assertEqual(self.cleaner.remove_HTML("House<br>"), "House")
        self.assertEqual(self.cleaner.remove_HTML("<div>Nice</div>"), "Nice")
        self.assertEqual(self.cleaner.remove_HTML("<p class='red'>Text</p>"), "Text")
        self.assertEqual(self.cleaner.remove_HTML("No HTML here"), "No HTML here")
        self.assertEqual(self.cleaner.remove_HTML("<html><body>Deep</body></html>"), "Deep")

    def test_unicode(self):
        self.assertEqual(self.cleaner.normalize_unicode("Hello\xa0World"), "Hello World")
        self.assertEqual(self.cleaner.normalize_unicode("“Smart Quotes”"), '"Smart Quotes"')
        self.assertEqual(self.cleaner.normalize_unicode("‘Single’"), "'Single'")
        self.assertEqual(self.cleaner.normalize_unicode("Café"), "Café")

    def test_lowercasing(self):
        self.assertEqual(self.cleaner.lowercasing("ALL CAPS"), "all caps")
        self.assertEqual(self.cleaner.lowercasing("mIxEd CaSe"), "mixed case")
        self.assertEqual(self.cleaner.lowercasing(None), "")

    def test_punctuations_and_spaces(self):
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("WOW!!!"), "WOW!")
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("Must see***"), "Must see*")
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("Too   many    spaces"), "Too many spaces")
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("  Leading space"), "Leading space")
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("Trailing space  "), "Trailing space")
        self.assertEqual(self.cleaner.normalize_characters_and_punctuations("New\nLine\tTab"), "New Line Tab")

    def test_prices(self):
        self.assertEqual(self.cleaner.normalize_prices("only 450k"), "only 450000")
        self.assertEqual(self.cleaner.normalize_prices("1.2m dollars"), "1200000 dollars")
        self.assertEqual(self.cleaner.normalize_prices("2m flat"), "2000000 flat")
        self.assertEqual(self.cleaner.normalize_prices("100K uppercase"), "100000 uppercase")
        self.assertEqual(self.cleaner.normalize_prices("0.5m"), "500000")
        self.assertEqual(self.cleaner.normalize_prices("fake 450 k"), "fake 450 k")

    def test_measurements(self):
        self.assertEqual(self.cleaner.normalize_measurements("2,000 square feet"), "2000 square feet")
        self.assertEqual(self.cleaner.normalize_measurements("1,234,567 square feet"), "1234567 square feet")
        self.assertEqual(self.cleaner.normalize_measurements("500 square feet"), "500 square feet")
        self.assertEqual(self.cleaner.normalize_measurements("2,000   square feet"), "2000 square feet")
        self.assertEqual(self.cleaner.normalize_measurements("Not 2,000 apples"), "Not 2,000 apples")

    def test_abbreviations(self):
        self.assertEqual(self.cleaner.expand_abbreviations("3 br"), "3 bedroom")
        self.assertEqual(self.cleaner.expand_abbreviations("2 ba"), "2 bathroom")
        self.assertEqual(self.cleaner.expand_abbreviations("house w/ pool"), "house with pool")
        self.assertEqual(self.cleaner.expand_abbreviations("house w/o pool"), "house without pool")
        self.assertEqual(self.cleaner.expand_abbreviations("sq.ft. is large"), "square feet is large")
        self.assertEqual(self.cleaner.expand_abbreviations("1000 sf"), "1000 square feet")
        self.assertEqual(self.cleaner.expand_abbreviations("backyard"), "backyard")
        self.assertEqual(self.cleaner.expand_abbreviations("BR and BA"), "bedroom and bathroom")
        self.assertEqual(self.cleaner.expand_abbreviations("a/c unit"), "air conditioning unit")
        self.assertEqual(self.cleaner.expand_abbreviations("hwd flrs"), "hardwood flrs")

    def test_clean_text_integration(self):
        dirty_1 = "<div class='test'> Beautiful 3br 2ba w/o a/c! \xa0 Only 450k!!! </div>"
        clean_1 = "beautiful 3 bedroom 2 bathroom without air conditioning! only 450000!"
        self.assertEqual(self.cleaner.clean_text(dirty_1), clean_1)

        dirty_2 = "Huge 2,500 sq.ft. house w/ 1.2m price   tag***"
        clean_2 = "huge 2500 square feet house with 1200000 price tag*"
        self.assertEqual(self.cleaner.clean_text(dirty_2), clean_2)

        dirty_3 = "Quiet nbrhd. Close to schools."
        clean_3 = "quiet neighborhood. close to schools."
        self.assertEqual(self.cleaner.clean_text(dirty_3), clean_3)
        
        self.assertEqual(self.cleaner.clean_text(""), "")
    
    def test_price_normalization(self):
        self.assertIn('450000', self.cleaner.normalize_prices('priced at 450k'))
        self.assertIn('1200000', self.cleaner.normalize_prices('$1.2m home'))

    def test_profiling(self):
        mock_data = {'remarks': ['Nice house', None, 'Beautiful 3br 2ba']}
        df = pd.DataFrame(mock_data)
        profile = self.cleaner.profile_column(df, 'remarks')
        self.assertIn('null_rate', profile)
        self.assertIn('avg_length', profile)
    
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)