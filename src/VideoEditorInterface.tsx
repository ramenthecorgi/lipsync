// Paste your TSX component code here

import { useState, useEffect } from 'react';
import { Edit3, AlertTriangle, Sparkles, LayoutGrid, Film, Loader2 } from 'lucide-react'; // Removed Volume2, Eye
import { useParams, useNavigate } from 'react-router-dom';
import { VideoProject, VideoSegment } from './types/video';
import { fetchVideoProject } from './services/videoApi';

export default function VideoEditorInterface() {
  const { videoId: videoIdFromUrl } = useParams<{ videoId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<VideoProject | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    const loadProject = async () => {
      if (!videoIdFromUrl) {
        setError('No video ID provided');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const loadedProject = await fetchVideoProject(videoIdFromUrl);
        setProject(loadedProject);
        if (loadedProject.segments && loadedProject.segments.length > 0) {
          setSelectedSegmentId(loadedProject.segments[0].id);
          setEditText(loadedProject.segments[0].editedText || loadedProject.segments[0].originalText);
        }
      } catch (err: unknown) {
        console.error('Error loading project:', err);
        const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
        setError(`Failed to load project: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [videoIdFromUrl]);

  // Derived states from project
  const currentSegment = project?.segments.find((s: VideoSegment) => s.id === selectedSegmentId);
  const segmentDuration = currentSegment ? currentSegment.endTime - currentSegment.startTime : 0;

  const countWords = (text: string): number => {
    return text.trim() ? text.trim().split(/\s+/).filter((word: string) => word.length > 0).length : 0;
  };

  const [originalWordCount, setOriginalWordCount] = useState(0);
  const [editedWordCount, setEditedWordCount] = useState(0);
  const [exceedsLimit, setExceedsLimit] = useState(false);

  // Update word counts and warning state when editText or currentSegment changes
  useEffect(() => {
    if (currentSegment) {
      const original = countWords(currentSegment.originalText);
      const edited = countWords(editText);
      setOriginalWordCount(original);
      setEditedWordCount(edited);
      setExceedsLimit(Math.abs(edited - original) > 1);
    }
  }, [editText, currentSegment?.id]);

  // Update edit text when current segment changes
  useEffect(() => {
    if (currentSegment) {
      setEditText(currentSegment.editedText || currentSegment.originalText);
      // Optionally, set currentTime to the start of the selected segment
      // setCurrentTime(currentSegment.startTime);
    }
  }, [currentSegment?.id]); // Only run when segment ID changes

  const handleSegmentClick = (segmentId: string) => {
    setSelectedSegmentId(segmentId);
    const segment = project?.segments.find((s: VideoSegment) => s.id === segmentId);
    if (segment) {
      const videoElement = document.querySelector('video') as HTMLVideoElement | null;
      if (videoElement) {
        const seekTo = segment.startTime;
        // If metadata is already loaded we can seek immediately
        if (videoElement.readyState >= 1) {
          videoElement.currentTime = seekTo;
        } else {
          // Otherwise wait until metadata is loaded before seeking
          const onLoaded = () => {
            videoElement.currentTime = seekTo;
            videoElement.removeEventListener('loadedmetadata', onLoaded);
          };
          videoElement.addEventListener('loadedmetadata', onLoaded);
        }
      }
    }
  };

  const handleGenerateVoice = async () => {
    if (!videoIdFromUrl || !project) return;
    
    try {
      setIsGenerating(true);
      
      // Get the video URL from the first video in the project
      const videoUrl = project.videos[0]?.file_path || '';
      
      // Prepare transcript data in the format expected by the generation page
      const transcript = {
        title: project.video.title,
        description: project.video.description || '',
        is_public: false,
        videos: [
          {
            title: project.video.title,
            file_path: videoUrl,
            duration: project.video.duration,
            segments: project.segments.map(segment => ({
              start_time: segment.startTime,
              end_time: segment.endTime,
              text: segment.editedText || segment.originalText,
              is_silence: false // This would come from your segment data if available
            }))
          }
        ]
      };
      
      // Navigate to the generation page with video URL and transcript as state
      navigate(`/generate/${videoIdFromUrl}`, { 
        state: { videoUrl, transcript } 
      });
    } catch (err) {
      console.error('Error preparing for generation:', err);
      setError('Failed to prepare for generation. Please try again.');
    } finally {
      setIsGenerating(false);
    }
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
              <Film size={16} className="text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              {project?.video.title || 'Video Editor Studio'}
            </h1>
          </div>
          <p className="text-slate-400 text-sm">{project?.video.description || 'Create, edit, and sync your video content with precision'}</p>
        </div>

        {/* Video Preview Section */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 mb-8 shadow-2xl">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white text-lg">📼</span>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Video Preview</h2>
                <p className="text-slate-400 text-sm">Interactive timeline playback</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/templates')}
              className="group flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600/80 text-slate-300 hover:text-white rounded-lg transition-all duration-200 shadow-md hover:shadow-lg text-sm font-medium"
            >
              <LayoutGrid size={16} />
              Change Template
            </button>
          </div>
          
          <div className="relative">
            <div className="w-full bg-black rounded-xl border border-slate-700/50 overflow-hidden group aspect-video">
              {project?.videos?.[0]?.file_path ? (
                <video
                  // TODO: need to change the video path from localhost
                  src={`http://localhost:8000${project.videos[0].file_path}`}
                  className="w-full h-full object-contain"
                  controls
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
                  <div className="text-center">
                    <div className="text-6xl mb-4">🎬</div>
                    <div className="text-white text-lg font-medium mb-2">No video available</div>
                    <div className="text-slate-400 text-sm">Video file not found</div>
                  </div>
                </div>
              )}
            </div>
            

          </div>
        </div>

        {/* Timeline Segments */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl overflow-hidden mb-8 shadow-2xl">
          <div className="p-4 border-b border-slate-700/50">
            <h3 className="text-lg font-semibold text-white mb-1">Timeline Segments</h3>
            <p className="text-slate-400 text-sm">Click any segment to edit its content</p>
          </div>
          
          <div className="w-full flex flex-wrap">
            {project?.segments.map((segment: VideoSegment) => (
              <button
                key={segment.id}
                onClick={() => handleSegmentClick(segment.id)}
                className={`group relative p-6 border-r border-slate-700/50 last:border-r-0 transition-all duration-300 hover:bg-slate-700/30 flex-1 ${selectedSegmentId === segment.id 
                    ? 'bg-slate-700/50' 
                    : ''
                }`}
              >
                <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${segment.style?.gradient || 'from-gray-500 to-gray-600'} ${selectedSegmentId === segment.id ? 'opacity-100' : 'opacity-30 group-hover:opacity-60'
                } transition-opacity duration-300`}></div>
                
                <div className="text-center">
                  <div className={`font-semibold mb-2 transition-colors duration-300 ${selectedSegmentId === segment.id ? 'text-white' : 'text-slate-300 group-hover:text-white'
                  }`}>
                    Segment {segment.order} {/* Using order for label */}
                  </div>
                  <div className={`text-sm transition-colors duration-300 ${selectedSegmentId === segment.id ? 'text-slate-300' : 'text-slate-500 group-hover:text-slate-400'
                  }`}>
                    {segment.startTime.toFixed(1)}s–{segment.endTime.toFixed(1)}s
                  </div>

                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Editable Segment */}
        {currentSegment && (
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-2xl">
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-3 h-6 bg-gradient-to-b ${currentSegment.style?.gradient || 'from-gray-500 to-gray-600'} rounded-full`}></div>
            <h3 className="text-xl font-semibold text-white">Edit Segment {currentSegment.order}</h3>
            <div className="ml-auto text-slate-400 text-sm">
              {segmentDuration.toFixed(1)}s available
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Column - Info & Original */}
            <div className="space-y-6">
              <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    <span className="text-white text-sm">📍</span>
                  </div>
                  <div>
                    <div className="text-white font-medium">
                      {currentSegment.startTime.toFixed(1)}s → {currentSegment.endTime.toFixed(1)}s
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
                    {editedWordCount} words
                  </span>
                  <span className={`font-medium ${exceedsLimit ? 'text-red-400' : 'text-emerald-400'}`}>
                    {exceedsLimit ? 'Word count changed too much' : 'Within limit'}
                  </span>
                </div>
              </div>


            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 pt-8 border-t border-slate-700/50 mt-8">
            <div className="flex-1 flex flex-col sm:flex-row gap-4 items-start sm:items-center">
              <button 
                onClick={handleGenerateVoice}
                disabled={isGenerating || !currentSegment}
                className={`group flex items-center gap-3 px-6 py-3 rounded-xl transition-all duration-200 font-medium shadow-lg hover:-translate-y-0.5 ${isGenerating || !currentSegment ? 'bg-slate-700/50 text-slate-500 cursor-not-allowed border border-slate-600/30' : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 hover:shadow-purple-500/30'}`}
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={18} />
                    <span>Generate Voice & Sync</span>
                  </>
                )}
              </button>

              {exceedsLimit && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 w-full max-w-2xl">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="text-red-400 mt-0.5 flex-shrink-0" size={16} />
                    <div>
                      <div className="text-red-400 text-sm font-medium">
                        Word Count Warning
                      </div>
                      <div className="text-red-300 text-xs">
                        Changed from {originalWordCount} to {editedWordCount} words (keep within ±1)
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
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
        )}

        {/* Loading and Error States */}
        {isLoading && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="flex flex-col items-center p-8 bg-slate-800 rounded-xl shadow-2xl">
              <Loader2 size={48} className="text-purple-400 animate-spin mb-4" />
              <p className="text-white text-lg">Loading Video Project...</p>
            </div>
          </div>
        )}

        {error && !isLoading && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="flex flex-col items-center p-8 bg-red-800/50 border border-red-700 rounded-xl shadow-2xl text-white">
              <AlertTriangle size={48} className="text-red-400 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Error Loading Project</h3>
              <p className="text-red-300 mb-4">{error}</p>
              <button 
                onClick={() => navigate('/templates')}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium transition-colors"
              >
                Back to Templates
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}