import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './Phrases.css';

function LearnPhrases() {
  const [currentPhrase, setCurrentPhrase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();
  const apiUrl = 'http://localhost:8000/api';

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
            <h3>{currentPhrase.phrase}</h3>
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
    </div>
  );
}

export default LearnPhrases;
