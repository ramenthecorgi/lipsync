import { VideoProject, VideoTemplate, VideoSegment, Speaker } from '../types/video';
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
  // Return empty array if no speakers are provided
  if (speakers.length === 0) {
    console.error('No speakers provided for segments');
    return [];
  }

  const baseSegments = [
    {
      id: `${templateId}_seg1`,
      videoId: templateId,
      order: 1,
      startTime: 0.0,
      endTime: 5.2,
      originalText: 'Welcome to our video presentation. Today, we have something special for you.',
      speakerId: speakers[0 % speakers.length].id, // Use modulo to ensure we don't go out of bounds
      status: 'processed' as const,
      style: {
        gradient: 'from-purple-500 to-pink-500'
      }
    },
    {
      id: `${templateId}_seg2`,
      videoId: templateId,
      order: 2,
      startTime: 5.2,
      endTime: 12.5,
      originalText: 'In this segment, we will explore the main features and benefits of our product.',
      speakerId: speakers[1 % speakers.length].id,
      status: 'processed' as const,
      style: {
        gradient: 'from-blue-500 to-cyan-500'
      }
    },
    {
      id: `${templateId}_seg3`,
      videoId: templateId,
      order: 3,
      startTime: 12.5,
      endTime: 22.0,
      originalText: 'Let me show you how easy it is to get started with just a few simple steps.',
      speakerId: speakers[2 % speakers.length].id,
      status: 'processed' as const,
      style: {
        gradient: 'from-green-500 to-teal-500'
      }
    },
    {
      id: `${templateId}_seg4`,
      videoId: templateId,
      order: 4,
      startTime: 22.0,
      endTime: 30.0,
      originalText: 'Thank you for watching. We hope you found this presentation helpful and informative.',
      speakerId: speakers[3 % speakers.length].id,
      status: 'processed' as const,
      style: {
        gradient: 'from-amber-500 to-orange-500'
      }
    }
  ];

  return baseSegments;
};

// Create a project from a template ID
export const createDummyProject = (templateId: string): VideoProject | null => {
  const template = getTemplateById(templateId);
  if (!template) {
    console.error(`Template with ID ${templateId} not found`);
    return null;
  }

  // Select 2-4 random speakers for this project
  const shuffledSpeakers = [...dummySpeakers].sort(() => 0.5 - Math.random());
  const projectSpeakers = shuffledSpeakers.slice(0, 2 + Math.floor(Math.random() * 3));
  
  // Create segments for this project
  const segments = createSegments(templateId, projectSpeakers);
  
  // If no segments were created, return null
  if (segments.length === 0) {
    console.error('Failed to create segments for project');
    return null;
  }

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
export const dummyProjects: Record<string, VideoProject> = {};

// Only create projects for templates that exist
const templateIds = ['1', '2', '3', '4', '5', '6'];

// Create projects and filter out any null values
const projectEntries = templateIds
  .map((templateId, index) => {
    const project = createDummyProject(templateId);
    return project ? [`project_${index + 1}`, project] : null;
  })
  .filter((entry): entry is [string, VideoProject] => entry !== null);

// Convert the entries to an object
Object.assign(dummyProjects, Object.fromEntries(projectEntries));

// Helper function to get a project by ID
export const getDummyProject = (projectId: string): VideoProject | null => {
  return dummyProjects[projectId] || null;
};
