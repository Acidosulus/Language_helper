import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';

const apiUrl = process.env.REACT_APP_API_URL;

function SyllablesList() {
  const [syllables, setSyllables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const limit = 10;
  const { user } = useAuth();
  const [wordPart, setWordPart] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [readyStatus, setReadyStatus] = useState(0);

  useEffect(() => {
    if (user) {
      fetchSyllables();
    }
  }, [page, user]);

  // Update list when input text changes (debounced)
  useEffect(() => {
    if (!user) return;
    const t = setTimeout(() => {
      setPage(1); // reset to first page on new search
      fetchSyllables(1);
    }, 350);
    return () => clearTimeout(t);
  }, [wordPart, user]);

  const fetchSyllables = async (forcedPage) => {
    try {
      const currentPage = forcedPage || page;
      const offset = (currentPage - 1) * limit;
      const url = `${apiUrl}/syllables/search?ready=${readyStatus}&word_part=${encodeURIComponent(
        wordPart
      )}&limit=${limit}&offset=${offset}`;
      setIsSearching(true);
      const response = await fetch(url, {
        credentials: 'include',
      });
      const data = await response.json();
      console.log('API Response:', data);
      console.log('Type of data:', typeof data);
      console.log('Is array:', Array.isArray(data));
      if (data && Array.isArray(data)) {
        console.log('First item:', data[0]);
      }
      setSyllables(data || []);
      // Assuming we get total count from the API in the future
      // For now, we'll just set a default total
      setTotalPages(Math.ceil(100 / limit));
    } catch (error) {
      console.error('Error fetching syllables:', error);
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const onSearchClick = () => {
    setPage(1);
    fetchSyllables(1);
  };

  const onClearClick = () => {
    setWordPart('');
    setPage(1);
    fetchSyllables(1);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this syllable?')) {
      try {
        await fetch(`${apiUrl}/syllable/${id}`, {
          method: 'DELETE',
          credentials: 'include',
        });
        fetchSyllables(); // Refresh the list
      } catch (error) {
        console.error('Error deleting syllable:', error);
      }
    }
  };

  const handleMarkAsLearned = async (syllableId) => {
    try {
      await fetch(`${apiUrl}/syllables/learned`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ syllable_id: syllableId }),
      });
      fetchSyllables(); // Refresh the list
    } catch (error) {
      console.error('Error marking as learned:', error);
    }
  };

  const handleMarkAsUnlearned = async (syllableId) => {
    try {
      await fetch(`${apiUrl}/syllables/unlearned`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ syllable_id: syllableId }),
      });
      fetchSyllables(); // Refresh the list
    } catch (error) {
      console.error('Error marking as unlearned:', error);
    }
  };

  if (loading) {
    return <div className="container mt-4">Loading...</div>;
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div className="d-flex align-items-center gap-2" style={{ flex: 1 }}>
          <input
            type="text"
            className="form-control"
            placeholder="Введите часть слова..."
            value={wordPart}
            onChange={(e) => setWordPart(e.target.value.toLowerCase())}
            style={{ maxWidth: 320, textTransform: 'lowercase' }}
          />
          <button className="btn btn-primary" onClick={onSearchClick} disabled={isSearching}>
            Искать
          </button>
          <button className="btn btn-secondary" onClick={onClearClick} disabled={isSearching && wordPart === ''}>
            Очистить
          </button>
          <button 
            className={`btn ${readyStatus === 0 ? 'btn-warning' : 'btn-success'}`}
            onClick={() => {
              const newStatus = readyStatus === 0 ? 1 : 0;
              setReadyStatus(newStatus);
              setPage(1);
              fetchSyllables(1);
            }}
            title={readyStatus === 0 ? 'Learn' : 'Learned'}
          >
            {readyStatus === 0 ? 'Learn' : 'Learned'}
          </button>
        </div>
        <div className="d-flex gap-2">
          <Link to="/syllables/learn" className="btn btn-success">
            Learn Words
          </Link>
          <Link to="/syllables/new" className="btn btn-primary">
            Add New Word
          </Link>
        </div>
      </div>

      <div className="table-responsive">
        <table className="table table-striped">
          <thead>
            <tr>
              <th>ID</th>
              <th>Text</th>
              <th>Translation</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {syllables.length > 0 ? (
              syllables.map((syllable) => (
                <tr key={syllable.syllable_id}>
                  <td>{syllable.syllable_id}</td>
                  <td>{syllable.word}</td>
                  <td>{syllable.translations}</td>
                  <td>
                    <div className="d-flex flex-column gap-1" style={{minWidth: '100px'}}>
                      <Link
                        to={`/syllables/${syllable.syllable_id}`}
                        className="btn btn-sm btn-info me-1"
                      >
                        View
                      </Link>
                      <Link
                        to={`/syllables/${syllable.syllable_id}/edit`}
                        className="btn btn-sm btn-warning me-1"
                      >
                        Edit
                      </Link>
                      <button
                        onClick={() => handleMarkAsLearned(syllable.syllable_id)}
                        className="btn btn-sm btn-success me-1"
                        title="Mark as Learned"
                      >
                        ✓ Learned
                      </button>
                      <button
                        onClick={() => handleMarkAsUnlearned(syllable.syllable_id)}
                        className="btn btn-sm btn-outline-secondary me-1"
                        title="Mark as Unlearned"
                      >
                        × Unlearned
                      </button>
                      <button
                        onClick={() => handleDelete(syllable.syllable_id)}
                        className="btn btn-sm btn-danger"
                        title="Delete"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="text-center">
                  No syllables found. Add your first syllable!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <nav>
          <ul className="pagination justify-content-center">
            <li className={`page-item ${page === 1 ? 'disabled' : ''}`}>
              <button
                className="page-link"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Previous
              </button>
            </li>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <li
                key={p}
                className={`page-item ${page === p ? 'active' : ''}`}
              >
                <button className="page-link" onClick={() => setPage(p)}>
                  {p}
                </button>
              </li>
            ))}
            <li className={`page-item ${page === totalPages ? 'disabled' : ''}`}>
              <button
                className="page-link"
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                Next
              </button>
            </li>
          </ul>
        </nav>
      )}
    </div>
  );
}

export default SyllablesList;
