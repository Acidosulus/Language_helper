import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

const apiUrl = process.env.REACT_APP_API_URL;

function SyllableDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [syllable, setSyllable] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSyllable = async () => {
      try {
        console.log('API URL:', `${apiUrl}/syllable?syllable_id=${id}`);
        const response = await fetch(
          `${apiUrl}/syllable?syllable_id=${id}`,
          {
            credentials: 'include',
          }
        );
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to fetch syllable: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Syllable data:', data);
        setSyllable(data);
      } catch (err) {
        setError('Failed to load syllable');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchSyllable();
    } else {
      setLoading(false);
    }
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this syllable?')) {
      try {
        const response = await fetch(`${apiUrl}/syllable/${id}`, {
          method: 'DELETE',
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to delete syllable');
        }

        navigate('/syllables');
      } catch (err) {
        setError('Failed to delete syllable');
        console.error(err);
      }
    }
  };

  if (loading) {
    return <div className="container mt-4">Loading...</div>;
  }

  if (!syllable && !loading) {
    return (
      <div className="container mt-4">
        <div className="alert alert-warning">Syllable not found</div>
        <Link to="/syllables" className="btn btn-secondary">
          Back to Syllables
        </Link>
      </div>
    );
  }

  return (
    <div className="container mt-4">
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h2>Syllable Details</h2>
          <div>
            <Link to={`/syllables/${id}/edit`} className="btn btn-warning me-2">
              Edit
            </Link>
            <button onClick={handleDelete} className="btn btn-danger">
              Delete
            </button>
          </div>
        </div>
        <div className="card-body">
          <dl className="row">
            <dd className="col-sm-9">{syllable.id}</dd>

            <dd className="col-sm-9">{syllable.word}</dd>

            <dd className="col-sm-9">{syllable.translations}</dd>

            {/* Add other fields as needed */}
          </dl>
        </div>
        <div className="card-footer">
          <Link to="/syllables" className="btn btn-secondary">
            Back to List
          </Link>
        </div>
      </div>
    </div>
  );
}

export default SyllableDetail;
