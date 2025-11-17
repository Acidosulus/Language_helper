import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import './Phrases.css';

function PhrasesList() {
  const [phrases, setPhrases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPhrase, setNewPhrase] = useState({
    phrase: '',
    translation: '',
  });
  const { user } = useAuth();
  const apiUrl = 'http://localhost:8000/api';

  useEffect(() => {
    const fetchPhrases = async () => {
      try {
        const response = await fetch(`${apiUrl}/phrases`, {
          credentials: 'include',
        });
        if (!response.ok) {
          throw new Error('Failed to fetch phrases');
        }
        const data = await response.json();
        setPhrases(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchPhrases();
    }
  }, [user]);

  if (!user) {
    return <div>Please log in to view phrases.</div>;
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewPhrase(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${apiUrl}/phrase`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newPhrase)
      });

      if (!response.ok) {
        throw new Error('Failed to add phrase');
      }

      const data = await response.json();
      setPhrases([...phrases, data]);
      setNewPhrase({ phrase: '', translation: ''});
      setShowAddForm(false);
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div>Loading phrases...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="phrases-container">
      <div className="phrases-header">
        <h2>My Phrases</h2>
        <button 
          className="btn" 
          onClick={() => setShowAddForm(true)}
          style={{ marginLeft: 'auto' }}
        >
          Add New Phrase
        </button>
      </div>
      
      {showAddForm && (
        <div className="add-phrase-form">
          <h3>Add New Phrase</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="phrase">Phrase:</label>
              <input
                type="text"
                id="phrase"
                name="phrase"
                value={newPhrase.phrase}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="translation">Translation:</label>
              <input
                type="text"
                id="translation"
                name="translation"
                value={newPhrase.translation}
                onChange={handleInputChange}
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="btn">Save</button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => setShowAddForm(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
      {phrases.length === 0 ? (
        <p>No phrases found. Start adding some!</p>
      ) : (
        <table className="phrases-table">
          <thead>
            <tr>
              <th>Original Text</th>
              <th>Translation</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {phrases.map((phrase) => (
              <tr key={phrase.id_phrase}>
                <td>{phrase.phrase}</td>
                <td>{phrase.translation}</td>
                <td>
                  <Link to={`/phrases/${phrase.id_phrase}`} className="btn" style={{ display: 'inline-block' }}>
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default PhrasesList;
