import importlib, warnings
warnings.filterwarnings("ignore")
for m in ['resemblyzer','torch','noisereduce','librosa','faster_whisper','funasr','pypinyin','zhconv','speechbrain','pyloudnorm','scipy','numpy']:
    try:
        mod = importlib.import_module(m); print(m, getattr(mod, '__version__', 'ok'))
    except Exception as e:
        print(m, 'MISSING', type(e).__name__)
