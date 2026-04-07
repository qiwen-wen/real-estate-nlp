from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class SemanticSearcher:
    def __init__(self):
        # Loading a light-weight transformer model (384 dimensions)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.listings = None

    def build_index(self, remarks_list):
        print(f"Encoding {len(remarks_list)} listings...")
        
        # Convert text strings into numerical vectors (embeddings)
        embeddings = self.model.encode(remarks_list)
        
        # Convert to float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')

        # Get the number of dimensions (should be 384 for this model)
        dim = embeddings.shape[1]
        
        # Create a FAISS index using Inner Product (IP)
        # When vectors are normalized, IP is equivalent to Cosine Similarity
        self.index = faiss.IndexFlatIP(dim)
        
        # Normalize vectors to unit length
        faiss.normalize_L2(embeddings)
        
        # Add the vectors to the searchable index
        self.index.add(embeddings)
        self.listings = remarks_list
        print("Index building complete.")

    def search(self, query, top_k=10):
        # 1. Encode the user query into a vector
        query_emb = self.model.encode([query]).astype('float32')
        
        # 2. Normalize the query vector
        faiss.normalize_L2(query_emb)
        
        # 3. Search the index for the 'top_k' most similar vectors
        # scores = similarity values, indices = the position in the original list
        scores, indices = self.index.search(query_emb, top_k)
        
        # 4. Map the indices back to the original text and return with scores
        results = [(self.listings[i], scores[0][j]) for j, i in enumerate(indices[0])]
        
        return results

# Example Usage:
# searcher = SemanticSearcher()
# searcher.build_index(["Cozy 2-bedroom apartment in SD", "Luxury villa with pool", "Studio near UCSD"])
# results = searcher.search("places for students near campus")
# print(results)