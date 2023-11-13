#@title MTGListeningModelUtils Class

from ParleyV2.Utils.MarginUtils import *
from ParleyV2.Utils.MidiUtils import *
from scipy.io import wavfile

class MTGListeningModelUtils:

  full_tag_hash = {"smooth": "mtg_jamendo_genre__easylistening",
              "jazzy": "mtg_jamendo_genre__jazz",
              "blues": "mtg_jamendo_genre__blues",
              "sad": "mtg_jamendo_moodtheme__sad",
              "happy": "mtg_jamendo_moodtheme__happy",
              "melancholic": "mtg_jamendo_moodtheme__melancholic",
              "deep": "mtg_jamendo_moodtheme__deep",
              "inspiring": "mtg_jamendo_moodtheme__inspiring",
              "upbeat": "mtg_jamendo_moodtheme__upbeat"}

  def get_wavfile_duration(wav_filepath):
    sample_rate, data = wavfile.read(wav_filepath)
    len_data = len(data)
    return len_data/sample_rate

  def get_embeddings(wav_filepath):
    sampleRate = int(79520/2) # 79520 gets five samples per bar (roughly)
    audio = MonoLoader(filename=wav_filepath, sampleRate=sampleRate)()
    return embeddings_model(audio)

  def get_activations(wav_filepath):
    duration = MTGListeningModelUtils.get_wavfile_duration(wav_filepath)
    start_s = 0
    all_activations = []
    embeddings = MTGListeningModelUtils.get_embeddings(wav_filepath)
    activations = MTGListeningModelUtils.get_activations_from_embeddings(embeddings)
    return activations

  def get_activations_from_embeddings(embeddings):
    activation_lists = [[] for i in range(0, len(embeddings))]
    for model_id in models_hash:
      st = time.time()
      model_output = models_hash[model_id](embeddings)
      for ind, activation in enumerate(model_output):
        activation_lists[ind].extend(model_output[ind])
    return activation_lists

  def add_bar_activations(composition, performance_spec, soundfont_filepath, fluidsynth_cli):
      midi_file = MidiUtils.get_midi_file(composition, performance_spec, soundfont_filepath)
      midi_filepath = "temp.mid"
      midi_file.save(midi_filepath)
      wav_filepath = f"temp.wav"
      process = subprocess.Popen(f"{fluidsynth_cli} {soundfont_filepath} --quiet --no-shell {midi_filepath} -T wav -F {wav_filepath} > /dev/null", shell=True)
      process.wait()

      activations_list = MTGListeningModelUtils.get_activations(wav_filepath)
      wav_duration = MTGListeningModelUtils.get_wavfile_duration(wav_filepath)
      slice_ms = wav_duration/len(activations_list)

      for bar in composition.bars:
        bar.mtg_activation_vectors = []
        bar.mtg_activations_hash = {}
        bar.mtg_activation_highlights = []

      ms = 0
      for activations_v in activations_list:
        for bar in composition.bars:
          if ms >= bar.start_tick/960 and ms <= bar.end_tick/960:
            bar.mtg_activation_vectors.append(activations_v)
        ms += slice_ms

      for bar in composition.bars:
        for tag in all_activation_tags:
          tag_ind = all_activation_tags.index(tag)
          vs_for_bar = [v[tag_ind] for v in bar.mtg_activation_vectors]
          if len(vs_for_bar) > 0:
            bar.mtg_activations_hash[tag] = np.mean(vs_for_bar)
          else:
            bar.mtg_activations_hash[tag] = 0
      os.remove("temp.mid")
      os.remove("temp.wav")

  def get_full_tag(short_tag):
      return MTGListeningModelUtils.full_tag_hash[short_tag]

  def get_short_tag(full_tag):
      for key in MTGListeningModelUtils.full_tag_hash.keys():
        if MTGListeningModelUtils.full_tag_hash[key] == full_tag:
          return key
      return None
