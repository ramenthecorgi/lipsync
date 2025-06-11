import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';
import { startVideoGeneration, TranscriptData } from './services/videoGenerationApi';

interface VideoGenerationState {
  isLoading: boolean;
  error: string | null;
  generatedVideoUrl: string | null;
}

export default function VideoGenerationPage() {
  const { videoId = '' } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  
  const [state, setState] = useState<VideoGenerationState>({
    isLoading: false,
    error: null,
    generatedVideoUrl: null
  });
  
  const [transcript, setTranscript] = useState<TranscriptData | null>(null);

  // Fetch transcript when component mounts
  useEffect(() => {
    const fetchTranscript = async () => {
      if (!videoId) return;
      
      try {
        // In a real app, you would fetch the transcript from your API
        // For now, we'll use a mock transcript
        const mockTranscript: TranscriptData = {
          title: `Video ${videoId}`,
          description: 'Generated video',
          is_public: false,
          videos: [
            {
              title: `Video ${videoId}`,
              file_path: `videos/${videoId}/source.mp4`,
              duration: 60,
              segments: [
                {
                  start_time: 0,
                  end_time: 5,
                  text: 'This is a test segment',
                  is_silence: false
                }
              ]
            }
          ]
        };
        
        setTranscript(mockTranscript);
      } catch (err) {
        setState(prev => ({ ...prev, error: 'Failed to load transcript' }));
        console.error('Error fetching transcript:', err);
      }
    };
    
    fetchTranscript();
  }, [videoId]);

  const startGeneration = async () => {
    if (!videoId || !transcript) return;
    
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      // Start the video generation process
      const response = await startVideoGeneration({
        videoPath: `videos/${videoId}/source.mp4`,
        transcript,
        outputPath: `videos/${videoId}/output.mp4`,
        testMode: true
      });
      
      // Handle the response directly
      if (response.error) {
        throw new Error(response.error);
      }
      
      setState(prev => ({
        ...prev,
        generatedVideoUrl: response.output_path,
        isLoading: false
      }));
      
    } catch (err) {
      console.error('Error during video generation:', err);
      setState(prev => ({
        ...prev,
        error: err instanceof Error ? err.message : 'Failed to generate video',
        isLoading: false
      }));
    }
  };
  
  // Start generation when component mounts and transcript is loaded
  useEffect(() => {
    if (transcript) {
      startGeneration();
    }
  }, [transcript]);

  const handleBack = () => {
    navigate(-1); // Go back to the editor
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Editor</span>
          </button>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
            Generating Your Video
          </h1>
          <div className="w-24"></div> {/* For spacing */}
        </div>

        {/* Main Content */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl p-8 shadow-xl border border-slate-700/50">
          {state.isLoading && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="relative w-24 h-24">
                  <Loader2 className="w-full h-full text-blue-500 animate-spin" />
                </div>
              </div>
              <h2 className="text-xl font-semibold mb-2">Generating your video...</h2>
              <p className="text-gray-400 mb-6">
                This may take a minute. Please don't close this page.
              </p>
            </div>
          )}

          {!state.isLoading && state.generatedVideoUrl && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center">
                  <CheckCircle className="w-12 h-12 text-green-500" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Video Generated Successfully!</h2>
              <p className="text-gray-300 mb-8">
                Your video has been successfully generated and is ready to download.
              </p>
              
              <div className="space-y-4">
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <video 
                    src={state.generatedVideoUrl} 
                    controls 
                    className="w-full rounded-md"
                  />
                </div>
                
                <div className="flex justify-center space-x-4">
                  <a
                    href={state.generatedVideoUrl}
                    download
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    Download Video
                  </a>
                  
                  <button
                    onClick={handleBack}
                    className="bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                  >
                    Back to Editor
                  </button>
                </div>
              </div>
            </div>
          )}

          {!state.isLoading && state.error && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="w-24 h-24 rounded-full bg-red-500/20 flex items-center justify-center">
                  <AlertCircle className="w-12 h-12 text-red-500" />
                </div>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Something went wrong</h2>
              <p className="text-red-400 mb-6">{state.error}</p>
              
              <div className="space-x-4">
                <button
                  onClick={startGeneration}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={handleBack}
                  className="bg-slate-600 hover:bg-slate-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
                >
                  Back to Editor
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
