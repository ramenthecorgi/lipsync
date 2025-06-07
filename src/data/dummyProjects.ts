import { VideoProject, VideoSegment, Speaker } from '../types/video';
import { getTemplateById } from './dummyTemplates';

// Common speakers that can be used across different projects
export const dummySpeakers: Speaker[] = [
  {
    id: 'spk_1',
    name: 'Alex Johnson',
    role: 'Host',
    avatarUrl: 'https://randomuser.me/api/portraits/men/32.jpg',
    voiceProfileId: 'voice_alex_1'
  },
  {
    id: 'spk_2',
    name: 'Maria Garcia',
    role: 'Narrator',
    avatarUrl: 'https://randomuser.me/api/portraits/women/44.jpg',
    voiceProfileId: 'voice_maria_1'
  },
  {
    id: 'spk_3',
    name: 'David Kim',
    role: 'Expert',
    avatarUrl: 'https://randomuser.me/api/portraits/men/22.jpg',
    voiceProfileId: 'voice_david_1'
  },
  {
    id: 'spk_4',
    name: 'Sarah Wilson',
    role: 'Presenter',
    avatarUrl: 'https://randomuser.me/api/portraits/women/68.jpg',
    voiceProfileId: 'voice_sarah_1'
  }
];

// Helper function to create segments for a project
const createSegments = (templateId: string, speakers: Speaker[]): VideoSegment[] => {
  if (!speakers || speakers.length === 0) {
    console.error('Error in createSegments: No speakers provided. Returning empty segments.');
    // Fallback: either return empty or use a default speaker if available globally
    // For now, returning empty to highlight the issue if it occurs.
    return []; 
  }

  const baseSegmentsData = [
    {
      order: 1,
      startTime: 0.0,
      endTime: 5.2,
      originalText: 'Welcome to our video presentation. Today, we have something special for you.',
      style: { gradient: 'from-purple-500 to-pink-500' }
    },
    {
      order: 2,
      startTime: 5.2,
      endTime: 12.5,
      originalText: 'In this segment, we will explore the main features and benefits of our product.',
      style: { gradient: 'from-blue-500 to-cyan-500' }
    },
    {
      order: 3,
      startTime: 12.5,
      endTime: 22.0,
      originalText: 'Let me show you how easy it is to get started with just a few simple steps.',
      style: { gradient: 'from-green-500 to-teal-500' }
    },
    {
      order: 4,
      startTime: 22.0,
      endTime: 30.0,
      originalText: 'Thank you for watching. We hope you found this presentation helpful and informative.',
      style: { gradient: 'from-amber-500 to-orange-500' }
    }
  ];

  return baseSegmentsData.map((segmentData, index) => ({
    id: `${templateId}_seg${segmentData.order}`,
    videoId: templateId,
    order: segmentData.order,
    startTime: segmentData.startTime,
    endTime: segmentData.endTime,
    originalText: segmentData.originalText,
    // Use modulo to cycle through speakers if there are fewer speakers than segments
    speakerId: speakers[index % speakers.length].id,
    status: 'processed' as const,
    style: segmentData.style
  }));
};

// Create a project from a template ID
export const createDummyProject = (templateId: string): VideoProject | null => {
  const template = getTemplateById(templateId);
  if (!template) return null;

  // Select 2-4 random speakers for this project
  const shuffledSpeakers = [...dummySpeakers].sort(() => 0.5 - Math.random());
  const projectSpeakers = shuffledSpeakers.slice(0, 2 + Math.floor(Math.random() * 3));
  
  // Create segments for this project
  const segments = createSegments(templateId, projectSpeakers);

  return {
    video: {
      ...template,
      // Override template duration with actual segments duration
      duration: Math.max(...segments.map(s => s.endTime)),
    },
    segments,
    speakers: projectSpeakers,
    projectInfo: {
      lastEdited: new Date().toISOString(),
      version: '1.0.0',
      createdBy: 'user@example.com',
      language: 'en-US'
    }
  };
};

// Generate a few dummy projects for testing
export const dummyProjects: Record<string, VideoProject> = {
  'project_1': createDummyProject('template_1')!,
  'project_2': createDummyProject('template_2')!,
  'project_3': createDummyProject('template_3')!,
  'project_4': createDummyProject('template_4')!,
  'project_5': createDummyProject('template_5')!,
  'project_6': createDummyProject('template_6')!
};

// Helper function to get a project by ID
export const getDummyProject = (projectId: string): VideoProject | null => {
  return dummyProjects[projectId] || null;
};
