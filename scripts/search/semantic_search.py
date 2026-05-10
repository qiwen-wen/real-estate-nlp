import os
import faiss
import numpy as np
import json 
from sentence_transformers import SentenceTransformer

class SemanticSearcher:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # 1. SETUP MODEL PATH
        # Navigate from scripts/search/ up to root, then to data/models/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_path = os.path.join(base_dir, 'data', 'models', model_name)
        
        # 2. LOAD OR DOWNLOAD MODEL
        if os.path.exists(model_path):
            print(f"Loading Semantic Model from local storage: {model_name}")
            self.model = SentenceTransformer(model_path)
        else:
            print(f"Downloading {model_name} for the first time...")
            self.model = SentenceTransformer(model_name)
            # Save it so we don't have to download it again
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.model.save(model_path)
            print(f"Model saved to {model_path}")

        self.index = None
        self.listings = None

    def build_index(self, remarks_list):
        if not remarks_list:
            print("Warning: remarks_list is empty. Cannot build index.")
            return

        print(f"Encoding {len(remarks_list)} listings into vectors...")
        
        # Convert text strings into numerical vectors (embeddings)
        embeddings = self.model.encode(remarks_list, show_progress_bar=True)
        embeddings = embeddings.astype('float32')

        # Get dimensions (384 for MiniLM)
        dim = embeddings.shape[1]
        
        # Create a FAISS index using Inner Product (Cosine Similarity)
        self.index = faiss.IndexFlatIP(dim)
        
        # Normalize vectors so that Inner Product = Cosine Similarity
        faiss.normalize_L2(embeddings)
        
        # Add to searchable index
        self.index.add(embeddings)
        self.listings = remarks_list
        print("FAISS Index building complete.")

    def search(self, query, top_k=5):
        if self.index is None:
            return [("Error: Index not built.", 0.0)]

        # 1. Encode and Normalize query
        query_emb = self.model.encode([query]).astype('float32')
        faiss.normalize_L2(query_emb)
        
        # 2. Search FAISS index
        scores, indices = self.index.search(query_emb, top_k)
        
        # 3. Map indices back to original text
        # Filter out invalid indices (-1 is FAISS code for "not found")
        results = []
        for j, i in enumerate(indices[0]):
            if i != -1 and i < len(self.listings):
                results.append((self.listings[i], scores[0][j]))
        
        return results
    
    def save_index(self, index_path, listings_path):
        """Persist the FAISS index and listings to disk."""
        if self.index is None:
            raise RuntimeError("Cannot save: index has not been built yet.")
        
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.index, index_path)
        
        with open(listings_path, 'w', encoding='utf-8') as f:
            json.dump(self.listings, f)
        print(f"Saved index to {index_path} and listings to {listings_path}")

    def load_index(self, index_path, listings_path):
        """Load a previously-saved FAISS index and listings from disk."""
        if not os.path.exists(index_path) or not os.path.exists(listings_path):
            raise FileNotFoundError(
                f"Index artifacts not found. Run pipelines/build_search_index.py first."
            )
        
        self.index = faiss.read_index(index_path)
        with open(listings_path, 'r', encoding='utf-8') as f:
            self.listings = json.load(f)
        print(f"Loaded index with {len(self.listings)} listings from {index_path}")