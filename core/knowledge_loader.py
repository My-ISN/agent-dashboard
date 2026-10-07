"""
ISKOM AI-OS Dynamic Knowledge Base Loader
Memuat seluruh SOP, FAQ, Produk, Kebijakan, dan Template secara dinamis.
Dapat di-update oleh Admin tanpa perlu merombak source code aplikasi.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional


class KnowledgeBase:
    """Mesin pemuat dan pencari data pengetahuan dinamis perusahaan"""

    def __init__(self, knowledge_dir: Optional[str] = None):
        if not knowledge_dir:
            # Default ke folder knowledge di root proyek
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            knowledge_dir = os.path.join(base_dir, "knowledge")
        self.knowledge_dir = knowledge_dir
        self.cache: Dict[str, Any] = {}
        self.reload()

    def reload(self):
        """Memuat ulang seluruh file knowledge dari disk ke memori (Hot-Reload)"""
        self.cache = {
            "products": [],
            "faq": [],
            "templates": {},
            "rules": {},
            "documents": {}  # markdown docs (sop, policies, dll)
        }

        if not os.path.exists(self.knowledge_dir):
            return

        for filename in os.listdir(self.knowledge_dir):
            filepath = os.path.join(self.knowledge_dir, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                if filename.endswith(".json"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if filename == "products_pricing.json":
                        self.cache["products"] = data
                    elif filename == "faq.json":
                        self.cache["faq"] = data
                    elif filename == "message_templates.json":
                        self.cache["templates"] = data
                    elif filename == "rules_config.json":
                        self.cache["rules"] = data
                    else:
                        self.cache["documents"][filename] = data

                elif filename.endswith(".md"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        self.cache["documents"][filename] = f.read()

            except Exception as e:
                print(f"[!] Warning: Gagal memuat file knowledge '{filename}': {e}")

    # =========================================================================
    # QUERY & RETRIEVAL METHODS
    # =========================================================================

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Mencari laptop berdasarkan brand, tipe, atau spesifikasi"""
        q = query.lower()
        results = []
        for p in self.cache["products"]:
            searchable = f"{p['brand']} {p['model']} {p['specs']} {p['category']}".lower()
            if any(term in searchable for term in q.split()):
                results.append(p)
        return results if results else self.cache["products"][:2]

    def get_product_by_model(self, model_query: str) -> Optional[Dict[str, Any]]:
        """Mengambil detail 1 produk yang paling cocok"""
        q = model_query.lower()
        for p in self.cache["products"]:
            if p["model"].lower() in q or q in p["model"].lower():
                return p
            if p["brand"].lower() in q:
                return p
        return self.cache["products"][0] if self.cache["products"] else None

    def search_faq(self, query: str) -> Optional[Dict[str, str]]:
        """Mencari jawaban FAQ yang paling relevan dengan pertanyaan"""
        q_terms = set(re.findall(r'\w+', query.lower()))
        best_match = None
        highest_score = 0

        for item in self.cache["faq"]:
            faq_terms = set(re.findall(r'\w+', item["question"].lower()))
            overlap = len(q_terms.intersection(faq_terms))
            if overlap > highest_score:
                highest_score = overlap
                best_match = item

        return best_match if highest_score > 0 else (self.cache["faq"][0] if self.cache["faq"] else None)

    def get_document(self, doc_filename: str) -> Optional[str]:
        """Mengambil isi dokumen markdown (SOP atau Kebijakan)"""
        return self.cache["documents"].get(doc_filename)

    def get_formatted_template(self, template_key: str, **kwargs) -> str:
        """Mengambil dan mengisi template pesan otomatis"""
        tmpl = self.cache["templates"].get(template_key, "")
        if not tmpl:
            return ""
        try:
            return tmpl.format(**kwargs)
        except KeyError:
            return tmpl

    # =========================================================================
    # UPDATE MECHANISM (ADMIN CAPABILITY WITHOUT TOUCHING CODE)
    # =========================================================================

    def save_document(self, filename: str, content: str) -> bool:
        """Menyimpan atau memperbarui dokumen SOP/kebijakan baru ke folder knowledge"""
        filepath = os.path.join(self.knowledge_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.reload()
            return True
        except Exception as e:
            print(f"[!] Error saat menyimpan knowledge '{filename}': {e}")
            return False

    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """Menambahkan produk baru ke katalog tanpa menyentuh source code"""
        filepath = os.path.join(self.knowledge_dir, "products_pricing.json")
        try:
            self.cache["products"].append(product_data)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.cache["products"], f, indent=2)
            self.reload()
            return True
        except Exception as e:
            print(f"[!] Error saat menambah produk baru: {e}")
            return False
