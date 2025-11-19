import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './Phrases.css';

const apiUrl = process.env.REACT_APP_API_URL;

function LearnSyllables() {
  const [currentSyllable, setCurrentSyllable] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  const fetchNextSyllable = async (currentId = 0) => {
    try {
      setLoading(true);
      const response = await fetch(`${apiUrl}/syllable/next?current_syllable_id=${currentId}`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        throw new Error('Ошибка при загрузке слога');
      }
      
      const data = await response.json();
      
      if (!data) {
        setCurrentSyllable(null);
        setError('Все слоги изучены!');
      } else {
        setCurrentSyllable(data);
        setError('');
      }
    } catch (err) {
      setError(err.message);
      if (err.message.includes('401')) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchNextSyllable();
    }
  }, [user]);

  const handleNextSyllable = () => {
    if (currentSyllable) {
      fetchNextSyllable(currentSyllable.syllable_id);
    }
  };

  if (!user) {
    return <div className="container">Пожалуйста, войдите в систему, чтобы изучать слоги</div>;
  }

  return (
    <div className="learn-container">
      <h2>Изучение слогов</h2>
      
      {error && <div className="error">{error}</div>}
      
      {loading && !currentSyllable ? (
        <div>Загрузка...</div>
      ) : currentSyllable ? (
        <div className="phrase-card">
          <div className="phrase-text">
            <h3>{currentSyllable.word}</h3>
            {currentSyllable.transcription && (
              <div className="transcription">
                [{currentSyllable.transcription}]
              </div>
            )}
            
            {currentSyllable.translations && (
              <div className="translation">
                <strong>Перевод:</strong> {currentSyllable.translations}
              </div>
            )}
            
            {currentSyllable.examples && (
              <div className="examples">
                <strong>Примеры:</strong> {currentSyllable.examples}
              </div>
            )}
            
            {currentSyllable.paragraphs && currentSyllable.paragraphs.length > 0 && (
              <div className="paragraphs">
                <h4>Примеры использования:</h4>
                {currentSyllable.paragraphs.map((para, index) => (
                  <div key={index} className="paragraph">
                    <div className="example">{para.example}</div>
                    {para.translate && (
                      <div className="example-translation">{para.translate}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <button 
            onClick={handleNextSyllable}
            className="next-button"
            disabled={loading}
          >
            {loading ? 'Загрузка...' : 'Следующий слог'}
          </button>
        </div>
      ) : (
        <div className="no-syllables">
          <p>Нет доступных слогов для изучения</p>
        </div>
      )}
    </div>
  );
}

export default LearnSyllables;
