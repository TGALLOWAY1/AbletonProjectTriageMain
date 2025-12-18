import { useEffect, useRef, useState } from 'react'
import { Play, Pause, Volume2, VolumeX } from 'lucide-react'
import WaveSurfer from 'wavesurfer.js'
import { audioApi } from '../services/api'
import clsx from 'clsx'

interface AudioPlayerProps {
  projectId: number
}

export default function AudioPlayer({ projectId }: AudioPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const wavesurferRef = useRef<WaveSurfer | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Clean up previous instance
    if (wavesurferRef.current) {
      wavesurferRef.current.destroy()
    }

    setLoading(true)
    setError(null)

    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#4a4a4a',
      progressColor: '#ff764d',
      cursorColor: '#ff764d',
      barWidth: 2,
      barRadius: 2,
      barGap: 2,
      height: 60,
      normalize: true,
      backend: 'WebAudio',
    })

    wavesurferRef.current = wavesurfer

    // Load audio
    const audioUrl = audioApi.getPreviewUrl(projectId)
    wavesurfer.load(audioUrl)

    // Event handlers
    wavesurfer.on('ready', () => {
      setLoading(false)
      setDuration(wavesurfer.getDuration())
    })

    wavesurfer.on('audioprocess', () => {
      setCurrentTime(wavesurfer.getCurrentTime())
    })

    wavesurfer.on('play', () => setIsPlaying(true))
    wavesurfer.on('pause', () => setIsPlaying(false))
    wavesurfer.on('finish', () => setIsPlaying(false))

    wavesurfer.on('error', (err) => {
      setLoading(false)
      setError('Failed to load audio')
      console.error('WaveSurfer error:', err)
    })

    return () => {
      wavesurfer.destroy()
    }
  }, [projectId])

  const togglePlay = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause()
    }
  }

  const toggleMute = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setMuted(!isMuted)
      setIsMuted(!isMuted)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (error) {
    return (
      <div className="p-4 bg-ableton-bg rounded-lg text-center text-sm text-ableton-text-muted">
        {error}
      </div>
    )
  }

  return (
    <div className="bg-ableton-bg rounded-lg p-4">
      {/* Waveform */}
      <div 
        ref={containerRef} 
        className={clsx(
          'mb-3 rounded overflow-hidden',
          loading && 'animate-pulse bg-ableton-surface-light'
        )}
        style={{ minHeight: 60 }}
      />

      {/* Controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          disabled={loading}
          className={clsx(
            'p-2 rounded-lg transition-colors',
            'bg-ableton-accent hover:bg-ableton-accent-hover text-white',
            loading && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isPlaying ? (
            <Pause className="w-4 h-4" />
          ) : (
            <Play className="w-4 h-4" />
          )}
        </button>

        <button
          onClick={toggleMute}
          className="p-2 rounded-lg bg-ableton-surface hover:bg-ableton-surface-light transition-colors"
        >
          {isMuted ? (
            <VolumeX className="w-4 h-4 text-ableton-text-muted" />
          ) : (
            <Volume2 className="w-4 h-4 text-ableton-text-muted" />
          )}
        </button>

        <div className="flex-1" />

        <span className="text-xs font-mono text-ableton-text-muted">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>
    </div>
  )
}

