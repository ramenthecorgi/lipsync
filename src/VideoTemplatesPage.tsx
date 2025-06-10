import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, Edit } from 'lucide-react';

// Import the actual templates from dummyTemplates
import { dummyTemplates } from './data/dummyTemplates';

// Define the VideoTemplate interface
interface VideoTemplate {
  id: string;
  title: string;
  thumbnailUrl: string;
  duration: number; // in seconds
  description: string;
}

// Use the actual templates from dummyTemplates with proper typing
const dummyVideoTemplates: VideoTemplate[] = dummyTemplates.map(template => ({
  id: template.id,
  title: template.title,
  thumbnailUrl: template.thumbnailUrl,
  duration: template.duration,
  description: template.description || 'No description available' // Provide a default value for description
}));

export default function VideoTemplatesPage() {
  const [templates] = useState<VideoTemplate[]>(dummyVideoTemplates);
  const navigate = useNavigate();

  const handleSelectTemplate = (templateId: string) => {
    navigate(`/editor/${templateId}`);
    console.log(`Navigating to editor for template: ${templateId}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100">
      {/* Background Effects (consistent with VideoEditorInterface) */}
      <div className="fixed inset-0 opacity-20">
        <div className="w-full h-full" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3Cpattern id='grid' width='10' height='10' patternUnits='userSpaceOnUse'%3E%3Cpath d='M 10 0 L 0 0 0 10' fill='none' stroke='rgba(148,163,184,0.03)' stroke-width='0.5'/%3E%3C/pattern%3E%3C/defs%3E%3Crect width='100' height='100' fill='url(%23grid)'/%3E%3C/svg%3E")`
        }}></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto p-6 sm:p-8">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">VT</span>
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              Video Templates
            </h1>
          </div>
          <p className="text-slate-400 text-sm">Choose a template to start your video project.</p>
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {templates.map((template) => (
            <div 
              key={template.id} 
              className="bg-slate-800/70 backdrop-blur-md border border-slate-700/50 rounded-xl overflow-hidden shadow-xl transition-all duration-300 hover:shadow-purple-500/20 hover:border-purple-500/50 hover:-translate-y-1 flex flex-col"
            >
              <div className="relative aspect-video group">
                <img src={template.thumbnailUrl} alt={template.title} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <PlayCircle size={64} className="text-white/80" />
                </div>
                <span className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  {Math.floor(template.duration / 60)}:{String(template.duration % 60).padStart(2, '0')}
                </span>
              </div>
              <div className="p-5 flex flex-col flex-grow">
                <h3 className="text-xl font-semibold mb-2 text-slate-100">{template.title}</h3>
                <p className="text-slate-400 text-sm mb-4 flex-grow">{template.description}</p>
                <button 
                  onClick={() => handleSelectTemplate(template.id)}
                  className="mt-auto w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all duration-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900 font-medium"
                >
                  <Edit size={18} />
                  Edit this Template
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
