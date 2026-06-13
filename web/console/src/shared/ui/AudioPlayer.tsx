import { useEffect, useRef, useState } from "react";

interface AudioPlayerProps {
  src: string;
  label?: string;
  className?: string;
}

function fmt(s: number): string {
  if (!Number.isFinite(s) || s < 0) return "0:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ src, label, className }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [playing, setPlaying] = useState(false);
  const [current, setCurrent] = useState(0);
  const [duration, setDuration] = useState(0);

  // biome-ignore lint/correctness/useExhaustiveDependencies: src is a prop, re-attach listeners when src changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onLoadedMetadata = () => setDuration(audio.duration);
    const onTimeUpdate = () => setCurrent(audio.currentTime);
    const onPlay = () => setPlaying(true);
    const onPause = () => setPlaying(false);
    const onEnded = () => setPlaying(false);

    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("play", onPlay);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("ended", onEnded);

    audio.play()?.catch(() => {});

    return () => {
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("play", onPlay);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("ended", onEnded);
    };
  }, [src]);

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play()?.catch(() => {});
    } else {
      audio.pause();
    }
  }

  function seek(e: React.ChangeEvent<HTMLInputElement>) {
    const audio = audioRef.current;
    if (!audio) return;
    const value = Number(e.target.value);
    audio.currentTime = value;
    setCurrent(value);
  }

  const pct = duration > 0 ? (current / duration) * 100 : 0;

  return (
    <div
      className={`audio-player ${className ?? ""}`}
      aria-label={label ?? "Audio output"}
    >
      {/* Hidden actual audio element */}
      {/* biome-ignore lint/a11y/useMediaCaption: dynamically synthesized speech has no caption track */}
      <audio ref={audioRef} src={src} preload="auto" />
      {/* Play/Pause button */}
      <button
        type="button"
        className="audio-play-btn"
        onClick={toggle}
        aria-label={playing ? "Pause" : "Play"}
      >
        {playing ? (
          <svg
            width="10"
            height="12"
            viewBox="0 0 10 12"
            fill="currentColor"
            aria-hidden="true"
          >
            <rect x="0" y="0" width="3" height="12" rx="1" />
            <rect x="7" y="0" width="3" height="12" rx="1" />
          </svg>
        ) : (
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M2 1.5l9 4.5-9 4.5z" />
          </svg>
        )}
      </button>
      {/* Scrubber */}
      <div className="audio-progress">
        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.05}
          value={current}
          onChange={seek}
          className="audio-scrubber"
          aria-label="Seek"
          style={{ "--pct": `${pct}%` } as React.CSSProperties}
        />
      </div>
      {/* Time */}
      <span className="audio-time" aria-live="off">
        {fmt(current)} / {fmt(duration)}
      </span>
    </div>
  );
}
