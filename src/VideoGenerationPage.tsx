import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Loader2, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react';

type GenerationStatus = 'generating' | 'completed' | 'error';

export default function VideoGenerationPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState<GenerationStatus>('generating');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    const generateVideo = async () => {
      try {
        // Simulate progress updates (replace with actual API call)
        const interval = setInterval(() => {
          setProgress(prev => {
            const newProgress = prev + Math.random() * 10;
            if (newProgress >= 100) {
              clearInterval(interval);
              setStatus('completed');
              // In a real app, this would be the URL from your backend
              setGeneratedVideoUrl(`/api/videos/${videoId}/generated`);
              return 100;
            }
            return newProgress;
          });
        }, 500);

        // In a real app, you would make an API call here
        // const response = await fetch(`/api/videos/${videoId}/generate`, {
        //   method: 'POST',
        //   // Add necessary body and headers
        // });

        return () => clearInterval(interval);
      } catch (err) {
        console.error('Generation failed:', err);
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Failed to generate video');
      }
    };

    generateVideo();
  }, [videoId]);

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
          {status === 'generating' && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="relative w-24 h-24">
                  <Loader2 className="w-full h-full text-purple-500 animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xl font-mono">{Math.round(progress)}%</span>
                  </div>
                </div>
              </div>
              <h2 className="text-xl font-semibold mb-2">Generating your video...</h2>
              <p className="text-slate-400 mb-6">
                This may take a minute. Please don't close this page.
              </p>
              <div className="w-full bg-slate-700/50 rounded-full h-2.5">
                <div 
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {status === 'completed' && generatedVideoUrl && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="w-24 h-24 rounded-full bg-green-500/20 flex items-center justify-center">
                  <CheckCircle className="w-12 h-12 text-green-500" />
                </div>
              </div>
              <h2 className="text-2xl font-bold mb-4">Video Ready!</h2>
              <p className="text-slate-400 mb-6">
                Your video has been successfully generated.
              </p>
              
              <div className="bg-black/50 rounded-lg overflow-hidden mb-6">
                <video 
                  src={generatedVideoUrl} 
                  controls 
                  autoPlay 
                  className="w-full max-h-[60vh]"
                />
              </div>
              
              <div className="flex gap-4 justify-center">
                <a
                  href={generatedVideoUrl}
                  download={`video-${videoId}.mp4`}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200"
                >
                  Download Video
                </a>
                <button
                  onClick={handleBack}
                  className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Back to Editor
                </button>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="flex justify-center mb-6">
                <div className="w-24 h-24 rounded-full bg-red-500/20 flex items-center justify-center">
                  <AlertCircle className="w-12 h-12 text-red-500" />
                </div>
              </div>
              <h2 className="text-2xl font-bold mb-4">Generation Failed</h2>
              <p className="text-slate-400 mb-6">
                {error || 'An unknown error occurred while generating your video.'}
              </p>
              <button
                onClick={handleBack}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Back to Editor
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
