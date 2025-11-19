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

  useEffect(() => {
    if (user) {
      fetchSyllables();
    }
  }, [page, user]);

  const fetchSyllables = async () => {
    try {
      const offset = (page - 1) * limit;
      const response = await fetch(
        `${apiUrl}/syllables?limit=${limit}&offset=${offset}`,
        {
          credentials: 'include',
        }
      );
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
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this syllable?')) {
      try {
        await fetch(`${apiUrl}/api/syllable/${id}`, {
          method: 'DELETE',
          credentials: 'include',
        });
        fetchSyllables(); // Refresh the list
      } catch (error) {
        console.error('Error deleting syllable:', error);
      }
    }
  };

  if (loading) {
    return <div className="container mt-4">Loading...</div>;
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Syllables</h2>
        <Link to="/syllables/new" className="btn btn-primary">
          Add New Syllable
        </Link>
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
                    <Link
                      to={`/syllables/${syllable.syllable_id}`}
                      className="btn btn-sm btn-info me-2"
                    >
                      View
                    </Link>
                    <Link
                      to={`/syllables/${syllable.syllable_id}/edit`}
                      className="btn btn-sm btn-warning me-2"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(syllable.syllable_id)}
                      className="btn btn-sm btn-danger"
                    >
                      Delete
                    </button>
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
