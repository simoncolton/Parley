import numpy as np


class MathUtils:

    def clamp(num, min_value, max_value):
        return max(min(num, max_value), min_value)

    def get_overlap(a, b):
        return max(0, min(a[1], b[1]) - max(a[0], b[0]))

    def largest_pow2_lte(a):
        for i in range(0, 20):
            if 2**i > a:
                return 2**(i-1)
        return None

    def get_entropy(labels):
        labs = []
        for l in labels:
            labs.append(labels.index(l))
        addon = abs(min(labels)) + 1 if min(labs) < 0 else 0
        positive_labels = [l + addon for l in labs]
        """ Computes entropy of 0-1 vector. """
        n_labels = len(positive_labels)

        if n_labels <= 1:
            return 0

        counts = np.bincount(positive_labels)
        probs = counts[np.nonzero(counts)] / n_labels
        n_classes = len(probs)

        if n_classes <= 1:
            return 0
        return - np.sum(probs * np.log(probs)) / np.log(n_classes)

    def get_rolling_entropies(labels, window_length):
        rolling_entropies = []
        for i in range(0, len(labels) - window_length):
            labs = labels[i:i+window_length]
            rolling_entropies.append(MathUtils.get_entropy(labs))
        return rolling_entropies

    def euclidean_distance(x1, y1, x2, y2):
        return ((x1 - x2) * (x1 - x2)) + ((y1 - y2) * (y1 - y2))

    def highest_power_of_2_dividing(n):
        answer = 0
        while 2 ** answer < n:
            answer += 1
        return answer - 1

    def closest_power_of_2_dividing(n):
        highest = MathUtils.highest_power_of_2_dividing(n)
        dist1 = n - (2 ** highest)
        dist2 = (2 ** (highest + 1)) - n
        return highest if dist2 > dist1 else highest + 1
