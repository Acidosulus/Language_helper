import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../App';

const apiUrl = process.env.REACT_APP_API_URL;

function SyllableForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(!!id);
  const [error, setError] = useState('');
  const [syllable, setSyllable] = useState({
    text: '',
    translation: '',
    // Add other fields as needed
  });

  useEffect(() => {
    if (id) {
      const fetchSyllable = async () => {
        try {
          const response = await fetch(`${apiUrl}/syllable?syllable_id=${id}`, {
            credentials: 'include',
          });
          if (!response.ok) throw new Error('Failed to fetch syllable');
          const data = await response.json();
          setSyllable(data);
        } catch (err) {
          setError('Failed to load syllable');
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchSyllable();
    } else {
      setLoading(false);
    }
  }, [id]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSyllable(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const method = id ? 'PUT' : 'POST';
      const url = id ? `${apiUrl}/syllable/${id}` : `${apiUrl}/syllable`;
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(syllable),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save syllable');
      }

      navigate('/syllables');
    } catch (err) {
      setError(err.message || 'An error occurred');
      console.error('Error saving syllable:', err);
    }
  };

  if (loading) {
    return <div className="container mt-4">Loading...</div>;
  }

  return (
    <div className="container mt-4">
      <h2>{id ? 'Edit Syllable' : 'Add New Syllable'}</h2>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="text" className="form-label">
            Text
          </label>
          <input
            type="text"
            className="form-control"
            id="text"
            name="text"
            value={syllable.text || ''}
            onChange={handleChange}
            required
          />
        </div>

        <div className="mb-3">
          <label htmlFor="translation" className="form-label">
            Translation
          </label>
          <input
            type="text"
            className="form-control"
            id="translation"
            name="translation"
            value={syllable.translation || ''}
            onChange={handleChange}
            required
          />
        </div>

        {/* Add other form fields as needed */}

        <div className="mt-4">
          <button type="submit" className="btn btn-primary me-2">
            {id ? 'Update' : 'Save'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/syllables')}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default SyllableForm;
