import numpy as np
import os
from dataclasses import dataclass

@dataclass
class Excerpt:
    id: "" = None
    pc_degradations: [] = None
    prop_degradations: [] = None
    prop_impacts: [] = None
    prop_overlap: [] = None
    activation_progressions_hash: {} = None
    correlations_hash: {} = None
    initial_directions_hash: {} = None

def get_correlations(filepath):
    excerpts_hash = {}
    with open(filepath) as f:
        lines = f.readlines()
        column_tags = lines[0].split(",")
        for line in lines[1:]:
            parts = line.split(",")
            midi_id = parts[0].split("__")[0]
            excerpt_id = f"{midi_id}_{parts[2]}_{parts[3]}"
            if excerpt_id not in excerpts_hash:
                excerpts_hash[excerpt_id] = Excerpt(excerpt_id, [], [], [], [], {}, {}, {})
            excerpt = excerpts_hash[excerpt_id]
            excerpt.pc_degradations.append(float(parts[1]))
            excerpt.prop_degradations.append(float(parts[5]))
            excerpt.prop_impacts.append(float(parts[6]))
            excerpt.prop_overlap.append(float(parts[7]))
            for pos in range(8, len(parts)):
                tag = column_tags[pos]
                if tag not in excerpt.activation_progressions_hash:
                    excerpt.activation_progressions_hash[tag] = []
                excerpt.activation_progressions_hash[tag].append(float(parts[pos]))
    for excerpt_id in excerpts_hash:
        excerpt = excerpts_hash[excerpt_id]
        for tag in excerpt.activation_progressions_hash.keys():
            vals = excerpt.activation_progressions_hash[tag]
            ds = excerpt.prop_degradations
            c = np.corrcoef(ds, vals)[0][1]
            excerpt.correlations_hash[tag] = c
            pos = [pos for pos in range(0, len(ds)) if ds[pos] == 0 or ds[pos-1] == 0][-1]
            excerpt.initial_directions_hash[tag] = (vals[pos] - vals[0])/ds[pos]

    return excerpts_hash

dir = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Data/ListeningAnalysisData"
csv_filepaths = [f for f in os.listdir(dir) if ".csv" in f and "chpn" in f]
all_excerpts = []
for csv_filepath in csv_filepaths:
    all_excerpts.extend(get_correlations(f"{dir}/{csv_filepath}").values())

tuples = []
activations_hash = {}
original_activations_hash = {}
for tag in all_excerpts[0].correlations_hash.keys():
    activations_hash[tag] = []
    original_activations_hash[tag] = []
for tag in all_excerpts[0].correlations_hash.keys():
    for excerpt in all_excerpts:
        activations_hash[tag].extend(excerpt.activation_progressions_hash[tag])
        original_activations_hash[tag].append(excerpt.activation_progressions_hash[tag][0])
    mean_activation = np.mean(activations_hash[tag])
    std = np.std(activations_hash[tag])
    original_mean = np.mean(original_activations_hash[tag])
    original_std = np.std(original_activations_hash[tag])
    correlations = [e.correlations_hash[tag] for e in all_excerpts]
    mean_correlation = np.mean(correlations)
    num_cs = len(correlations)
    prop_positives = len([c for c in correlations if c >= 0])/num_cs
    prop_negatives = len([c for c in correlations if c <= 0])/num_cs
    initial_directions = [e.initial_directions_hash[tag] for e in all_excerpts]
    mean_initial_direction = np.mean(initial_directions)
    tuples.append((tag, mean_correlation, prop_positives, prop_negatives, mean_activation, std, original_mean, original_std, mean_initial_direction))

print("tag,tag_ind,mean_correlation,prop_pos,prop_neg,mean_activation,std_activation,mean_original_activation,std_original_activation,mean_initial_move")
#tuples.sort(key= lambda x: x[1])
for ind, t in enumerate(tuples):
    l = "\"" + t[0].strip() + "\"," + f"{ind}"
    for t in t[1:]:
        l += f",{t:.5f}"
    print(f"ip.add_listener({l})")
correlations = [t[1] for t in tuples]
activations = [t[6] for t in tuples]
print("---")
print("average_correlation = ", np.mean(correlations))
print("average activation = ", np.mean(activations))

