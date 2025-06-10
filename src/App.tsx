import { Routes, Route, Navigate } from 'react-router-dom';
import VideoEditorInterface from './VideoEditorInterface';
import VideoTemplatesPage from './VideoTemplatesPage';
import VideoGenerationPage from './VideoGenerationPage';
import './index.css'; // Ensure Tailwind styles are applied

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/templates" replace />} />
      <Route path="/templates" element={<VideoTemplatesPage />} />
      <Route path="/editor/:videoId" element={<VideoEditorInterface />} />
      <Route path="/generate/:videoId" element={<VideoGenerationPage />} />
      {/* You can add a 404 page here if needed */}
      <Route path="*" element={<Navigate to="/templates" replace />} /> 
    </Routes>
  );
}

export default App;
