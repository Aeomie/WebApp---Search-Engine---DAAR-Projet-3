from search_algorithms.astTree import RegEx, RegExTree, Operation

class NFA:
    def __init__(self, regexPattern: str):
        self.regex = RegEx(regexPattern).parse()
        self.regexPattern = regexPattern
        self.node_counter = 0
        self.alphabet = []
        # Build NFA using Thompson's construction
        self.start_state, self.final_state, self.transitions = self.build_nfa(self.regex)

        # Get all states
        self.states = self.get_all_states()

        # Build transition table
        self.transition_table = self.build_transition_table()

    # -----------------------------
    # State generator
    # -----------------------------
    def new_node(self):
        """Generate a new unique state ID"""
        state_id = f"q{self.node_counter}"
        self.node_counter += 1
        return state_id

    # -----------------------------
    # Build NFA using Thompson's Construction
    # -----------------------------
    def build_nfa(self, tree: RegExTree):
        """
        Build NFA fragment for a tree node.
        Returns (start_state, end_state, transitions)
        transitions is a dict: {from_state: {symbol: [to_states]}}
        """
        transitions = {}

        def add_transition(from_state, to_state, symbol):
            """Add a transition to the transitions dict"""
            if from_state not in transitions:
                transitions[from_state] = {}
            if symbol not in transitions[from_state]:
                transitions[from_state][symbol] = []
            transitions[from_state][symbol].append(to_state)

        # Base case: literal character
        if isinstance(tree.root, str):
            start = self.new_node()
            end = self.new_node()
            self.alphabet.append(tree.root)  # Add to alphabet
            add_transition(start, end, tree.root)

            return start, end, transitions

        # CONCAT operation
        elif tree.root == Operation.CONCAT:
            # Build left subtree
            left_start, left_end, left_trans = self.build_nfa(tree.subTrees[0])
            transitions.update(left_trans)

            # Build right subtree
            right_start, right_end, right_trans = self.build_nfa(tree.subTrees[1])
            transitions.update(right_trans)

            # Connect left end to right start with epsilon²
            add_transition(left_end, right_start, 'ε')

            return left_start, right_end, transitions

        # ALTERN (|) operation
        elif tree.root == Operation.ALTERN:
            start = self.new_node()
            end = self.new_node()

            # Build both alternatives
            left_start, left_end, left_trans = self.build_nfa(tree.subTrees[0])
            transitions.update(left_trans)

            right_start, right_end, right_trans = self.build_nfa(tree.subTrees[1])
            transitions.update(right_trans)

            # Connect start to both alternatives with epsilon
            add_transition(start, left_start, 'ε')
            add_transition(start, right_start, 'ε')

            # Connect both ends to final state with epsilon
            add_transition(left_end, end, 'ε')
            add_transition(right_end, end, 'ε')

            return start, end, transitions

        # ETOILE (*) operation
        elif tree.root == Operation.ETOILE:
            start = self.new_node()
            end = self.new_node()

            # Build subtree
            sub_start, sub_end, sub_trans = self.build_nfa(tree.subTrees[0])
            transitions.update(sub_trans)

            # Epsilon from start to sub_start (one or more times)
            add_transition(start, sub_start, 'ε')

            # Epsilon from sub_end back to sub_start (loop)
            add_transition(sub_end, sub_start, 'ε')

            # Epsilon from sub_end to end (exit)
            add_transition(sub_end, end, 'ε')

            # Epsilon from start to end (zero times)
            add_transition(start, end, 'ε')

            return start, end, transitions

        # PLUS (+) operation
        elif tree.root == Operation.PLUS:
            start = self.new_node()
            end = self.new_node()

            # Build subtree
            sub_start, sub_end, sub_trans = self.build_nfa(tree.subTrees[0])
            transitions.update(sub_trans)

            # Epsilon from start to sub_start (at least once)
            add_transition(start, sub_start, 'ε')

            # Epsilon from sub_end back to sub_start (loop)
            add_transition(sub_end, sub_start, 'ε')

            # Epsilon from sub_end to end (exit)
            add_transition(sub_end, end, 'ε')

            return start, end, transitions

        # PROTECTION (just unwrap)
        elif tree.root == Operation.PROTECTION:
            return self.build_nfa(tree.subTrees[0])

        else:
            raise Exception(f"Unknown operation: {tree.root}")

    # -----------------------------
    # Get all states
    # -----------------------------
    """Extract all states from transitions & orders them"""
    def get_all_states(self):
        states = set()
        states.add(self.start_state)
        states.add(self.final_state)

        for from_state, node_transitions in self.transitions.items():
            states.add(from_state)
            for symbol, to_states in node_transitions.items():
                states.update(to_states)

        return sorted(states, key=lambda x: int(x[1:])) # takes the second and sorts them , like in q10 it takes 10

    # -----------------------------
    # Build transition table
    # -----------------------------
    def build_transition_table(self):
        """
        Build a transition table as a dictionary:
        {state: {symbol: [next_states]}}
        """
        table = {}

        # Initialize all states
        for state in self.states:
            table[state] = {symbol: [] for symbol in self.alphabet}
            table[state]['ε'] = []  # Epsilon transitions

        # Fill in transitions
        for from_state, trans in self.transitions.items():
            for symbol, to_states in trans.items():
                table[from_state][symbol] = to_states

        return table

    # -----------------------------
    # Display methods
    # -----------------------------
    def display_transition_table(self):
        """Print the transition table in a readable format"""
        print("\n=== NFA Transition Table ===")
        print(f"Initial state: {self.start_state}")
        print(f"Final state: {self.final_state}")
        print(f"Alphabet: {sorted(self.alphabet)}")
        print(f"\nStates: {self.states}\n")

        # Header
        symbols = sorted(self.alphabet) + ['ε']
        header = f"{'State':<8} | " + " | ".join(f"{s:<10}" for s in symbols)
        print(header)
        print("-" * len(header))

        # Rows
        for state in self.states:
            marker = "*" if state == self.start_state else " "
            marker += ">" if state == self.final_state else " "
            row = f"{state:<6}{marker} | "

            for symbol in symbols:
                targets = self.transition_table[state].get(symbol, [])
                targets_str = ",".join(targets) if targets else "∅"
                row += f"{targets_str:<10} | "

            print(row)
        print("* for start node , > for the final node")

    def __str__(self):
        """String representation of the NFA"""
        return f"NFA(states={len(self.states)}, alphabet={self.alphabet})"
