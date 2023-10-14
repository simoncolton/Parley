from dataclasses import dataclass
import random
import numpy as np

@dataclass
class CorrelationAnalysis:
    tag: str = None
    correlation: float = None
    support: float = None

@dataclass
class Activations:
    id: str = None
    pc_degradation: int = None
    activations: [] = None

def get_tags():
    with open("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/listening_data.csv") as f:
        lines = f.readlines()
        tags_line_parts = lines[0].split(",")
        tags = [tags_line_parts[t].strip() for t in range(4, len(tags_line_parts))]
        return tags

def get_correlations(correlation_hash):
    tag_correlations = {}
    for tag_num, tag in enumerate(tags):
      tag_pcs = [int(pc) for pc in correlation_hash.keys()]
      tag_activations = [correlation_hash[pc][tag_num] for pc in correlation_hash.keys()]
      tag_correlations[tag] = np.corrcoef(tag_pcs, tag_activations)[0][1]
    return tag_correlations

def get_ten_fold_split_ids():
    with open("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/listening_data.csv") as f:
        lines = f.readlines()
        tags_line_parts = lines[0].split(",")
        tags = [tags_line_parts[t].strip() for t in range(4, len(tags_line_parts))]
        unique_lines = []
        pos = 0
        while pos < len(lines):
            line1 = lines[pos].strip()
            parts1 = line1.split(",")
            id = f"{parts1[0]}__{parts1[1]}__{parts1[2]}"


def generate_correlations_file():
    correlation_hashes = {}
    with open("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/listening_data.csv") as f:
        lines = f.readlines()
        tags_line_parts = lines[0].split(",")
        tags = [tags_line_parts[t].strip() for t in range(4, len(tags_line_parts))]
        unique_lines = []
        pos = 0
        while pos < len(lines):
            line1 = lines[pos].strip()
            parts1 = line1.split(",")
            id1 = f"{parts1[0]}__{parts1[1]}__{parts1[2]}"
            unique_lines.append(line1)
            a1 = [f"{p}," for p in parts1[4:]]
            is_same = True
            pos += 1
            while is_same and pos < len(lines):
                line2 = lines[pos].strip()
                parts2 = line2.split(",")
                id2 = f"{parts2[0]}__{parts2[1]}__{parts2[2]}"
                if id1 != id2:
                    is_same = False
                else:
                    a2 = [f"{p}," for p in parts2[4:]]
                    if a1 != a2:
                        is_same = False
                if is_same:
                    pos += 1
        print(len(lines), "->", len(unique_lines), "lines")

        for line in lines:
            parts = line.split(",")
            id = f"{parts[0]}__{parts[1]}__{parts[2]}"
            try:
                pc_change = int(parts[3])
                if id not in correlation_hashes:
                    correlation_hashes[id] = {}
                activations = [float(parts[i]) for i in range(4, len(parts))]
                correlation_hashes[id][pc_change] = activations
            except:
                pass
        triples = []
        for tag in tags:
            corrs = [get_correlations(correlation_hashes[key])[tag] for key in correlation_hashes.keys()]
            av = sum(corrs) / len(corrs)
            std = np.std(corrs)
            prop_pos = len([c for c in corrs if c > 0]) / len(corrs)
            prop_neg = len([c for c in corrs if c < 0]) / len(corrs)
            support = prop_pos if av >= 0 else prop_neg
            print(tag, f"{av:.5f}", f"{support:.5f}", f"{std:.5f}", f"{prop_pos:.5f}", f"{prop_neg:.5f}")
            triples.append((av, support, std, prop_pos, prop_neg, tag))
        triples.sort()
        print("===")
        for t in triples:
            line = t[-1]
            for i in range(0, len(t) - 1):
                line += f",{t[i]:.5f}"
            print(line)

def load_correlations(neg_threshold, pos_threshold):
    correlations = {}
    with open("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/correlations.csv") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split(",")
            try:
                ca = CorrelationAnalysis(parts[0], float(parts[1]), float(parts[2]))
                if ca.correlation <= neg_threshold or ca.correlation >= pos_threshold:
                    correlations[parts[0]] = ca
            except:
                pass
    return correlations

def are_equal_activations(act1, act2):
    for ind, a in enumerate(act1):
        if act2[ind] != a:
            return False
    return True

def load_activations():
    activations_hash = {}
    with open("/Users/Simon/Dropbox/Code/PycharmProjects/Parley/listening_data.csv") as f:
        lines = f.readlines()
        for line in lines:
            parts = line.split(",")
            id = f"{parts[0]}__{parts[1]}__{parts[2]}"
            try:
              pc_degradation = int(parts[3])
              if id not in activations_hash:
                  activations_hash[id] = []
              av = [float(parts[i]) for i in range(4, len(parts))]
              activation = Activations(id, pc_degradation, av)
              activations_hash[id].append(activation)
            except:
                pass

        return activations_hash

def is_degraded(correlations, tags, id, pc1, pc2):
    activations = activations_hash[id]
    activations1 = [a for a in activations if a.pc_degradation == pc1][0].activations
    activations2 = [a for a in activations if a.pc_degradation == pc2][0].activations
    if are_equal_activations(activations1, activations2):
        return None
    num_matches = 0
    num_misses = 0
    match_total = 0
    miss_total = 0
    for ind, tag in enumerate(tags):
        if tag in correlations.keys():
            tag_direction = "pos" if activations2[ind] > activations1[ind] else "neg"
            correlation_direction = "pos" if correlations[tag].correlation > 0 else "neg"
            if correlation_direction == tag_direction:
                num_matches += 1
                match_total += correlations[tag].support
            else:
                num_misses += 1
                miss_total += correlations[tag].support
            #print(tag, activations1[ind], activations2[ind], tag_direction, correlation_direction)
    #print("matches", num_matches)
    #print("misses", num_misses)
    #print("IS DEGRADED" if num_matches >= num_misses else "IS NOT DEGRADED")
    return num_matches >= num_misses
    #return match_total > miss_total

tags = get_tags()
generate_correlations_file()
#correlations = load_correlations(-0.5, 0.4)
correlations = load_correlations(-0.5, 0.4)
activations_hash = load_activations()

for pc in range(5, 101, 5):
    num_correct = 0
    num_trials = 0
    for key in activations_hash.keys():
        is_correct = is_degraded(correlations, tags, key, 0, pc)
        if is_correct is not None:
            num_correct += 1 if is_correct else 0
            num_trials += 1
    success1 = ((100 * num_correct)/num_trials)
    print(f"0->{pc}:", num_correct, "out of", num_trials, "=", f"{success1:.1f}% (degraded)")
    num_correct = 0
    num_trials = 0
    for key in activations_hash.keys():
        is_correct = not is_degraded(correlations, tags, key, pc, 0)
        if is_correct is not None:
            num_correct += 1 if is_correct else 0
            num_trials += 1
    success2 = ((100 * num_correct)/num_trials)
    print(f"0->{pc}:", num_correct, "out of", num_trials, "=", f"{success2:.1f}% (not degraded)")
    print(f"total: {(success1 + success2)/2:.1f}%")
    print("---")
