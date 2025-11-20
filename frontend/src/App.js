import React, { useState, useEffect, createContext, useContext } from 'react';
import { 
  BrowserRouter as Router, 
  Routes, 
  Route, 
  Navigate, 
  useNavigate, 
  Link,
  NavLink 
} from 'react-router-dom';
import { Nav, Navbar, Container, NavDropdown } from 'react-bootstrap';
import { FaBook, FaList, FaGraduationCap, FaHome } from 'react-icons/fa';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import PhrasesList from './components/PhrasesList';
import PhraseDetail from './components/PhraseDetail';
import LearnPhrases from './components/LearnPhrases';
import SyllablesList from './components/SyllablesList';
import SyllableDetail from './components/SyllableDetail';
import SyllableForm from './components/SyllableForm';
import LearnSyllables from './components/LearnSyllables';
import BooksList from './components/BooksList';
import BookReader from './components/BookReader';

// Create auth context
export const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const apiUrl = process.env.REACT_APP_API_URL;

  useEffect(() => {
    // Check if user is logged in on initial load
    const checkAuth = async () => {
      try {
        const response = await fetch(`${apiUrl}/me`, {
          credentials: 'include',
        });
        const data = await response.json();
        if (data.authenticated) {
          setUser({ username: data.user, email: data.email});
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch(`${apiUrl}/login`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUser({ username: data.user });
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await fetch(`${apiUrl}/register`, {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        return { success: true };
      } else {
        return { success: false, error: data.detail || 'Registration failed' };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: 'Network error' };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${apiUrl}/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      setUser(null);
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: 'Logout failed' };
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      <Router>
        <div className="app">
          <nav className="navbar">
            <div className="nav-left">
              <h1><Link to="/" className="brand-button">Language Helper</Link></h1>
              {user && (
                <div className="nav-actions-left">
                  <Link to="/phrases" className="nav-link">Phrases</Link>
                  <Link to="/syllables" className="nav-link">Words</Link>
                  <Link to="/books" className="nav-link">Books</Link>
                </div>
              )}
            </div>
            <div className="nav-links">
              {user ? (
                <>
                  <span>Welcome, {user.username}!</span>
                  <button onClick={logout} className="nav-button">Logout</button>
                </>
              ) : (
                <>
                  <a href="/login">Login</a>
                  <a href="/register">Register</a>
                </>
              )}
            </div>
          </nav>

          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route
                path="/login"
                element={user ? <Navigate to="/" /> : <Login />}
              />
              <Route
                path="/register"
                element={user ? <Navigate to="/" /> : <Register />}
              />
              <Route
                path="/secret"
                element={user ? <SecretPage /> : <Navigate to="/login" />}
              />
              <Route
                path="/phrases"
                element={user ? <PhrasesList /> : <Navigate to="/login" />}
              />
              <Route
                path="/phrases/learn"
                element={user ? <LearnPhrases /> : <Navigate to="/login" />}
              />
              <Route
                path="/phrases/:id_phrase"
                element={user ? <PhraseDetail /> : <Navigate to="/login" />}
              />
              {/* Syllables Routes */}
              <Route
                path="/syllables"
                element={user ? <SyllablesList /> : <Navigate to="/login" />}
              />
              <Route
                path="/syllables/new"
                element={user ? <SyllableForm /> : <Navigate to="/login" />}
              />
              <Route
                path="/syllables/:id"
                element={user ? <SyllableDetail /> : <Navigate to="/login" />}
              />
              <Route
                path="/syllables/:id/edit"
                element={user ? <SyllableForm /> : <Navigate to="/login" />}
              />
              <Route
                path="/syllables/learn"
                element={user ? <LearnSyllables /> : <Navigate to="/login" />}
              />
              {/* Books Routes */}
              <Route
                path="/books"
                element={user ? <BooksList /> : <Navigate to="/login" />}
              />
              <Route
                path="/books/:id_book/read"
                element={user ? <BookReader /> : <Navigate to="/login" />}
              />
            </Routes>
          </main>
        </div>
      </Router>
    </AuthContext.Provider>
  );
}

function Home() {
  return null;
}

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const result = await login(username, password);
    if (result.success) {
      navigate('/');
    } else {
      setError(result.error || 'Login failed');
    }
  };

  return (
    <div className="auth-container">
      <h2>Login</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="btn">Login</button>
      </form>
      <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
  );
}

function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 3) {
      setError('Password must be at least 3 characters long');
      return;
    }

    const result = await register(username, password);
    if (result.success) {
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } else {
      setError(result.error || 'Registration failed');
    }
  };

  if (success) {
    return (
      <div className="auth-container">
        <h2>Registration Successful!</h2>
        <p>Redirecting to login page...</p>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <h2>Register</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label>Password (min 3 characters):</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={3}
          />
        </div>
        <button type="submit" className="btn">Register</button>
      </form>
      <p>Already have an account? <a href="/login">Login here</a></p>
    </div>
  );
}

function SecretPage() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSecret = async () => {
      try {
        const response = await fetch(process.env.REACT_APP_API_URL+'/secret', {
          credentials: 'include',
        });
        const data = await response.json();
        if (response.ok) {
          setMessage(data.message);
        } else {
          navigate('/login');
        }
      } catch (error) {
        console.error('Error fetching secret:', error);
        navigate('/login');
      } finally {
        setLoading(false);
      }
    };

    fetchSecret();
  }, [navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="container">
      <h2>Secret Page</h2>
      <p>{message}</p>
      <a href="/" className="btn">Back to Home</a>
    </div>
  );
}

export default App;
