"""
PDF Knowledge Base - Extracts and searches command knowledge from Ubuntu Linux Toolbox PDF
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2

class PDFKnowledgeBase:
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.cache_path = self.pdf_path.with_suffix('.cache.json')
        self.content = []
        self.load_or_extract()
    
    def load_or_extract(self):
        """Load from cache or extract from PDF"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    self.content = json.load(f)
                print(f"✅ Loaded {len(self.content)} pages from cache")
                return
            except Exception as e:
                print(f"⚠️  Cache load failed: {e}")
        
        # Extract from PDF
        self.extract_from_pdf()
    
    def extract_from_pdf(self):
        """Extract text content from PDF"""
        try:
            print(f"📖 Extracting content from {self.pdf_path.name}...")
            with open(self.pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        self.content.append({
                            'page': i + 1,
                            'text': text
                        })
                    
                    if (i + 1) % 50 == 0:
                        print(f"  Processed {i + 1}/{total_pages} pages...")
            
            # Save cache
            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.content, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Extracted {len(self.content)} pages and saved cache")
        
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            self.content = []
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search for relevant content in the PDF"""
        query_lower = query.lower()
        results = []
        
        for page_data in self.content:
            text = page_data['text']
            text_lower = text.lower()
            
            # Simple relevance scoring
            score = 0
            for word in query_lower.split():
                if len(word) > 2:  # Skip very short words
                    score += text_lower.count(word)
            
            if score > 0:
                results.append({
                    'page': page_data['page'],
                    'text': text,
                    'score': score
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def get_context(self, query: str) -> str:
        """Get relevant context for a query"""
        results = self.search(query, max_results=2)  # Reduced from 3 to 2
        
        if not results:
            return ""  # Return empty instead of message to save tokens
        
        context = "Reference from Ubuntu Linux Toolbox:\n\n"
        for i, result in enumerate(results, 1):
            # Limit text length to 400 chars per page (reduced from 1000)
            text = result['text'][:400]
            context += f"{text}\n\n"
        
        return context
