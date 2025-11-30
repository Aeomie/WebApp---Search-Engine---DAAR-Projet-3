# main.py
from concurrent.futures import ProcessPoolExecutor

from fastapi import FastAPI
from engine import engine_text

from functools import lru_cache
from pydantic import BaseModel
from typing import List
from search_algorithms.nfa import NFA
from search_algorithms.dfa import DFA

class SearchRequest(BaseModel):
    pattern: str
    texts: List[str]  # can handle one or multiple titles
    verbose: bool = False

class GenerateRequset(BaseModel):
    pattern: str
    max_length: int
    max_words: int

class AdvancedSearchRequest(BaseModel):
    pattern: str
    book_ids: List[int]  # the books to load
    verbose: bool = False


app = FastAPI()


@app.post("/engine/generateWords")
def generate_words(request: GenerateRequset):
    pattern = request.pattern
    max_length = request.max_length
    max_word = request.max_words
    nfa = NFA(pattern)
    dfa = DFA(nfa)
    words = dfa.generate_words(max_words=max_word, max_length=max_length)
    return {"generated_words": words}

