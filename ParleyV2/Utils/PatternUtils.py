import random

class PatternUtils:

    def get_form_pattern(num_patterns):
        if num_patterns == 1:
            return "A"
        patterns = []
        if num_patterns == 2:
            patterns.append("AB")
            patterns.append("ABA")
            patterns.append("ABBA")
            patterns.append("ABB")
            patterns.append("AAB")
            patterns.append("AABB")
            return random.choice(patterns)
        if num_patterns == 3:
            patterns.append("ABC")
            patterns.append("ABABC")
            patterns.append("ABBC")
            patterns.append("AABBCC")
            patterns.append("ABABC")
            patterns.append("ABCC")
            return random.choice(patterns)
        return "ABABC"
