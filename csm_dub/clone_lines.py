import json, sys, torch, soundfile as sf
from qwen_tts import Qwen3TTSModel
torch.set_num_threads(4)
cfg=json.load(open(sys.argv[1])); out=sys.argv[2]
ids = set(map(int, sys.argv[3].split(","))) if len(sys.argv)>3 else None
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
for L in cfg["lines"]:
    if ids and L["id"] not in ids: continue
    c=cfg["characters"][L["spk"]]
    w,sr = m.generate_voice_clone(text=L["text"], language="Japanese", ref_audio=f"{out}/ref_{L['spk']}.wav", ref_text=c["ref_text"])
    sf.write(f"{out}/line_{L['id']:02d}.wav", w[0], sr); print("line", L["id"], len(w[0])/sr, flush=True)
