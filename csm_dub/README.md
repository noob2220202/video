# 체인소맨 레제편 예고편 — 대사 재더빙 파이프라인

1. Demucs로 원본 오디오를 `vocals` / `no_vocals`로 분리
2. faster-whisper(medium) + 화면 자막으로 대사 10개·화자·타이밍 확정 → `lines.json`
3. `make_refs.py`: Qwen3-TTS VoiceDesign으로 캐릭터별 기준 목소리 생성 (텍스트 묘사 기반, 원 성우 복제 아님)
4. `clone_lines.py`: Qwen3-TTS Base로 기준 목소리를 복제해 각 대사 생성 (`ids` 인자로 특정 줄만 재생성)
5. `mix.py`: 대사 구간만 원본 보이스 제거, 새 대사를 슬롯에 맞춰 배치·음량 매칭·리버브 후 영상과 합성

패러디로 바꾸려면 `lines.json`의 `text`만 고치고 4→5단계 다시 실행.
