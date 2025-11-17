import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../App';
import './Phrases.css';

function PhraseDetail() {
  const { id_phrase } = useParams();
  const [phrase, setPhrase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();
  const apiUrl = 'http://localhost:8000/api';

  useEffect(() => {
    const fetchPhrase = async () => {
      try {
        const response = await fetch(`${apiUrl}/phrase/${id_phrase}`, {
          credentials: 'include',
        });
        if (!response.ok) {
          throw new Error('Failed to fetch phrase');
        }
        const data = await response.json();
        setPhrase(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchPhrase();
    }
  }, [id_phrase, user]);

  if (!user) {
    return <div>Please log in to view this phrase.</div>;
  }

  if (loading) {
    return <div>Loading phrase...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  if (!phrase) {
    return <div>Phrase not found</div>;
  }

  return (
    <div className="phrase-detail">
      <div style={{ marginBottom: '20px' }}>
        <Link to="/phrases" className="back-link">
          &larr; Back to Phrases
        </Link>
      </div>
      <div className="phrase-card">
        <div className="phrase-original">
          <h3>Original <Text></Text></h3>
          <p>{phrase.phrase}</p>
        </div>
        <div className="phrase-translation">
          <h3>Translation</h3>
          <p>{phrase.translation || 'No translation available'}</p>
        </div>
        {phrase.context && (
          <div className="phrase-context">
            <h3>Context</h3>
            <p>{phrase.context}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PhraseDetail;
