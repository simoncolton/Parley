import tensorflow as tf
import numpy as np
from tqdm import tqdm
from ParleyV2.Utils.MusicUtils import *

# To install tensorflow for macos
# sudo python pip install tensorflow-macos
# sudo python pip install tensorflow-metal

class ListeningUtils:

    classical_interestingness_model = None
    c20_interestingness_model = None
    rnn_units = 1024
    vocab_size = 12
    embedding_dim = 256
    batch_size = 1
    classical_checkpoint_dir = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Parley/Models/BerkerClassical"
    c20_checkpoint_dir = "/Users/Simon/Dropbox/Code/PycharmProjects/Parley/Parley/Models/BerkerModern"

    def build_interestingness_models():
        if ListeningUtils.classical_interestingness_model is None:
            ListeningUtils.classical_interestingness_model = ListeningUtils.build_interestingness_model(ListeningUtils.classical_checkpoint_dir)
            ListeningUtils.c20_interestingness_model = ListeningUtils.build_interestingness_model(ListeningUtils.c20_checkpoint_dir)

    def build_interestingness_model(checkpoint_dir):
        embedding_layer = tf.keras.layers.Embedding(ListeningUtils.vocab_size, ListeningUtils.embedding_dim,
                                                    batch_input_shape=[ListeningUtils.batch_size, None])
        lstm = tf.keras.layers.LSTM(ListeningUtils.rnn_units, return_sequences=True, recurrent_initializer='glorot_uniform',
                                    recurrent_activation='sigmoid', stateful=True)
        dense_layer = tf.keras.layers.Dense(ListeningUtils.vocab_size)
        model = tf.keras.Sequential([embedding_layer, lstm, dense_layer])
        model.load_weights(tf.train.latest_checkpoint(checkpoint_dir))
        model.build(tf.TensorShape([1, None]))
        return model

    def predict_classical_interestingness(prior_pitch_classes, pitch_class):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.classical_interestingness_model
        return ListeningUtils.predict_interestingness(model, prior_pitch_classes, pitch_class)

    def predict_c20_interestingness(prior_pitch_classes, pitch_class):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.c20_interestingness_model
        return ListeningUtils.predict_interestingness(model, prior_pitch_classes, pitch_class)

    def predict_interestingness(model, prior_pitch_classes, pitch_class):
        input_eval = tf.expand_dims(prior_pitch_classes, 0)
        model.reset_states()
        predictions = model(input_eval)
        probabilities = predictions[-1][-1]
        sorted_probabilities = np.argsort(probabilities)
        likelihood = np.where(sorted_probabilities == pitch_class)
        return 12 - likelihood[0][0]

    def most_likely_classical(prior_pitch_classes, top_num):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.classical_interestingness_model
        return ListeningUtils.most_likely(model, prior_pitch_classes, top_num)

    def most_likely_c20(prior_pitch_classes, top_num):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.c20_interestingness_model
        return ListeningUtils.most_likely(model, prior_pitch_classes, top_num)

    def increasing_likeliness_ordered_pitch_classes(model, prior_pitch_classes):
        input_eval = tf.expand_dims(prior_pitch_classes, 0)
        model.reset_states()
        predictions = model(input_eval)
        probabilities = predictions[-1][-1]
        ordered_pitch_classes = list(reversed(np.argsort(probabilities)))
        return ordered_pitch_classes

    def annotate_composition_with_classical_interestingness(composition):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.classical_interestingness_model
        return ListeningUtils.annotate_composition_with_interestingness(composition, model)

    def annotate_composition_with_c20_interestingness(composition, track_nums=None):
        ListeningUtils.build_interestingness_models()
        model = ListeningUtils.c20_interestingness_model
        return ListeningUtils.annotate_composition_with_interestingness(composition, model)

    def annotate_composition_with_interestingness(composition, model):
        composition_lead_up_hash = AnalysisUtils.get_composition_lead_up_notes(composition)
        episode_lead_up_hash = AnalysisUtils.get_episode_lead_up_notes(composition)
        bar_lead_up_hash = AnalysisUtils.get_one_bar_lead_up_notes(composition)
        notes = composition.form.episodes[0].bars[0].note_sequences[6].notes

        ListeningUtils.annotate(model, composition_lead_up_hash, "composition", True)
        ListeningUtils.annotate(model, composition_lead_up_hash, "fifty", False, 50)
        ListeningUtils.annotate(model, episode_lead_up_hash, "episode", False)
        ListeningUtils.annotate(model, bar_lead_up_hash, "bar", False)

        ListeningUtils.calculate_bar_interestingness_profiles(composition, "composition")
        ListeningUtils.calculate_bar_interestingness_profiles(composition, "fifty")
        ListeningUtils.calculate_bar_interestingness_profiles(composition, "episode")
        ListeningUtils.calculate_bar_interestingness_profiles(composition, "bar")

    def annotate(model, lead_up_hash, lead_up_type, add_colour=False):
        for note in tqdm(lead_up_hash.keys()):
            if note.pitch is not None:
                if note.interestingness_profile is None:
                    note.interestingness_profile = {}
                pitch_class = MusicUtils.pitch_class(note.pitch)
                lead_up_pitches = []
                for lead_up_note in lead_up_hash[note]:
                    if lead_up_note.pitch is not None:
                        lead_up_pitches.append(MusicUtils.pitch_class(lead_up_note.pitch))
                if len(lead_up_pitches) > 0:
                    interestingness = ListeningUtils.predict_interestingness(model, lead_up_pitches, pitch_class)
                else:
                    interestingness = 6
                note.interestingness_profile[lead_up_type] = interestingness
                if add_colour and not (note.tie_type is None or note.tie_type == "start"):
                    if interestingness == 12:
                        note.score_colour = "red"
                    elif interestingness >= 9:
                        note.score_colour = "orange"
                    elif interestingness <= 4:
                        note.score_colour = "green"

    def calculate_bar_interestingness_profiles(composition, interestingness_type):
        for ep_num, episode in enumerate(composition.form.episodes):
            if episode.interestingness_profile is None:
                episode.interestingness_profile = {}
            episode_total = 0
            episode_count = 0
            for bar in episode.bars:
                if bar.interestingness_profile is None:
                    bar.interestingness_profile = {}
                bar_total_interestingness = 0
                bar_count = 0
                for note_sequence in bar.note_sequences:
                    if note_sequence.interestingness_profile is None:
                        note_sequence.interestingness_profile = {}
                    sequence_total_interestingness = 0
                    sequence_count = 0
                    for note in note_sequence.notes:
                        if note.interestingness_profile is not None and (note.tie_type is None or note.tie_type == "start"):
                            sequence_total_interestingness += note.interestingness_profile[interestingness_type]
                            sequence_count += 1
                    if sequence_count > 0:
                        note_sequence.interestingness_profile[interestingness_type] = 0 if sequence_count == 0 \
                            else sequence_total_interestingness/sequence_count
                        bar_total_interestingness += note_sequence.interestingness_profile[interestingness_type]
                        bar_count += 1
                bar.interestingness_profile[interestingness_type] = 0 if bar_count == 0 else bar_total_interestingness/bar_count
                episode_total += bar.interestingness_profile[interestingness_type]
                episode_count += 1
            episode.interestingness_profile[interestingness_type] = episode_total / episode_count
            print(ep_num, len(episode.bars), episode.interestingness_profile)
