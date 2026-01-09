import React, { useState } from 'react';
import { InputGroup, FormControl, Button } from 'react-bootstrap';
import { FaSearch, FaTimes } from 'react-icons/fa';

const searchEngines = {
  google: 'https://www.google.com/search?q=',
  yandex: 'https://yandex.com/search/?text=',
  youtube: 'https://www.youtube.com/results?search_query=',
  wikipedia: 'https://en.wikipedia.org/w/index.php?search='
};

const SearchBar = () => {
  const [searchQueries, setSearchQueries] = useState({
    google: '',
    yandex: '',
    youtube: '',
    wikipedia: ''
  });

  const handleSearch = (engine) => {
    const query = searchQueries[engine].trim();
    if (query) {
      window.open(`${searchEngines[engine]}${encodeURIComponent(query)}`, '_blank');
    }
  };

  const handleKeyPress = (e, engine) => {
    if (e.key === 'Enter') {
      handleSearch(engine);
    }
  };

  const handleClear = (engine) => {
    setSearchQueries(prev => ({
      ...prev,
      [engine]: ''
    }));
  };

  const handleChange = (e, engine) => {
    setSearchQueries(prev => ({
      ...prev,
      [engine]: e.target.value
    }));
  };

  return (
    <div className="search-container">
      {Object.entries({
        google: 'Google',
        yandex: 'Yandex',
        youtube: 'YouTube',
        wikipedia: 'Wikipedia'
      }).map(([key, label]) => (
        <div key={key} className="search-group">
          <InputGroup>
            <InputGroup.Text>{label}</InputGroup.Text>
            <FormControl
              placeholder={`Search with ${label}...`}
              value={searchQueries[key]}
              onChange={(e) => handleChange(e, key)}
              onKeyPress={(e) => handleKeyPress(e, key)}
            />
            <Button 
              variant="outline-secondary" 
              onClick={() => handleClear(key)}
              title="Clear"
            >
              <FaTimes />
            </Button>
            <Button 
              variant="primary" 
              onClick={() => handleSearch(key)}
              disabled={!searchQueries[key].trim()}
              title={`Search with ${label}`}
            >
              <FaSearch />
            </Button>
          </InputGroup>
        </div>
      ))}
    </div>
  );
};

export default SearchBar;
