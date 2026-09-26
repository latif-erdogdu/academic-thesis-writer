"""TF-IDF + Cosine Similarity ile claim-evidence benzerlik hesaplama.

scikit-learn TfidfVectorizer kullanarak offline, hızlı benzerlik.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Stopwords (Türkçe + İngilizce)
STOPWORDS = {
    # İngilizce
    "the", "a", "an", "and", "or", "of", "in", "for", "to", "with", "on", "by",
    "as", "at", "from", "into", "during", "including", "until", "against",
    "among", "throughout", "despite", "towards", "upon", "within", "without",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might",
    "must", "shall", "can", "this", "that", "these", "those", "it", "its",
    "we", "our", "you", "your", "he", "she", "his", "her", "they", "their",
    "i", "me", "my", "myself", "us", "our", "ours", "ourselves",
    # Türkçe
    "ve", "veya", "ile", "için", "bu", "şu", "o", "bir", "da", "de", "ki",
    "olan", "olarak", "gibi", "ise", "var", "yok", "mi", "mü", "mu", "mü",
    "ben", "sen", "o", "biz", "siz", "onlar", "benim", "senin", "onun",
    "bizim", "sizin", "onların", "beni", "seni", "onu", "bizi", "sizi",
    "onları", "içinde", "üzerinde", "altında", "yanında", "karşısında",
    "için", "gibi", "kadar", "daha", "en", "çok", "az", "büyük", "küçük",
}

# Tokenizer regex (kelimeleri ayır)
TOKEN_PATTERN = re.compile(r"\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{2,}\b")


@dataclass
class TFIDFSimilarityEngine:
    """TF-IDF tabanlı benzerlik motoru."""

    max_features: int = 5000
    ngram_range: tuple[int, int] = (1, 2)  # unigram + bigram
    min_df: int = 1
    max_df: float = 1.0
    stop_words: set[str] = field(default_factory=set)

    _vectorizer: TfidfVectorizer = field(init=False, repr=False)
    _fitted: bool = field(init=False, default=False)
    _corpus: list[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        self._vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            min_df=self.min_df,
            max_df=self.max_df,
            stop_words=list(self.stop_words),
            token_pattern=r"(?u)\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{2,}\b",
            lowercase=True,
            sublinear_tf=True,  # log(tf+1)
        )

    def fit(self, corpus: list[str]) -> "TFIDFSimilarityEngine":
        """Korpus üzerinde TF-IDF modelini eğit."""
        cleaned = [self._clean_text(doc) for doc in corpus]
        self._corpus = cleaned
        self._vectorizer.fit(cleaned)
        self._fitted = True
        return self

    def _clean_text(self, text: str) -> str:
        """Metni temizle: küçük harf, fazla boşlukları temizle."""
        if not text:
            return ""
        text = text.lower()
        # Sadece çoklu boşlukları tek boşluğa indir, tokenizasyon vectorizer'e bırak
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def transform(self, texts: list[str]) -> np.ndarray:
        """Metinleri TF-IDF vektörlerine dönüştür."""
        if not self._fitted:
            raise RuntimeError("Model eğitilmemiş. Önce fit() çağrın.")
        cleaned = [self._clean_text(doc) for doc in texts]
        return self._vectorizer.transform(cleaned)

    def fit_transform(self, corpus: list[str]) -> np.ndarray:
        """Eğit ve dönüştür."""
        return self.fit(corpus).transform(corpus)

    def similarity(self, text1: str, text2: str) -> float:
        """İki metin arası cosine similarity."""
        if not self._fitted:
            self.fit([text1, text2])
        vecs = self.transform([text1, text2])
        sim = cosine_similarity(vecs[0:1], vecs[1:2])[0, 0]
        return float(sim)

    def similarity_matrix(self, texts: list[str]) -> np.ndarray:
        """Metinler arası tüm çift similarity matrisi."""
        if not self._fitted:
            self.fit(texts)
        vecs = self.transform(texts)
        return cosine_similarity(vecs)

    def rank_similar(self, query: str, candidates: list[str], top_k: int = 5) -> list[tuple[int, float]]:
        """Sorgu ile en benzer top-k adayı bul."""
        if not self._fitted:
            self.fit([query] + candidates)
        query_vec = self.transform([query])
        cand_vecs = self.transform(candidates)
        sims = cosine_similarity(query_vec, cand_vecs)[0]
        ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


# Global engine instance (singleton pattern)
_DEFAULT_ENGINE: TFIDFSimilarityEngine | None = None


def get_similarity_engine() -> TFIDFSimilarityEngine:
    """Global TFIDF engine instance."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = TFIDFSimilarityEngine()
    return _DEFAULT_ENGINE


def compute_tfidf_similarity(text1: str, text2: str) -> float:
    """İki metin arası TF-IDF cosine similarity (basit fonksiyon)."""
    engine = TFIDFSimilarityEngine()  # Her çağrıda yeni engine
    return engine.similarity(text1, text2)


def rank_evidence_for_claim(
    claim_text: str,
    evidence_texts: list[str],
    top_k: int = 5,
) -> list[tuple[int, float]]:
    """İddia metni için kanıt metinlerini sırala.

    Returns: [(index, similarity_score), ...] - skor büyükten küçüğe.
    """
    engine = TFIDFSimilarityEngine()  # Her çağrıda yeni engine
    return engine.rank_similar(claim_text, evidence_texts, top_k)


@dataclass
class ClaimEvidenceMatcher:
    """İddia-kanıt eşleştirme motoru."""

    min_similarity: float = 0.3
    top_k: int = 5
    keyword_bonus_weight: float = 0.05
    max_keyword_bonus: float = 0.2

    _engine: TFIDFSimilarityEngine = field(init=False, default_factory=TFIDFSimilarityEngine)

    def find_evidence(
        self,
        claim_text: str,
        evidence_candidates: list[dict],
        text_field: str = "text",
    ) -> list[dict]:
        """İddia için en alakalı kanıtları bul ve sırala.

        Args:
            claim_text: İddia metni
            evidence_candidates: Kanıt adayları listesi (dict, 'text' alanı zorunlu)
            text_field: Kanıt dict'indeki metin alanı adı

        Returns:
            Sıralı kanıt listesi (similarity, keyword_bonus, final_score eklendi)
        """
        if not evidence_candidates:
            return []

        # TF-IDF için corpus hazırla
        corpus = [claim_text] + [c.get(text_field, "") for c in evidence_candidates]
        self._engine.fit(corpus)

        # Claim vektörü
        claim_vec = self._engine.transform([claim_text])

        results = []
        for idx, candidate in enumerate(evidence_candidates):
            text = candidate.get(text_field, "")
            if not text or len(text) < 50:
                continue

            # TF-IDF similarity
            cand_vec = self._engine.transform([text])
            tfidf_sim = cosine_similarity(
                self._engine._vectorizer.transform([claim_text]),
                cand_vec
            )[0, 0]

            # Anahtar kelime bonusu
            keyword_bonus = self._keyword_bonus(claim_text, text)

            final_score = float(tfidf_sim[0]) + keyword_bonus

            if final_score >= self.min_similarity:
                result = candidate.copy()
                result["tfidf_similarity"] = float(tfidf_sim[0])
                result["keyword_bonus"] = keyword_bonus
                result["final_score"] = final_score
                results.append(result)

        # Final score'a göre sırala
        results.sort(key=lambda x: x["final_score"], reverse=True)
        return results[:self.top_k]

    def _keyword_bonus(self, claim_text: str, evidence_text: str) -> float:
        """İddia ve kanıt metni arasındaki ortak anahtar kelime bonusu."""
        claim_words = set(self._extract_keywords(claim_text))
        evidence_words = set(self._extract_keywords(evidence_text))

        if not claim_words:
            return 0.0

        overlap = claim_words & evidence_words
        bonus = len(overlap) * self.keyword_bonus_weight
        return min(bonus, self.max_keyword_bonus)

    def _extract_keywords(self, text: str) -> set[str]:
        """Metinden anahtar kelimeleri çıkar (stopwords hariç, 3+ harf)."""
        words = re.findall(r"\b[a-zğüşıöçĞÜŞİÖÇ]{3,}\b", text.lower())
        return {w for w in words if w not in STOPWORDS}