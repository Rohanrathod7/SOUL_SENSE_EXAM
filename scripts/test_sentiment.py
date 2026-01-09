from journal_feature import JournalFeature
from tkinter import Tk
import nltk

print("Testing NLTK Sentiment Analysis...")
try:
    root = Tk()
    root.withdraw() # Hide root
    journal = JournalFeature(root)

    test_cases = [
        "I am happy", 
        "I am NOT happy", 
        "I am devastatingly sad", 
        "I feel meh but okay"
    ]

    for text in test_cases:
        score = journal.analyze_sentiment(text)
        print(f"Text: '{text}' -> Score: {score}")
        
    print("✅ Test Complete.")
except Exception as e:
    print(f"❌ Test Failed: {e}")
