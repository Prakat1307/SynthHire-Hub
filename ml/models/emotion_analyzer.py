
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import io
import re
import base64

@dataclass
class EmotionFrame:

    timestamp: float
    facial_emotions: Dict[str, float] = field(default_factory=dict)
    dominant_emotion: str = "neutral"
    gaze_score: float = 0.0
    confidence_composite: float = 0.5

@dataclass  
class ProsodyChunk:

    timestamp_start: float
    timestamp_end: float
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    energy_mean: float = 0.0
    speech_rate_wpm: float = 0.0
    pause_ratio: float = 0.0
    filler_words: List[str] = field(default_factory=list)
    confidence_score: float = 0.5

@dataclass
class EmotionSummary:

    avg_confidence: float = 0.5
    confidence_trend: str = "stable"
    stress_peaks: List[Dict] = field(default_factory=list)
    total_filler_words: int = 0
    avg_eye_contact: float = 0.5
    avg_speech_rate_wpm: float = 130.0
    emotion_distribution: Dict[str, float] = field(default_factory=dict)

class FacialEmotionAnalyzer:

    def __init__(self):
        self.mp_face_mesh = None
        self._try_load_mediapipe()

    def _try_load_mediapipe(self):

        try:
            import mediapipe as mp
            self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
            self.mp = mp
            print("✅ MediaPipe Face Mesh loaded")
        except ImportError:
            print("⚠️ MediaPipe not available — facial analysis disabled")
            self.mp_face_mesh = None

    def analyze_frame(self, frame_rgb: np.ndarray, timestamp: float) -> EmotionFrame:

        if self.mp_face_mesh is None:
            return EmotionFrame(timestamp=timestamp)

        if frame_rgb.dtype != np.uint8:
            frame_rgb = (frame_rgb * 255).astype(np.uint8)

        results = self.mp_face_mesh.process(frame_rgb)

        if not results.multi_face_landmarks:
            return EmotionFrame(timestamp=timestamp)

        landmarks = results.multi_face_landmarks[0]

        gaze_score = self._estimate_gaze(landmarks, frame_rgb.shape)
        emotions = self._classify_emotions_from_landmarks(landmarks)
        dominant = max(emotions, key=emotions.get)
        confidence = self._calculate_confidence(emotions, gaze_score)

        return EmotionFrame(
            timestamp=timestamp,
            facial_emotions=emotions,
            dominant_emotion=dominant,
            gaze_score=gaze_score,
            confidence_composite=confidence,
        )

    def _estimate_gaze(self, landmarks, image_shape) -> float:

        h, w = image_shape[:2]

        try:
            
            left_iris = landmarks.landmark[468]
            right_iris = landmarks.landmark[473]
            nose_tip = landmarks.landmark[1]

            face_center_x = (left_iris.x + right_iris.x) / 2
            face_center_y = (left_iris.y + right_iris.y) / 2

            x_deviation = abs(face_center_x - 0.5)
            y_deviation = abs(face_center_y - 0.4)

            gaze_score = max(0.0, 1.0 - (x_deviation + y_deviation) * 2)
            return float(gaze_score)
        except (IndexError, AttributeError):
            return 0.5

    def _classify_emotions_from_landmarks(self, landmarks) -> Dict[str, float]:

        emotions = {
            "neutral": 0.5,
            "happy": 0.1,
            "surprise": 0.05,
            "sad": 0.05,
            "angry": 0.05,
            "fear": 0.05,
            "disgust": 0.05,
        }

        try:
            
            upper_lip = landmarks.landmark[13]
            lower_lip = landmarks.landmark[14]
            mouth_open = abs(upper_lip.y - lower_lip.y)

            left_brow_inner = landmarks.landmark[70]
            left_eye_top = landmarks.landmark[159]
            brow_raise = abs(left_brow_inner.y - left_eye_top.y)

            left_eye_upper = landmarks.landmark[159]
            left_eye_lower = landmarks.landmark[145]
            eye_open = abs(left_eye_upper.y - left_eye_lower.y)

            mouth_left = landmarks.landmark[61]
            mouth_right = landmarks.landmark[291]
            mouth_center = landmarks.landmark[0]
            smile_factor = (mouth_left.y + mouth_right.y) / 2 - mouth_center.y

            if mouth_open > 0.03:
                emotions["surprise"] += 0.3
                emotions["neutral"] -= 0.15

            if brow_raise > 0.04:
                emotions["surprise"] += 0.2

            if smile_factor > 0.02:
                emotions["happy"] += 0.4
                emotions["neutral"] += 0.1

            if eye_open < 0.02:
                emotions["sad"] += 0.2
                emotions["tired"] = 0.3

        except (IndexError, AttributeError):
            pass

        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v / total for k, v in emotions.items()}

        return emotions

    def _calculate_confidence(self, emotions: Dict[str, float], gaze: float) -> float:

        neutral_happy = emotions.get("neutral", 0) + emotions.get("happy", 0)
        negative = (
            emotions.get("fear", 0) + emotions.get("angry", 0) + 
            emotions.get("sad", 0) + emotions.get("disgust", 0)
        )

        emotion_confidence = min(1.0, neutral_happy - negative * 0.5 + 0.3)
        
        confidence = float(np.clip(emotion_confidence * 0.6 + gaze * 0.4, 0.0, 1.0))
        return confidence

class AudioProsodyAnalyzer:

    FILLER_WORDS = {
        "um", "uh", "like", "you know", "so", "basically", 
        "actually", "literally", "right", "well", "okay",
        "I mean", "you see", "sort of", "kind of", "pretty much"
    }

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self._try_load_librosa()

    def _try_load_librosa(self):

        try:
            import librosa
            self.librosa = librosa
            print("✅ Librosa loaded for prosody analysis")
        except ImportError:
            self.librosa = None
            print("⚠️ Librosa not available — prosody analysis limited")

    def analyze_audio_chunk(
        self,
        audio_bytes: bytes,
        timestamp_start: float,
        timestamp_end: float,
    ) -> ProsodyChunk:

        if self.librosa is None:
            return ProsodyChunk(
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
            )

        try:
            
            audio_array, sr = self.librosa.load(
                io.BytesIO(audio_bytes),
                sr=self.sample_rate,
                mono=True,
            )

            pitches, magnitudes = self.librosa.piptrack(y=audio_array, sr=sr)
            pitch_values = pitches[pitches > 0]
            pitch_mean = float(np.mean(pitch_values)) if len(pitch_values) > 0 else 0.0
            pitch_std = float(np.std(pitch_values)) if len(pitch_values) > 0 else 0.0

            rms = self.librosa.feature.rms(y=audio_array)
            energy_mean = float(np.mean(rms))

            onset_env = self.librosa.onset.onset_strength(y=audio_array, sr=sr)
            tempo = self.librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
            estimated_wpm = float(tempo[0]) if len(tempo) > 0 else 130.0

            intervals = self.librosa.effects.split(audio_array, top_db=30)
            speech_duration = sum(end - start for start, end in intervals) / sr
            total_duration = len(audio_array) / sr
            pause_ratio = 1.0 - (speech_duration / max(total_duration, 0.01))

            pitch_stability = 1.0 / (1.0 + pitch_std / max(pitch_mean, 1.0))
            energy_level = min(1.0, energy_mean * 10)
            confidence = float(np.clip(
                pitch_stability * 0.4 + 
                energy_level * 0.3 + 
                (1 - pause_ratio) * 0.3,
                0.0, 1.0
            ))

            return ProsodyChunk(
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
                pitch_mean=pitch_mean,
                pitch_std=pitch_std,
                energy_mean=energy_mean,
                speech_rate_wpm=estimated_wpm,
                pause_ratio=float(pause_ratio),
                confidence_score=confidence,
            )
        except Exception as e:
            print(f"⚠️ Prosody analysis error: {e}")
            return ProsodyChunk(
                timestamp_start=timestamp_start,
                timestamp_end=timestamp_end,
            )

    def count_filler_words(self, transcript: str) -> Tuple[int, List[str]]:

        words = transcript.lower()
        found = []
        count = 0

        for filler in sorted(self.FILLER_WORDS, key=len, reverse=True):
            if filler in words:
                occurrences = words.count(filler)
                count += occurrences
                found.extend([filler] * occurrences)
                words = words.replace(filler, " ")

        single_words = words.split()
        for word in single_words:
            if word in self.FILLER_WORDS:
                count += 1
                found.append(word)

        return count, found

    def calculate_speech_rate(self, transcript: str, duration_seconds: float) -> float:

        word_count = len(transcript.split())
        if duration_seconds <= 0:
            return 0.0
        return (word_count / duration_seconds) * 60

class EmotionAnalysisPipeline:

    def __init__(self):
        self.facial_analyzer = FacialEmotionAnalyzer()
        self.prosody_analyzer = AudioProsodyAnalyzer()
        self.emotion_frames: List[EmotionFrame] = []
        self.prosody_chunks: List[ProsodyChunk] = []
        self.filler_count = 0
        self.total_transcript_duration = 0.0

    def process_video_frame(self, frame_rgb: np.ndarray, timestamp: float):

        emotion = self.facial_analyzer.analyze_frame(frame_rgb, timestamp)
        self.emotion_frames.append(emotion)

    def process_audio_chunk(self, audio_bytes: bytes, start: float, end: float):

        prosody = self.prosody_analyzer.analyze_audio_chunk(audio_bytes, start, end)
        self.prosody_chunks.append(prosody)

    def process_transcript(self, transcript: str, duration_seconds: float):

        self.total_transcript_duration += duration_seconds
        count, fillers = self.prosody_analyzer.count_filler_words(transcript)
        self.filler_count += count
        wpm = self.prosody_analyzer.calculate_speech_rate(transcript, duration_seconds)
        return {"filler_count": count, "fillers": fillers, "wpm": wpm}

    def get_behavioral_scores(self) -> Dict[str, float]:

        facial_confidences = [f.confidence_composite for f in self.emotion_frames] if self.emotion_frames else [0.5]
        avg_facial = np.mean(facial_confidences)

        prosody_confidences = [p.confidence_score for p in self.prosody_chunks] if self.prosody_chunks else [0.5]
        avg_prosody = np.mean(prosody_confidences)

        gaze_scores = [f.gaze_score for f in self.emotion_frames] if self.emotion_frames else [0.5]
        avg_gaze = np.mean(gaze_scores)

        wpm_values = [p.speech_rate_wpm for p in self.prosody_chunks if p.speech_rate_wpm > 0]
        if wpm_values:
            wpm_consistency = 1.0 / (1.0 + np.std(wpm_values) / max(np.mean(wpm_values), 1.0))
        else:
            wpm_consistency = 0.5

        filler_penalty = max(0.0, 1.0 - self.filler_count * 0.03)

        overall_confidence = avg_facial * 0.3 + avg_prosody * 0.4 + avg_gaze * 0.2 + filler_penalty * 0.1

        return {
            "technical_correctness": float(overall_confidence * 0.7 + 0.3),
            "problem_decomposition": float(overall_confidence * 0.6 + 0.4),
            "communication_clarity": float(avg_prosody * 0.4 + wpm_consistency * 0.3 + filler_penalty * 0.3),
            "handling_ambiguity": float(overall_confidence * 0.5 + 0.5),
            "edge_case_awareness": float(overall_confidence * 0.5 + 0.5),
            "time_management": float(wpm_consistency * 0.5 + 0.5),
            "collaborative_signals": float(avg_gaze * 0.4 + avg_prosody * 0.3 + 0.3),
            "growth_mindset": float(overall_confidence * 0.6 + 0.4),
        }

    def get_summary(self) -> EmotionSummary:

        confidences = [f.confidence_composite for f in self.emotion_frames]

        if len(confidences) >= 10:
            first_half = np.mean(confidences[: len(confidences) // 2])
            second_half = np.mean(confidences[len(confidences) // 2 :])
            if second_half - first_half > 0.1:
                trend = "improving"
            elif first_half - second_half > 0.1:
                trend = "declining"
            elif np.std(confidences) > 0.2:
                trend = "volatile"
            else:
                trend = "stable"
        else:
            trend = "stable"

        stress_peaks = []
        for i, conf in enumerate(confidences):
            if conf < 0.3:
                stress_peaks.append({
                    "frame_index": i,
                    "timestamp": self.emotion_frames[i].timestamp if i < len(self.emotion_frames) else 0,
                    "stress_level": float(1.0 - conf),
                })

        emotion_counts: Dict[str, int] = {}
        for frame in self.emotion_frames:
            dom = frame.dominant_emotion
            emotion_counts[dom] = emotion_counts.get(dom, 0) + 1
        total_frames = max(len(self.emotion_frames), 1)
        emotion_dist = {k: v / total_frames for k, v in emotion_counts.items()}

        wpm_values = [p.speech_rate_wpm for p in self.prosody_chunks if p.speech_rate_wpm > 0]
        avg_wpm = float(np.mean(wpm_values)) if wpm_values else 130.0

        return EmotionSummary(
            avg_confidence=float(np.mean(confidences)) if confidences else 0.5,
            confidence_trend=trend,
            stress_peaks=stress_peaks[:5],
            total_filler_words=self.filler_count,
            avg_eye_contact=float(np.mean([f.gaze_score for f in self.emotion_frames])) if self.emotion_frames else 0.5,
            avg_speech_rate_wpm=avg_wpm,
            emotion_distribution=emotion_dist,
        )

    def reset(self):

        self.emotion_frames = []
        self.prosody_chunks = []
        self.filler_count = 0
        self.total_transcript_duration = 0.0

    def get_frame_count(self) -> int:

        return len(self.emotion_frames)

    def get_chunk_count(self) -> int:

        return len(self.prosody_chunks)

if __name__ == "__main__":
    pipeline = EmotionAnalysisPipeline()
    
    dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    pipeline.process_video_frame(dummy_frame, 0.0)
    
    dummy_audio = b'\x00' * 1000
    pipeline.process_audio_chunk(dummy_audio, 0.0, 1.0)
    
    result = pipeline.process_transcript("Um, I think this solution works.", 2.0)
    print(f"Transcript result: {result}")
    
    scores = pipeline.get_behavioral_scores()
    print(f"Behavioral scores: {scores}")
    
    summary = pipeline.get_summary()
    print(f"Emotion summary: {summary}")