"""
Deep NLP Analysis Engine
Implements full text analytics curriculum:
- Text Preprocessing (tokenize, stopwords, stemming, lemmatization)
- Bag of Words (BoW) word frequency
- TF-IDF analysis
- N-gram analysis (bigrams, trigrams)
- Topic Modeling (LDA)
- Naive Bayes classification
- K-Means Clustering + PCA visualization
- Named Entity Recognition (NLTK)
- Extractive Text Summarization
- Vocabulary statistics
"""
import re
import json
import streamlit as st
from collections import Counter

# ── NLTK Setup ────────────────────────────────────────────────────────────────
import nltk

def _nltk_setup():
    pkgs = [
        "punkt", "punkt_tab", "stopwords", "wordnet",
        "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng",
        "maxent_ne_chunker", "maxent_ne_chunker_tab", "words", "omw-1.4",
    ]
    for p in pkgs:
        try:
            nltk.download(p, quiet=True)
        except Exception:
            pass

_nltk_setup()

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import ne_chunk, pos_tag
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, PCA as SkPCA
from sklearn.cluster import KMeans
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder

_stemmer     = PorterStemmer()
_lemmatizer  = WordNetLemmatizer()
_analyzer    = SentimentIntensityAnalyzer()

# Extended stop words for product reviews
_STOP = set(stopwords.words("english"))
_STOP.update({
    "product", "buy", "get", "got", "one", "also", "even", "much", "well",
    "would", "really", "use", "used", "using", "thing", "think", "time",
    "bit", "lot", "way", "make", "made", "need", "know", "still", "day",
    "im", "its", "ive"
})


# ── Preprocessing ─────────────────────────────────────────────────────────────
def preprocess(text: str, mode: str = "lemma") -> list[str]:
    """Full NLP preprocessing: lowercase → tokenize → stopwords → stem/lemma."""
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in _STOP and len(t) > 2 and t.isalpha()]
    if mode == "stem":
        return [_stemmer.stem(t) for t in tokens]
    return [_lemmatizer.lemmatize(t) for t in tokens]


# ── Vocabulary Stats ──────────────────────────────────────────────────────────
def vocab_stats(texts: list[str]) -> dict:
    all_words = re.findall(r"\b[a-zA-Z]{2,}\b", " ".join(texts).lower())
    unique    = set(all_words)
    avg_len   = sum(len(t.split()) for t in texts) / max(len(texts), 1)
    try:
        n_sents = sum(len(sent_tokenize(t)) for t in texts[:100])
    except Exception:
        n_sents = 0
    return {
        "total_reviews":      len(texts),
        "total_tokens":       len(all_words),
        "unique_tokens":      len(unique),
        "vocab_richness_pct": round(len(unique) / max(len(all_words), 1) * 100, 1),
        "avg_words_per_review": round(avg_len, 1),
        "total_sentences":    n_sents,
    }


# ── BoW Word Frequency ────────────────────────────────────────────────────────
def bow_frequency(texts: list[str], top_n: int = 25) -> dict[str, int]:
    tokens = []
    for t in texts:
        tokens.extend(preprocess(t))
    return dict(Counter(tokens).most_common(top_n))


# ── TF-IDF ───────────────────────────────────────────────────────────────────
def tfidf_terms(texts: list[str], top_n: int = 20) -> dict[str, float]:
    if len(texts) < 2:
        return {}
    try:
        vec  = TfidfVectorizer(max_features=300, stop_words="english",
                               ngram_range=(1, 1), min_df=1)
        mat  = vec.fit_transform(texts)
        sc   = mat.mean(axis=0).A1
        feat = vec.get_feature_names_out()
        idx  = sc.argsort()[::-1][:top_n]
        return {feat[i]: round(float(sc[i]), 4) for i in idx}
    except Exception:
        return {}


# ── N-grams ───────────────────────────────────────────────────────────────────
def ngram_freq(texts: list[str], n: int = 2, top_k: int = 15) -> dict[str, int]:
    if not texts:
        return {}
    try:
        vec  = CountVectorizer(ngram_range=(n, n), stop_words="english",
                               max_features=200, min_df=1)
        mat  = vec.fit_transform(texts)
        cnt  = mat.sum(axis=0).A1
        feat = vec.get_feature_names_out()
        pairs = sorted(zip(feat, cnt.tolist()), key=lambda x: x[1], reverse=True)
        return {k: int(v) for k, v in pairs[:top_k]}
    except Exception:
        return {}


# ── LDA Topic Modeling ────────────────────────────────────────────────────────
def lda_topics(texts: list[str], n_topics: int = 3) -> list[dict]:
    if len(texts) < 5:
        return []
    try:
        vec = CountVectorizer(max_features=400, stop_words="english",
                              min_df=1, max_df=0.9)
        dtm = vec.fit_transform(texts)
        feat = vec.get_feature_names_out()

        lda = LatentDirichletAllocation(
            n_components=n_topics, random_state=42,
            max_iter=15, learning_method="online", learning_decay=0.7,
        )
        lda.fit(dtm)
        doc_dist = lda.transform(dtm)

        topic_names = {
            0: "User Experience & Quality",
            1: "Pricing & Purchase Decision",
            2: "Technical Performance",
        }
        topics = []
        for i, comp in enumerate(lda.components_):
            top_idx = comp.argsort()[::-1][:8]
            topics.append({
                "id":       i + 1,
                "name":     topic_names.get(i, f"Topic {i+1}"),
                "keywords": [feat[j] for j in top_idx],
                "weights":  [round(float(comp[j]), 2) for j in top_idx],
                "doc_share": round(float(doc_dist[:, i].mean()) * 100, 1),
            })
        return topics
    except Exception:
        return []


# ── Extractive Summarization ──────────────────────────────────────────────────
def extractive_summary(texts: list[str], top_n: int = 4) -> str:
    """TF-IDF sentence scoring — returns most representative sentences."""
    sents = []
    for t in texts:
        try:
            for s in sent_tokenize(t):
                s = s.strip()
                if 40 < len(s) < 500:
                    sents.append(s)
        except Exception:
            pass

    if not sents:
        return ""
    if len(sents) <= top_n:
        return " … ".join(sents)

    try:
        vec   = TfidfVectorizer(stop_words="english", min_df=1)
        mat   = vec.fit_transform(sents)
        scores = mat.mean(axis=1).A1
        top_idx = scores.argsort()[::-1][:top_n]
        return " … ".join(sents[i] for i in sorted(top_idx))
    except Exception:
        return " … ".join(sents[:top_n])


# ── Named Entity Recognition ──────────────────────────────────────────────────
def ner_analysis(texts: list[str]) -> dict:
    """NLTK NE chunker — rule-based NER."""
    counts   = Counter()
    examples = {}

    NE_LABELS = {
        "ORGANIZATION": "Organizations / Brands",
        "PERSON":       "People / Names",
        "GPE":          "Locations",
        "FACILITY":     "Facilities",
        "GSP":          "Geo-Socio-Political",
    }

    for text in texts[:40]:  # limit for speed
        try:
            tokens   = word_tokenize(text)
            tags     = pos_tag(tokens)
            tree     = ne_chunk(tags, binary=False)
            for subtree in tree:
                if hasattr(subtree, "label"):
                    ent_type = subtree.label()
                    ent_text = " ".join(l[0] for l in subtree.leaves())
                    counts[ent_type] += 1
                    examples.setdefault(ent_type, [])
                    if ent_text not in examples[ent_type]:
                        examples[ent_type].append(ent_text)
        except Exception:
            pass

    return {
        "counts":   dict(counts.most_common(8)),
        "examples": {k: v[:5] for k, v in examples.items()},
        "labels":   NE_LABELS,
    }


# ── K-Means Clustering + PCA ──────────────────────────────────────────────────
def cluster_and_pca(texts: list[str], n_clusters: int = 3) -> dict:
    """K-Means on TF-IDF vectors + PCA 2D reduction for scatter plot."""
    if len(texts) < max(n_clusters, 4):
        return {}
    try:
        vec    = TfidfVectorizer(max_features=150, stop_words="english", min_df=1)
        mat    = vec.fit_transform(texts)
        feat   = vec.get_feature_names_out()
        k      = min(n_clusters, len(texts) // 2, 5)

        km     = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=100)
        labels = km.fit_predict(mat)

        pca    = SkPCA(n_components=2)
        coords = pca.fit_transform(mat.toarray())

        cluster_kw = {}
        for i in range(k):
            center = km.cluster_centers_[i]
            top    = [feat[j] for j in center.argsort()[::-1][:5]]
            cluster_kw[i] = top

        return {
            "labels":     labels.tolist(),
            "x":          [round(c[0], 3) for c in coords],
            "y":          [round(c[1], 3) for c in coords],
            "keywords":   cluster_kw,
            "sizes":      dict(Counter(labels.tolist())),
            "k":          k,
        }
    except Exception:
        return {}


# ── Naive Bayes Feature Analysis ──────────────────────────────────────────────
def nb_features(texts: list[str]) -> dict:
    """Naive Bayes classification with VADER auto-labels. Shows top discriminative words."""
    if len(texts) < 8:
        return {}
    try:
        # Auto-label with VADER
        labels = []
        for t in texts:
            c = _analyzer.polarity_scores(t)["compound"]
            labels.append("positive" if c >= 0.05 else ("negative" if c <= -0.05 else "neutral"))

        vec    = CountVectorizer(stop_words="english", max_features=500, min_df=1)
        X      = vec.fit_transform(texts)
        feat   = vec.get_feature_names_out()
        le     = LabelEncoder()
        y      = le.fit_transform(labels)

        nb     = MultinomialNB()
        nb.fit(X, y)

        top_feats = {}
        for idx, cls in enumerate(le.classes_):
            if idx < len(nb.feature_log_prob_):
                top_idx = nb.feature_log_prob_[idx].argsort()[::-1][:12]
                top_feats[cls] = [feat[i] for i in top_idx]

        return {
            "top_features": top_feats,
            "label_dist":   dict(Counter(labels)),
        }
    except Exception:
        return {}


# ── Master Runner ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def run_deep_nlp(texts_json: str) -> dict:
    """
    Full NLP pipeline.
    texts_json: JSON-serialized list[str] for Streamlit cache compatibility.
    """
    texts = json.loads(texts_json)
    if not texts:
        return {}
    texts = [t for t in texts if len(t.strip()) > 20][:200]

    return {
        "vocab":    vocab_stats(texts),
        "bow":      bow_frequency(texts),
        "tfidf":    tfidf_terms(texts),
        "bigrams":  ngram_freq(texts, n=2),
        "trigrams": ngram_freq(texts, n=3),
        "topics":   lda_topics(texts),
        "summary":  extractive_summary(texts),
        "ner":      ner_analysis(texts),
        "clusters": cluster_and_pca(texts),
        "nb":       nb_features(texts),
    }
