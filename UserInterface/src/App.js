import React from 'react';
import PanoramaViewer from './PanoramaViewer';
import './App.css';

function App() {
  return (
    <div className="App">
      <div className="panorama-container">
        <PanoramaViewer imageSrc="omni7_20220307_155200_14809959_Panoramic_000140_6890_124-5394.jpg" />
      </div>
    </div>
  );
}

export default App;
