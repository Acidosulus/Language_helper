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
    word: '',
    transcription: '',
    translations: '',
    examples: null,
    paragraphs: []
  });
  
  const [newParagraph, setNewParagraph] = useState({
    example: '',
    translate: ''
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
  
  const handleParagraphChange = (e, index) => {
    const { name, value } = e.target;
    setSyllable(prev => ({
      ...prev,
      paragraphs: prev.paragraphs.map((p, i) => 
        i === index ? { ...p, [name]: value } : p
      )
    }));
  };
  
  const handleNewParagraphChange = (e) => {
    const { name, value } = e.target;
    setNewParagraph(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const addParagraph = () => {
    if (newParagraph.example.trim() && newParagraph.translate.trim()) {
      setSyllable(prev => ({
        ...prev,
        paragraphs: [
          ...prev.paragraphs,
          {
            paragraph_id: `new-${Date.now()}`,
            example: newParagraph.example,
            translate: newParagraph.translate,
            syllable_id: id || null
          }
        ]
      }));
      setNewParagraph({ example: '', translate: '' });
    }
  };
  
  const removeParagraph = (index) => {
    setSyllable(prev => ({
      ...prev,
      paragraphs: prev.paragraphs.filter((_, i) => i !== index)
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
          <label htmlFor="word" className="form-label">
            Word
          </label>
          <input
            type="text"
            className="form-control"
            id="word"
            name="word"
            value={syllable.word || ''}
            onChange={handleChange}
            required
          />
        </div>

        <div className="mb-3">
          <label htmlFor="transcription" className="form-label">
            Transcription
          </label>
          <input
            type="text"
            className="form-control"
            id="transcription"
            name="transcription"
            value={syllable.transcription || ''}
            onChange={handleChange}
            placeholder="e.g., |ɪmˈbjuː|"
          />
        </div>

        <div className="mb-3">
          <label htmlFor="translations" className="form-label">
            Translations (one per line)
          </label>
          <textarea
            className="form-control"
            id="translations"
            name="translations"
            rows="5"
            value={syllable.translations || ''}
            onChange={handleChange}
            required
          />
        </div>

        <div className="mb-4">
          <h4>Examples</h4>
          {syllable.paragraphs && syllable.paragraphs.map((para, index) => (
            <div key={para.paragraph_id || index} className="card mb-3">
              <div className="card-body">
                <div className="d-flex justify-content-end">
                  <button 
                    type="button" 
                    className="btn-close" 
                    aria-label="Remove"
                    onClick={() => removeParagraph(index)}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Example</label>
                  <input
                    type="text"
                    className="form-control"
                    name="example"
                    value={para.example || ''}
                    onChange={(e) => handleParagraphChange(e, index)}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Translation</label>
                  <input
                    type="text"
                    className="form-control"
                    name="translate"
                    value={para.translate || ''}
                    onChange={(e) => handleParagraphChange(e, index)}
                    required
                  />
                </div>
              </div>
            </div>
          ))}
          
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Add New Example</h5>
              <div className="mb-3">
                <label className="form-label">Example</label>
                <input
                  type="text"
                  className="form-control"
                  name="example"
                  value={newParagraph.example}
                  onChange={handleNewParagraphChange}
                  placeholder="Enter example sentence"
                />
              </div>
              <div className="mb-3">
                <label className="form-label">Translation</label>
                <input
                  type="text"
                  className="form-control"
                  name="translate"
                  value={newParagraph.translate}
                  onChange={handleNewParagraphChange}
                  placeholder="Enter translation"
                />
              </div>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={addParagraph}
                disabled={!newParagraph.example.trim() || !newParagraph.translate.trim()}
              >
                Add Example
              </button>
            </div>
          </div>
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
