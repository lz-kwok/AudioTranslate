import numpy as np
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Subtle emotion → Edge-TTS prosody parameter mapping
# pitch unit: Hz  |  rate/volume unit: %
# ─────────────────────────────────────────────────────────────
EMOTION_PARAMS = {
    "excited": {"rate": "+20%", "pitch": "+50Hz", "volume": "+10%"},
    "happy":   {"rate": "+12%", "pitch": "+30Hz", "volume": "+5%"},
    "angry":   {"rate": "+15%", "pitch": "+40Hz", "volume": "+15%"},
    "sad":     {"rate": "-15%", "pitch": "-30Hz", "volume": "-5%"},
    "fearful": {"rate": "+10%", "pitch": "+20Hz", "volume": "-5%"},
    "neutral": {"rate": "+0%",  "pitch": "+0Hz",  "volume": "+0%"},
}

# ─────────────────────────────────────────────────────────────
# Chinese text sentiment keyword banks
# ─────────────────────────────────────────────────────────────
_EXCITED_KW  = ["太棒了", "难以置信", "真的吗", "太厉害", "震惊", "惊人", "!"]
_HAPPY_KW    = ["很好", "非常好", "感谢", "喜欢", "高兴", "开心", "成功", "完美", "真的", "棒"]
_ANGRY_KW    = ["不可能", "凭什么", "绝对不", "为什么", "必须", "一定要", "不行", "不公平"]
_SAD_KW      = ["可惜", "遗憾", "失去", "离开", "结束", "难过", "伤心", "哭"]
_NEGATIVE_KW = ["但是", "问题", "失败", "不好", "担心", "差", "糟糕", "困难", "错误"]


class EmotionAnalyzer:
    """
    Two-layer emotion analyzer.

    Layer 1 – Acoustic: librosa acoustic features → arousal / valence → emotion label.
    Layer 2 – Text:     Chinese keyword sentiment → emotion label.
    Merge:  acoustic is primary; text corrects neutral or polarity flips.
    """

    # ── Public API ──────────────────────────────────────────────

    def analyze(self, audio_clip_path: str, text: str = "") -> dict:
        """
        Returns a dict:
            emotion  – str label
            arousal  – float 0‥1
            valence  – float 0‥1
            rate     – SSML rate  string, e.g. '+12%'
            pitch    – SSML pitch string, e.g. '+30Hz'
            volume   – SSML vol   string, e.g. '+5%'
        """
        acoustic = self._acoustic_analysis(audio_clip_path)
        text_emo = self._text_sentiment(text)
        emotion  = self._merge(acoustic, text_emo)

        params = EMOTION_PARAMS.get(emotion, EMOTION_PARAMS["neutral"])
        return {
            "emotion": emotion,
            "arousal": acoustic["arousal"],
            "valence": acoustic["valence"],
            "rate":    params["rate"],
            "pitch":   params["pitch"],
            "volume":  params["volume"],
        }

    # ── Layer 1: Acoustic ────────────────────────────────────────

    def _acoustic_analysis(self, audio_path: str) -> dict:
        try:
            import librosa  # already in requirements
            y, sr = librosa.load(audio_path, sr=16000)

            if len(y) < sr * 0.3:          # < 0.3 s → unreliable
                return _neutral_acoustic()

            # — Pitch (F0) via PYIN —
            f0, voiced_flag, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr)
            f0_voiced = f0[voiced_flag] if voiced_flag is not None else np.array([])
            pitch_mean = float(np.mean(f0_voiced)) if len(f0_voiced) > 3 else 150.0
            pitch_std  = float(np.std(f0_voiced))  if len(f0_voiced) > 3 else 20.0

            # — Energy (RMS) —
            rms = librosa.feature.rms(y=y)[0]
            energy = float(np.mean(rms))

            # — Zero-Crossing Rate (proxy for speech rate / noise) —
            zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))

            # — Normalise to [0, 1] —
            energy_n    = min(energy   / 0.10, 1.0)   # 0.10 ≈ loud speech
            pitch_std_n = min(pitch_std / 80.0, 1.0)  # 80 Hz std ≈ very expressive
            zcr_n       = min(zcr      / 0.15, 1.0)

            # Arousal: energy (40 %) + pitch variability (40 %) + speech rate (20 %)
            arousal = energy_n * 0.4 + pitch_std_n * 0.4 + zcr_n * 0.2
            arousal = round(float(np.clip(arousal, 0.0, 1.0)), 2)

            # Valence: higher pitch mean → more positive (rough but practical)
            valence = (pitch_mean - 80.0) / 200.0   # 80‥280 Hz → 0‥1
            valence = round(float(np.clip(valence, 0.0, 1.0)), 2)

            emotion = _map_to_emotion(arousal, valence)
            return {"emotion": emotion, "arousal": arousal, "valence": valence}

        except Exception as e:
            logger.debug(f"Acoustic analysis failed ({audio_path}): {e}")
            return _neutral_acoustic()

    # ── Layer 2: Text sentiment ──────────────────────────────────

    def _text_sentiment(self, text: str) -> str:
        if not text:
            return "neutral"

        # Score each category
        scores = {
            "excited":  sum(1 for kw in _EXCITED_KW  if kw in text),
            "happy":    sum(1 for kw in _HAPPY_KW    if kw in text),
            "angry":    sum(1 for kw in _ANGRY_KW    if kw in text),
            "sad":      sum(1 for kw in _SAD_KW      if kw in text),
            "negative": sum(1 for kw in _NEGATIVE_KW if kw in text),
        }

        # Exclamation / question boosts
        if "！" in text or "!" in text:
            scores["excited"] += 1
        if "？" in text or "?" in text:
            scores["angry"] += 0.5

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "neutral"
        if best == "negative":
            return "sad"
        return best

    # ── Merge ────────────────────────────────────────────────────

    def _merge(self, acoustic: dict, text_emo: str) -> str:
        acou = acoustic["emotion"]
        if acou == text_emo:
            return acou
        # Acoustic neutral → text has signal
        if acou == "neutral" and text_emo != "neutral":
            return text_emo
        # Text neutral → keep acoustic (subtle cues)
        if text_emo == "neutral":
            return acou
        # Polarity conflict → trust text (cleaner semantic signal)
        pos = {"happy", "excited"}
        neg = {"sad", "angry", "fearful"}
        if (acou in pos and text_emo in neg) or (acou in neg and text_emo in pos):
            return text_emo
        # Same polarity, different shade → keep acoustic
        return acou


# ── Helpers ──────────────────────────────────────────────────────

def _neutral_acoustic() -> dict:
    return {"emotion": "neutral", "arousal": 0.5, "valence": 0.5}


def _map_to_emotion(arousal: float, valence: float) -> str:
    if arousal > 0.70 and valence > 0.60:
        return "excited"
    if arousal > 0.55 and valence > 0.50:
        return "happy"
    if arousal > 0.60 and valence < 0.40:
        return "angry"
    if arousal < 0.35 and valence < 0.45:
        return "sad"
    if arousal > 0.50 and valence < 0.50:
        return "fearful"
    return "neutral"
