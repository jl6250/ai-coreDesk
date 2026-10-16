import json
import os
import time
from typing import List, Dict, Any

class RAGEngine:
    """
    RAG 知识库多语言检索融合模块
    支持 zh, en, vi, th 四种语言的内容召回
    """
    def __init__(self, data_path: str = None):
        if not data_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "faq_knowledge.json")
        self.data_path = data_path
        self.knowledge_base: List[Dict[str, Any]] = []
        self._load_knowledge()

    def _load_knowledge(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r", encoding="utf-8") as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = []

    def retrieve_context(self, query: str, top_k: int = 2, lang: str = "zh") -> Dict[str, Any]:
        start = time.perf_counter()
        query_lower = query.lower()
        scored_items = []

        for item in self.knowledge_base:
            score = 0
            # 关键词命中
            for kw in item.get("keywords", []):
                if kw in query_lower:
                    score += 3
            # 标题命中
            if query_lower in item.get("title", "").lower():
                score += 2

            if score > 0:
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_matches = [item for _, item in scored_items[:top_k]]

        latency_ms = (time.perf_counter() - start) * 1000

        if not top_matches and self.knowledge_base:
            top_matches = [self.knowledge_base[0]]

        content_key = f"content_{lang}"
        formatted_docs = []
        context_parts = []

        for item in top_matches:
            body = item.get(content_key, item.get("content_zh", ""))
            formatted_docs.append({
                "id": item["id"],
                "category": item["category"],
                "title": item["title"],
                "content": body
            })
            context_parts.append(f"【FAQ {item['id']}】{item['title']}\n{body}")

        context_text = "\n---\n".join(context_parts)

        return {
            "matched_count": len(top_matches),
            "top_docs": formatted_docs,
            "context_text": context_text,
            "lang": lang,
            "latency_ms": round(latency_ms, 2)
        }

rag_engine = RAGEngine()
