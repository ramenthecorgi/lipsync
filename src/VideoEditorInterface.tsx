// Paste your TSX component code here

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, RotateCcw, RotateCw, Edit3, Volume2, Eye, Save, AlertTriangle, Sparkles, LayoutGrid } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';

// Dummy video data
const dummyVideos = [
  { id: 'vid1', title: 'Summer Vacation Highlights', thumbnailUrl: 'https://via.placeholder.com/150/FFC107/000000?Text=Video1', duration: 125 },
  { id: 'vid2', title: 'Cooking Masterclass: Pasta', thumbnailUrl: 'https://via.placeholder.com/150/4CAF50/FFFFFF?Text=Video2', duration: 320 },
  { id: 'vid3', title: 'Tech Review: New Gadgets', thumbnailUrl: 'https://via.placeholder.com/150/2196F3/FFFFFF?Text=Video3', duration: 180 },
  { id: 'vid4', title: 'Fitness Challenge Day 10', thumbnailUrl: 'https://via.placeholder.com/150/E91E63/FFFFFF?Text=Video4', duration: 240 },
];

export default function VideoEditorInterface() {
  const { videoId: videoIdFromUrl } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  const [availableVideos, setAvailableVideos] = useState(dummyVideos);
  const [selectedVideoId, setSelectedVideoId] = useState(dummyVideos[0].id); // Default video

  useEffect(() => {
    if (videoIdFromUrl && availableVideos.some(v => v.id === videoIdFromUrl)) {
      setSelectedVideoId(videoIdFromUrl);
    }
    // If videoIdFromUrl is not present or invalid, selectedVideoId remains its current value (default or last valid).
  }, [videoIdFromUrl, availableVideos]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedSegment, setSelectedSegment] = useState(2);
  const [editText, setEditText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const videoRef = useRef(null);

  const selectedVideo = availableVideos.find(v => v.id === selectedVideoId);

  const segments = [
    { id: 1, label: 'Segment 01', startTime: 0.0, endTime: 3.2, speaker: 'Jane Smith', originalText: 'Hello everyone, welcome to our presentation today.', color: 'from-purple-500 to-pink-500' },
    { id: 2, label: 'Segment 02', startTime: 3.2, endTime: 6.0, speaker: 'John Doe', originalText: 'Thank you Jane. Let me start with our key findings.', color: 'from-blue-500 to-cyan-500' },
    { id: 3, label: 'Segment 03', startTime: 6.0, endTime: 9.4, speaker: 'John Doe', originalText: 'We really believe this is a game-changer for small businesses.', color: 'from-emerald-500 to-teal-500' },
    { id: 4, label: 'Segment 04', startTime: 9.4, endTime: 11.0, speaker: 'Jane Smith', originalText: 'The results speak for themselves.', color: 'from-orange-500 to-red-500' },
    { id: 5, label: 'Segment 05', startTime: 11.0, endTime: 13.5, speaker: 'John Doe', originalText: 'Moving forward, we see tremendous opportunities ahead.', color: 'from-indigo-500 to-purple-500' }
  ];

  const currentSegment = segments[selectedSegment];
  const segmentDuration = currentSegment.endTime - currentSegment.startTime;
  
  const estimateTextDuration = (text) => {
    const words = text.trim().split(/\s+/).filter(word => word.length > 0);
    const wordsPerSecond = 150 / 60;
    return words.length / wordsPerSecond;
  };

  const editedDuration = editText ? estimateTextDuration(editText) : segmentDuration;
  const exceedsLimit = editedDuration > segmentDuration;

  useEffect(() => {
    setEditText(currentSegment.originalText);
  }, [selectedSegment]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleRewind = () => {
    setCurrentTime(Math.max(0, currentTime - 5));
  };

  const handleFastForward = () => {
    setCurrentTime(currentTime + 5);
  };

  const handleSegmentClick = (index) => {
    setSelectedSegment(index);
    setCurrentTime(segments[index].startTime);
  };

  const handleGenerateVoice = () => {
    setIsGenerating(true);
    setTimeout(() => setIsGenerating(false), 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Background Effects */}
      <div className="fixed inset-0 opacity-20">
        <div className="w-full h-full" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3Cpattern id='grid' width='10' height='10' patternUnits='userSpaceOnUse'%3E%3Cpath d='M 10 0 L 0 0 0 10' fill='none' stroke='rgba(148,163,184,0.03)' stroke-width='0.5'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100' height='100' fill='url(%23grid)'/%3E%3C/svg%3E")`
        }}></div>
      </div>
      
      <div className="relative z-10 max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">V</span>
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              Video Editor Studio
            </h1>
          </div>
          <p className="text-slate-400 text-sm">Create, edit, and sync your video content with precision</p>
        </div>



        {/* Video Preview Section */}
        {selectedVideo && (
          <div className="mb-2 text-slate-400">
            Currently editing: <span className="font-semibold text-purple-400">{selectedVideo.title}</span>
          </div>
        )}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 mb-8 shadow-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white text-lg">📼</span>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-white">Video Preview</h2>
                  <p className="text-slate-400 text-sm">Interactive timeline playback</p>
                </div>
                <button
                  onClick={() => navigate('/templates')}
                  className="group flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600/80 text-slate-300 hover:text-white rounded-lg transition-all duration-200 shadow-md hover:shadow-lg text-sm font-medium"
                >
                  <LayoutGrid size={16} />
                  Change Template
                </button>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={handlePlayPause}
                className="group flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5"
              >
                {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                <span className="font-medium">{isPlaying ? 'Pause' : 'Play'}</span>
              </button>
              <button
                onClick={handleRewind}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-700/80 text-slate-200 rounded-xl hover:bg-slate-600/80 transition-all duration-200 hover:-translate-y-0.5"
              >
                <RotateCcw size={18} />
                <span className="font-medium">-5s</span>
              </button>
              <button
                onClick={handleFastForward}
                className="flex items-center gap-2 px-4 py-2.5 bg-slate-700/80 text-slate-200 rounded-xl hover:bg-slate-600/80 transition-all duration-200 hover:-translate-y-0.5"
              >
                <RotateCw size={18} />
                <span className="font-medium">+5s</span>
              </button>
            </div>
          </div>
          
          <div className="relative">
            <div className="w-full h-80 bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl border border-slate-700/50 flex items-center justify-center overflow-hidden group">
              {/* Animated background */}
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-emerald-500/10 animate-pulse"></div>
              
              <div className="relative text-center z-10">
                <div className="text-6xl mb-4 animate-bounce">🎬</div>
                <div className="text-white text-lg font-medium mb-2">Video frame playing in sync</div>
                <div className="text-slate-400 text-sm mb-4">Selected: {currentSegment.label}</div>
                
                {/* Progress bar */}
                <div className="w-full bg-slate-800/50 aspect-video rounded-xl shadow-lg overflow-hidden relative group">
                  <div 
                    className={`h-full bg-gradient-to-r ${currentSegment.color} rounded-full transition-all duration-300`}
                    style={{ width: `${(currentTime / 13.5) * 100}%` }}
                  ></div>
                </div>
                <div className="text-slate-300 text-xs mt-2">
                  {currentTime.toFixed(1)}s / 13.5s
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Timeline Segments */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl overflow-hidden mb-8 shadow-2xl">
          <div className="p-4 border-b border-slate-700/50">
            <h3 className="text-lg font-semibold text-white mb-1">Timeline Segments</h3>
            <p className="text-slate-400 text-sm">Click any segment to edit its content</p>
          </div>
          
          <div className="grid grid-cols-5">
            {segments.map((segment, index) => (
              <button
                key={segment.id}
                onClick={() => handleSegmentClick(index)}
                className={`group relative p-6 border-r border-slate-700/50 last:border-r-0 transition-all duration-300 hover:bg-slate-700/30 ${
                  selectedSegment === index 
                    ? 'bg-slate-700/50' 
                    : ''
                }`}
              >
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${segment.color} ${
                  selectedSegment === index ? 'opacity-100' : 'opacity-30 group-hover:opacity-60'
                } transition-opacity duration-300`}></div>
                
                <div className="text-center">
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${
                    selectedSegment === index ? 'text-white' : 'text-slate-300 group-hover:text-white'
                  }`}>
                    {segment.label}
                  </div>
                  <div className={`text-sm transition-colors duration-300 ${
                    selectedSegment === index ? 'text-slate-300' : 'text-slate-500 group-hover:text-slate-400'
                  }`}>
                    {segment.startTime}s–{segment.endTime}s
                  </div>
                  <div className={`text-xs mt-1 transition-colors duration-300 ${
                    selectedSegment === index ? 'text-slate-400' : 'text-slate-600'
                  }`}>
                    {segment.speaker}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Editable Segment */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-3 h-6 bg-gradient-to-b ${currentSegment.color} rounded-full`}></div>
            <h3 className="text-xl font-semibold text-white">Edit {currentSegment.label}</h3>
            <div className="ml-auto text-slate-400 text-sm">
              {segmentDuration.toFixed(1)}s available
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Info & Original */}
            <div className="space-y-6">
              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">🗣️</span>
                  </div>
                  <div>
                    <div className="text-white font-medium">{currentSegment.speaker}</div>
                    <div className="text-slate-400 text-sm">Speaker</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">📍</span>
                  </div>
                  <div>
                    <div className="text-white font-medium">
                      {currentSegment.startTime}s → {currentSegment.endTime}s
                    </div>
                    <div className="text-slate-400 text-sm">
                      Duration: {segmentDuration.toFixed(1)} seconds
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30">
                <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                  <span className="text-lg">🎵</span>
                  Original Transcript
                </h4>
                <p className="text-slate-300 italic leading-relaxed">
                  "{currentSegment.originalText}"
                </p>
              </div>
            </div>

            {/* Right Column - Editor */}
            <div className="space-y-6">
              <div>
                <label className="flex items-center gap-2 text-white font-medium mb-3">
                  <Edit3 size={16} />
                  Edit Transcript
                </label>
                <div className="relative">
                  <textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    className="w-full h-32 p-4 bg-slate-900/80 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 resize-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200"
                    placeholder="Enter your edited text here..."
                  />
                  <div className="absolute bottom-3 right-3 text-xs text-slate-400">
                    {editText.length} chars
                  </div>
                </div>
                
                <div className="flex justify-between items-center mt-2 text-sm">
                  <span className="text-slate-400">
                    Estimated: {editedDuration.toFixed(1)}s
                  </span>
                  <span className={`font-medium ${exceedsLimit ? 'text-red-400' : 'text-emerald-400'}`}>
                    {exceedsLimit ? 'Over limit' : 'Within limit'}
                  </span>
                </div>
              </div>

              {exceedsLimit && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="text-red-400 mt-0.5 flex-shrink-0" size={20} />
                    <div>
                      <div className="text-red-400 font-medium mb-1">
                        Duration Exceeded
                      </div>
                      <div className="text-red-300 text-sm">
                        Your edit is {editedDuration.toFixed(1)}s but only {segmentDuration.toFixed(1)}s available. 
                        Try shortening the text or split across segments.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-4 pt-8 border-t border-slate-700/50 mt-8">
            <button 
              onClick={handleGenerateVoice}
              disabled={isGenerating}
              className="group flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl hover:from-emerald-600 hover:to-teal-600 transition-all duration-200 shadow-lg hover:shadow-emerald-500/25 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isGenerating ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <Volume2 size={18} />
              )}
              <span className="font-medium">
                {isGenerating ? 'Generating...' : 'Generate Voice'}
              </span>
              {!isGenerating && <Sparkles size={16} className="opacity-70" />}
            </button>
            
            <button className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl hover:from-blue-600 hover:to-purple-600 transition-all duration-200 shadow-lg hover:shadow-blue-500/25 hover:-translate-y-0.5">
              <span className="text-lg">🎧</span>
              <span className="font-medium">Preview Audio</span>
            </button>
            
            <button className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:from-purple-600 hover:to-pink-600 transition-all duration-200 shadow-lg hover:shadow-purple-500/25 hover:-translate-y-0.5">
              <Eye size={18} />
              <span className="font-medium">Lip Sync Preview</span>
            </button>
            
            <button 
              className={`flex items-center gap-3 px-6 py-3 rounded-xl transition-all duration-200 font-medium ${
                exceedsLimit 
                  ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed border border-slate-600/30' 
                  : 'bg-gradient-to-r from-slate-600 to-slate-700 text-white hover:from-slate-500 hover:to-slate-600 shadow-lg hover:shadow-slate-500/25 hover:-translate-y-0.5'
              }`}
              disabled={exceedsLimit}
            >
              <Save size={18} />
              Save Changes
            </button>
          </div>

          {/* Final Warning */}
          <div className="flex items-center gap-3 mt-6 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <div className="w-8 h-8 bg-gradient-to-r from-amber-500 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white text-sm">⚠️</span>
            </div>
            <div className="text-amber-400 text-sm">
              <span className="font-medium">Important:</span> All segments must stay within their original time duration for proper video sync.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}