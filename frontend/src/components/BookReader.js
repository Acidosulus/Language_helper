import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

function BookReader() {
  const { id_book } = useParams();
  const apiUrl = process.env.REACT_APP_API_URL;
  const [bookMeta, setBookMeta] = useState(null); // {id_book, book_name, current_paragraph, Min_Paragraph_Number, Max_Paragraph_Number}
  const [startParagraph, setStartParagraph] = useState(null);
  const [paragraphs, setParagraphs] = useState([]); // array of { id_paragraph, sentences[] }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Audio player state
  const audioRef = useRef(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [playerVisible, setPlayerVisible] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);

  // Derived progress data
  const progressInfo = useMemo(() => {
    if (!bookMeta) return { index: null, total: null, percent: null };
    const min = Number(bookMeta.Min_Paragraph_Number ?? 0);
    const max = Number(bookMeta.Max_Paragraph_Number ?? 0);
    const total = max >= min ? (max - min + 1) : 0;
    const currentAbs = startParagraph != null ? Number(startParagraph) : Number(bookMeta.current_paragraph ?? min);
    if (!total || currentAbs == null) return { index: null, total, percent: null };
    const index = currentAbs >= min && currentAbs <= max ? (currentAbs - min + 1) : Math.max(1, Math.min(total, currentAbs - min + 1));
    const raw = (index / total) * 100;
    const percent = Math.max(0, Math.min(100, raw));
    return { index, total, percent };
  }, [bookMeta, startParagraph]);

  // Selects the text content of the clicked sentence span
  const handleSentenceClick = (e) => {
    try {
      const node = e.currentTarget;
      const selection = window.getSelection && window.getSelection();
      if (!node || !selection) return;
      const range = document.createRange();
      range.selectNodeContents(node);
      selection.removeAllRanges();
      selection.addRange(range);
    } catch (err) {
      // no-op if selection API not available
      // console.warn('Selection failed', err);
    }
  };

  const cleanupAudioUrl = () => {
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setAudioUrl(null);
  };

  const stopAudio = () => {
    try {
      const el = audioRef.current;
      if (el) {
        el.pause();
        el.currentTime = 0;
      }
    } catch (e) {
      // ignore
    }
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
    } catch (e) {
      // ignore
    }
  };

  const resumeAudio = async () => {
    try {
      const el = audioRef.current;
      if (el) {
        await el.play();
        setIsPaused(false);
        setIsPlaying(true);
      }
    } catch (e) {
      // ignore
    }
  };

  const playSentenceTTS = async (text) => {
    if (!text) return;
    setTtsLoading(true);
    setPlayerVisible(true);
    setIsPlaying(false);
    setIsPaused(false);
    try {
      // Request TTS from backend
      const res = await fetch(`${apiUrl}/text_to_speech`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          accept: 'audio/mpeg',
        },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(`TTS failed: ${res.status} ${t}`);
      }
      const blob = await res.blob();
      // Ensure it's mp3
      const playable = blob.type ? blob : new Blob([blob], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(playable);
      cleanupAudioUrl();
      setAudioUrl(url);
      const el = audioRef.current;
      if (el) {
        el.src = url;
        // Attach end handler
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
      alert('Не удалось выполнить озвучку предложения.');
    } finally {
      setTtsLoading(false);
    }
  };

  // Fetch meta including current position
  useEffect(() => {
    const fetchMeta = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiUrl}/book?book_id=${id_book}`, { credentials: 'include' });
        if (!res.ok) throw new Error('Failed to load book info');
        const data = await res.json();
        setBookMeta(data);
        const initial = Number(data?.current_paragraph) || Number(data?.Min_Paragraph_Number);
        setStartParagraph(initial);
      } catch (e) {
        console.error(e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchMeta();
  }, [apiUrl, id_book]);

  // Helper to fetch one paragraph and sort sentences by id_sentence
  const fetchParagraph = async (id_paragraph) => {
    const res = await fetch(`${apiUrl}/book/paragraph?id_book=${id_book}&id_paragraph=${id_paragraph}`, { credentials: 'include' });
    if (!res.ok) throw new Error(`Failed to load paragraph ${id_paragraph}`);
    const data = await res.json();
    const sorted = Array.isArray(data) ? [...data].sort((a, b) => (a.id_sentence || 0) - (b.id_sentence || 0)) : [];
    return { id_paragraph: Number(id_paragraph), sentences: sorted };
  };

  // Load 5 paragraphs window starting at startParagraph
  useEffect(() => {
    const loadWindow = async () => {
      if (!bookMeta || startParagraph == null) return;
      setLoading(true);
      setError(null);
      try {
        const start = Math.max(bookMeta.Min_Paragraph_Number, startParagraph);
        const endExclusive = Math.min(start + 5, bookMeta.Max_Paragraph_Number + 1);
        const ids = [];
        for (let p = start; p < endExclusive; p++) ids.push(p);
        const results = [];
        for (const pid of ids) {
          // sequential to keep it simple and avoid overloading API
          // could be parallelized if backend supports
          // eslint-disable-next-line no-await-in-loop
          const para = await fetchParagraph(pid);
          results.push(para);
        }
        setParagraphs(results);
      } catch (e) {
        console.error(e);
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    loadWindow();
  }, [bookMeta, startParagraph]);

  const atStart = useMemo(() => {
    if (!bookMeta || startParagraph == null) return true;
    return startParagraph <= bookMeta.Min_Paragraph_Number;
  }, [bookMeta, startParagraph]);

  const atEnd = useMemo(() => {
    if (!bookMeta || startParagraph == null) return false;
    return startParagraph + 5 > bookMeta.Max_Paragraph_Number;
  }, [bookMeta, startParagraph]);

  // Refresh only lightweight stats (e.g., paragraphs_read_24h) after saving position
  const refreshBookStats = async () => {
    try {
      const res = await fetch(`${apiUrl}/book?book_id=${id_book}`, { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      setBookMeta((prev) => ({
        ...(prev || {}),
        // keep previous known fields, but refresh dynamic stats
        paragraphs_read_24h: data?.paragraphs_read_24h ?? prev?.paragraphs_read_24h,
        Min_Paragraph_Number: data?.Min_Paragraph_Number ?? prev?.Min_Paragraph_Number,
        Max_Paragraph_Number: data?.Max_Paragraph_Number ?? prev?.Max_Paragraph_Number,
        // optionally sync current_paragraph from server if needed
        current_paragraph: data?.current_paragraph ?? prev?.current_paragraph,
      }));
    } catch (_) {
      // ignore silent refresh errors
    }
  };

  const savePosition = async (newStart) => {
    try {
      setSaving(true);
      const res = await fetch(`${apiUrl}/book/paragraph`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          accept: 'application/json',
        },
        body: JSON.stringify({ id_book: Number(id_book), id_new_paragraph: Number(newStart) }),
      });
      if (!res.ok) {
        // Don't block UI, but log error
        const txt = await res.text();
        console.error('Failed to save position', res.status, txt);
      } else {
        // After a successful save, refresh stats so the 24h counter updates without full reload
        refreshBookStats();
      }
    } catch (e) {
      console.error('Error saving position', e);
    } finally {
      setSaving(false);
    }
  };

  const goPrev = async () => {
    if (!bookMeta || startParagraph == null) return;
    const newStart = Math.max(bookMeta.Min_Paragraph_Number, startParagraph - 5);
    setStartParagraph(newStart);
    savePosition(newStart);
    try {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      if (typeof window !== 'undefined' && window.scrollTo) window.scrollTo(0, 0);
    }
  };
  const goNext = async () => {
    if (!bookMeta || startParagraph == null) return;
    const newStart = Math.min(bookMeta.Max_Paragraph_Number, startParagraph + 5);
    setStartParagraph(newStart);
    savePosition(newStart);
    try {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      // Fallback in non-browser environments
      if (typeof window !== 'undefined' && window.scrollTo) window.scrollTo(0, 0);
    }
  };

  if (loading && !bookMeta) {
    return (
      <div className="container mt-4 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Loading book...</p>
      </div>
    );
  }

  if (error) {
    return <div className="container mt-4 alert alert-danger">Error: {error}</div>;
  }

  return (
    <div className="container mt-4">
      <div className="row align-items-center mb-3">
        <div className="col-auto">
          <h2 className="mb-0">{bookMeta?.book_name || 'Book'}</h2>
        </div>
        <div className="col text-center">
          {progressInfo && progressInfo.total ? (
            <span className="text-warning opacity-75">
              {progressInfo.percent != null ? Math.round(progressInfo.percent) : 0}% · {progressInfo.index ?? '-'} / {progressInfo.total}
              {typeof bookMeta?.paragraphs_read_24h === 'number' ? ` · ${bookMeta.paragraphs_read_24h}` : ''}
            </span>
          ) : (
            <span className="text-warning opacity-75"> - % · - / -</span>
          )}
        </div>
        <div className="col-auto">
          <Link to="/books" className="btn btn-outline-secondary">← Back to Books</Link>
        </div>
      </div>

      <div className="d-flex gap-2 mb-3">
        <button className="btn btn-outline-primary" onClick={goPrev} disabled={atStart || loading}>
          ◀ 5
        </button>
        <button className="btn btn-outline-primary" onClick={goNext} disabled={atEnd || loading}>
          5 ▶
        </button>
        {saving && <span className="text-muted ms-2">Saving position...</span>}
      </div>

      {loading && bookMeta && (
        <div className="text-muted mb-2">Loading paragraphs...</div>
      )}

      <div className="reading-area">
        {paragraphs.map((p) => (
          <div key={p.id_paragraph} className="card mb-3">
            <div className="card-body">
              <p style={{ whiteSpace: 'pre-wrap', textAlign: 'justify', marginBottom: 0 }}>
                {p.sentences.map((s, idx) => (
                  <React.Fragment key={idx}>
                    <span
                      onClick={handleSentenceClick}
                      style={{ color: idx % 2 === 0 ? 'lightgreen' : 'lightblue', cursor: 'pointer' }}
                    >
                      {s.sentence}
                    </span>
                    <button
                      type="button"
                      className="btn btn-link btn-sm p-0 ms-1 align-baseline"
                      title="Озвучить предложение"
                      onClick={() => playSentenceTTS(s.sentence)}
                      disabled={ttsLoading}
                      style={{ verticalAlign: 'baseline', textDecoration: 'none' }}
                    >
                      {ttsLoading ? '…' : '🔊'}
                    </button>
                    {idx !== p.sentences.length - 1 && ' '}
                  </React.Fragment>
                ))}
              </p>
            </div>
          </div>
        ))}
        {paragraphs.length === 0 && !loading && (
          <div className="alert alert-info">Нет абзацев для отображения.</div>
        )}
      </div>

      <div className="d-flex gap-2 mt-3">
        <button className="btn btn-outline-primary" onClick={goPrev} disabled={atStart || loading}>
          ◀ 5
        </button>
        <button className="btn btn-outline-primary" onClick={goNext} disabled={atEnd || loading}>
          5 ▶
        </button>
      </div>
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

      {/* Bottom spacer to allow extra scroll and space for context menus */}
      <div aria-hidden="true" style={{ height: '100vh' }} />
    </div>
  );
}

export default BookReader;
