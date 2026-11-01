import json, sys, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
cfg=json.load(open(sys.argv[1])); out=sys.argv[2]
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
for k,c in cfg["characters"].items():
    w,sr = m.generate_voice_design(text=c["ref_text"], instruct=c["instruct"], language="Japanese")
    sf.write(f"{out}/ref_{k}.wav", w[0], sr); print("ref", k, flush=True)
