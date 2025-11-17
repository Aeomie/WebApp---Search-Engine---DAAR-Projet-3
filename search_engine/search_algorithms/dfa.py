from search_algorithms.nfa import NFA

class DFA:
    def __init__(self, nfa: NFA):
        self.nfa = nfa
        self.alphabet = [s for s in nfa.alphabet if s != 'ε']  # DFA alphabet
        self.start_state = frozenset(self.epsilon_closure(nfa.start_state))
        self.transitions = {}
        self.final_states = set()
        self.build_dfa()
        self.detect_final_states()

    # -----------------------------
    # Epsilon closure
    # -----------------------------
    def epsilon_closure(self, states):
        if isinstance(states, str):
            states = {states}

        closure = set(states)
        stack = list(states)

        while stack:
            state = stack.pop()
            for t in self.nfa.transitions.get(state, {}).get('ε', []):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return closure

    # -----------------------------
    # Build DFA
    # -----------------------------
    def build_dfa(self):
        queue = [self.start_state]
        visited = set()

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            self.transitions[current] = {}

            for symbol in self.alphabet:
                # Collect all NFA states reachable by this symbol
                next_states = set()
                for s in current:
                    next_states.update(self.nfa.transitions.get(s, {}).get(symbol, []))
                # Take epsilon closure of the result
                if next_states:
                    closure = frozenset(self.epsilon_closure(next_states))
                    self.transitions[current][symbol] = closure
                    if closure not in visited and closure not in queue:
                        queue.append(closure)
                else:
                    self.transitions[current][symbol] = frozenset()

    # -----------------------------
    # Detect DFA final states
    # -----------------------------
    def detect_final_states(self):
        for state in self.transitions:
            if self.nfa.final_state in state:
                self.final_states.add(state)

    # -----------------------------
    # Display DFA transition table
    # -----------------------------
    def display_transition_table(self):
        print("\n=== DFA Transition Table ===")
        print(f"Start state: {set(self.start_state)}")
        print(f"Final states: {[set(s) for s in self.final_states]}\n")

        header = f"{'State':<30} | " + " | ".join(f"{s:<15}" for s in self.alphabet)
        print(header)
        print("-" * len(header))

        for state, trans in self.transitions.items():
            state_label = ",".join(sorted(state))
            marker = ""
            if state == self.start_state:
                marker += "*"
            if state in self.final_states:
                marker += ">"
            row = f"{state_label:<28}{marker:<2} | "
            for symbol in self.alphabet:
                targets = trans.get(symbol, frozenset())
                targets_str = ",".join(sorted(targets)) if targets else "∅"
                row += f"{targets_str:<15} | "
            print(row)
        print("\n* for start state, > for final state")

    # -----------------------------
    # Match word using DFA
    # -----------------------------
    def match_dfa(self, text: str, max_matches: int = 0):
        """
        Find all substrings in `text` that are accepted by the DFA.
        Returns a list of tuples: (matched_substring, start_index)
        """
        matches = []

        for start in range(len(text)):
            current_state = self.start_state
            for end in range(start, len(text)):
                if max_matches != 0 and len(matches) >= max_matches:
                    return matches, len(matches)

                char = text[end]
                if char not in self.alphabet:
                    break  # stop this substring
                current_state = self.transitions.get(current_state, {}).get(char, frozenset())
                if not current_state:
                    break  # dead end
                if current_state in self.final_states:
                    matches.append(start) # Just store the start index
                    # If you want the actual matched substring, uncomment the next line
                    #matches.append((text[start:end + 1], start))
        return matches, len(matches)
