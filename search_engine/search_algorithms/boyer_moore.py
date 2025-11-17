class Boyer:
    def __init__(self, pattern):
        self.pattern = pattern
        self.m = len(pattern)
        self.hoops = self.compute_hoops(pattern)

    def compute_hoops(self, pattern):
        hoops = {}
        for i in range(len(pattern)):
            hoops[pattern[i]] = max(1, self.m - i - 1)
        # default skip for all other characters
        hoops['*'] = self.m
        return hoops


    def match_boyer(self, text, max_match = 0):
        n = len(text)
        i = 0  # index in text
        word_counter = 0
        word_indexes = []
        while i <= n - self.m:
            if word_counter >= max_match and max_match != 0:
                break
            j = self.m - 1  # start from right of pattern

            # compare pattern from right to left
            while j >= 0 and self.pattern[j] == text[i + j]:
                j -= 1

            if j < 0:
                # match found
                #print("Pattern found at index", i)
                word_indexes.append(i)
                word_counter += 1
                # shift pattern completely after match or default
                if i + self.m < n:
                    next_char = text[i + self.m]
                    i += self.hoops.get(next_char, self.hoops['*'])
                else:
                    i += 1
            else:
                # mismatch: shift according to bad-character table
                bad_char = text[i + j] # get the character where there was a mismatch
                i += self.hoops.get(bad_char, self.hoops['*'])

        return word_indexes, word_counter
