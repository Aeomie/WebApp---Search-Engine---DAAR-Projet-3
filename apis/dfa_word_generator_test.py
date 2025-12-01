
from search_algorithms.nfa import NFA
from search_algorithms.dfa import DFA

pattern = "ab*a"
nfa = NFA(pattern)
dfa = DFA(nfa)

words = dfa.generate_words(max_words=5, max_length=150)

print(words)

print(f"Total words generated: {len(words)}")