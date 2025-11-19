import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';

function BooksList() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const apiUrl = process.env.REACT_APP_API_URL;
  const { user } = useAuth();

  useEffect(() => {
    const fetchBooks = async () => {
      try {
        const response = await fetch(`${apiUrl}/books`, {
          credentials: 'include',
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch books');
        }
        
        const data = await response.json();
        setBooks(data);
      } catch (err) {
        console.error('Error fetching books:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchBooks();
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2">Loading books...</p>
      </div>
    );
  }

  if (error) {
    return <div className="container mt-4 alert alert-danger">Error: {error}</div>;
  }

  return (
    <div className="container mt-4">
      <h2>Books</h2>
      {user && (
        <div className="mb-3">
          <Link to="/books/add" className="btn btn-primary">
            Add New Book
          </Link>
        </div>
      )}
      
      <div className="list-group">
        {books.map((book) => (
          <div key={book.id_book} className="list-group-item">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-1">{book.book_name}</h5>
                <small className="text-muted">
                  Added on: {new Date(book.dt).toLocaleDateString()}
                </small>
                <div>
                  <small className="text-muted">
                    Paragraphs: {book.Min_Paragraph_Number} - {book.Max_Paragraph_Number}
                  </small>
                </div>
              </div>
              <Link 
                to={`/books/${book.id_book}`} 
                className="btn btn-sm btn-outline-primary"
              >
                View Details
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BooksList;
