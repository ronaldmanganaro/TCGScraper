import React from 'react';
import './App.css';

function App() {
  const PriceCheck = () => {
    alert('Button Clicked')
  }


  return (
    <div className="App">
      <h1>Trigger Jobs!</h1>
      <button onClick={PriceCheck}> Run Price Check </button>
    </div>
  );
}

export default App;
