import React, { useState } from 'react';
import './App.css';

function App() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

  const handleQuestionChange = (event) => {
    setQuestion(event.target.value);
  };

  const submitQuestion = async () => {
    try {
      const response = await fetch('http://localhost:8000/process/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: question }),
      });
      const data = await response.json();
      setAnswer(data.processed_text);
    } catch (error) {
      console.error('Error fetching data: ', error);
      setAnswer('Error fetching data');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Ask your golf assistant any question</h1>
        <h2>Examples:</h2>
        <ul>
          <li>I am wondering if I should alter the width of my stance for my drives, can you provide some input?</li>
          <li>When I hit iron shots, my ball starts to the left and then curvers further to the left, I am a lefty, what should I do to fix this?</li>
          <li> What are some basic rules in green reading, and approaching long puts, please provide to bullet points on this.</li>
        </ul>
        <textarea
          className="question-input"
          value={question}
          onChange={handleQuestionChange}
          placeholder="Type your question here..."
          rows="4"
          />
        <button className="submit-button" onClick={submitQuestion}>
          Submit
        </button>
        <div>
          <strong>Response:</strong> {answer}
        </div>
      </header>
    </div>
  );
}

export default App;
