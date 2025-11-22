import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './Phrases.css';

function LearnPhrases() {
  const [currentPhrase, setCurrentPhrase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();
  const apiUrl = process.env.REACT_APP_API_URL;

  // Audio / TTS state
  const audioRef = useRef(null);
  const [playerVisible, setPlayerVisible] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const fetchNextPhrase = async (currentId = 0) => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/phrase/next?current_phrase_id=${currentId}`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch next phrase');
      }
      
      const data = await response.json();
      setCurrentPhrase(data);
      setError('');
    } catch (err) {
      setError(err.message);
      if (err.message.includes('401')) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const cleanupAudioUrl = () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
  };

  const stopAudio = () => {
    try {
      const el = audioRef.current;
      if (el) {
        el.pause();
        el.currentTime = 0;
      }
    } catch {}
    setIsPlaying(false);
    setIsPaused(false);
    setPlayerVisible(false);
    cleanupAudioUrl();
  };

  const pauseAudio = () => {
    try {
      const el = audioRef.current;
      if (el) {
        el.pause();
        setIsPaused(true);
        setIsPlaying(false);
      }
    } catch {}
  };

  const resumeAudio = async () => {
    try {
      const el = audioRef.current;
      if (el) {
        await el.play();
        setIsPaused(false);
        setIsPlaying(true);
      }
    } catch {}
  };

  const playTTS = async (text) => {
    if (!text) return;
    setTtsLoading(true);
    setPlayerVisible(true);
    setIsPlaying(false);
    setIsPaused(false);
    try {
      const res = await fetch(`${apiUrl}/text_to_speech`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          accept: 'audio/mpeg',
        },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error('TTS failed');
      const blob = await res.blob();
      const playable = blob.type ? blob : new Blob([blob], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(playable);
      cleanupAudioUrl();
      setAudioUrl(url);
      const el = audioRef.current;
      if (el) {
        el.src = url;
        el.onended = () => {
          setIsPlaying(false);
          setIsPaused(false);
          setPlayerVisible(false);
          cleanupAudioUrl();
        };
        await el.play();
        setIsPlaying(true);
        setIsPaused(false);
      }
    } catch (e) {
      console.error(e);
      setPlayerVisible(false);
      alert('Не удалось озвучить текст');
    } finally {
      setTtsLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNextPhrase(0);
    }
  }, [user]);

  const handleNextPhrase = () => {
    if (currentPhrase) {
      fetchNextPhrase(currentPhrase.id_phrase);
    }
  };

  if (!user) {
    return <div>Пожалуйста, войдите в систему, чтобы учить фразы.</div>;
  }

  if (loading && !currentPhrase) {
    return <div>Загрузка фразы...</div>;
  }

  return (
    <div className="learn-container">
      <h2>Учить фразы</h2>
      
      {error && <div className="error">{error}</div>}
      
      {currentPhrase && (
        <div className="phrase-card">
          <div className="phrase-text">
            <h3>
              {currentPhrase.phrase}
              <button
                type="button"
                className="btn btn-link btn-sm p-0 ms-2 align-baseline"
                title="Озвучить фразу"
                onClick={() => playTTS(currentPhrase.phrase)}
                disabled={ttsLoading}
                style={{ verticalAlign: 'baseline', textDecoration: 'none' }}
              >
                {ttsLoading ? '…' : '🔊'}
              </button>
            </h3>
            <div className="translation">{currentPhrase.translation}</div>
          </div>
          
          <button 
            onClick={handleNextPhrase}
            className="next-button"
            disabled={loading}
          >
            {loading ? 'Загрузка...' : 'Следующая фраза'}
          </button>
        </div>
      )}
      {/* Hidden audio element */}
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Bottom floating control panel */}
      {playerVisible && (
        <div
          className="shadow bg-light border-top"
          style={{ position: 'fixed', left: 0, right: 0, bottom: 0, zIndex: 1050 }}
        >
          <div className="container py-2 d-flex align-items-center justify-content-between">
            <div className="d-flex align-items-center gap-2">
              <strong className="me-2" style={{ color: '#adb5bd' }}>Воспроизведение</strong>
              {ttsLoading && <span className="text-muted" style={{ color: '#ced4da' }}>Загрузка аудио…</span>}
            </div>
            <div className="btn-group">
              <button className="btn btn-outline-danger btn-sm" onClick={stopAudio} title="Стоп" aria-label="Стоп">⏹️</button>
              <button className="btn btn-outline-secondary btn-sm" onClick={pauseAudio} disabled={!isPlaying} title="Пауза" aria-label="Пауза">⏸️</button>
              <button className="btn btn-outline-primary btn-sm" onClick={resumeAudio} disabled={!isPaused} title="Продолжить" aria-label="Продолжить">▶️</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LearnPhrases;
