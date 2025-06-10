import { VideoProject, VideoTemplate, VideoSegment, Speaker } from '../types/video';

const API_BASE_URL = 'http://localhost:8000/api/v1'; // Backend API base URL

interface ApiVideoProject {
  title: string;
  description: string;
  is_public: boolean;
  metadata: {
    video_duration: number;
    total_segments: number;
    total_segments_duration: number;
    processing_timestamp: number;
    processing_notes: string;
    segment_stats: {
      min_duration: number;
      max_duration: number;
      avg_duration: number;
      silent_segments: number;
      spoken_segments: number;
    };
  };
  videos: Array<{
    title: string;
    file_path: string;
    duration: number;
    segments: Array<{
      start_time: number;
      end_time: number;
      text: string;
      is_silence: boolean;
    }>;
  }>;
}

/**
 * Fetches a video template by ID from the backend and transforms it to match the VideoProject type
 */
export async function fetchVideoProject(templateId: string): Promise<VideoProject> {
  try {
    const response = await fetch(`${API_BASE_URL}/templates/${templateId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch template: ${response.statusText}`);
    }
    
    const data: ApiVideoProject = await response.json();
    const video = data.videos[0]; // Take the first video
    
    // Transform the API response to match VideoProject type
    const videoTemplate: VideoTemplate = {
      id: templateId,
      title: data.title,
      description: data.description,
      thumbnailUrl: '/placeholder-thumbnail.jpg', // Default thumbnail
      duration: data.metadata.video_duration,
      aspectRatio: '16:9', // Default aspect ratio
    };

    const segments: VideoSegment[] = video.segments.map((segment, index) => ({
      id: `segment_${index + 1}`,
      videoId: templateId,
      order: index + 1,
      startTime: segment.start_time,
      endTime: segment.end_time,
      originalText: segment.text,
      editedText: segment.text,
      status: 'processed',
      speakerId: 'speaker_1', // Assign default speaker ID to match the speaker we create below
    }));

    const defaultSpeaker: Speaker = {
      id: 'speaker_1',
      name: 'Default Speaker',
      role: 'Narrator',
      avatarUrl: '/default-avatar.png',
    };

    return {
      video: videoTemplate,
      segments,
      speakers: [defaultSpeaker],
      projectInfo: {
        lastEdited: new Date().toISOString(),
        version: '1.0.0',
        createdBy: 'System',
        language: 'en-US',
      },
    };
  } catch (error) {
    console.error('Error fetching video template:', error);
    throw error;
  }
}

/**
 * Fetches available video templates
 */
export async function fetchVideoTemplates(): Promise<VideoTemplate[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/templates`);
    if (!response.ok) {
      throw new Error(`Failed to fetch templates: ${response.statusText}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching video templates:', error);
    throw error;
  }
}

/**
 * Updates a video segment on the backend
 */
export async function updateVideoSegment(
  projectId: string,
  segmentId: string,
  updates: Partial<{
    editedText: string;
    speakerId: string;
    startTime: number;
    endTime: number;
  }>
): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/projects/${projectId}/segments/${segmentId}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update segment: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error updating video segment:', error);
    throw error;
  }
}

/**
 * Saves the current state of the video project
 */
export async function saveVideoProject(project: VideoProject): Promise<void> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/projects/${project.video.id}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(project),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to save project: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Error saving video project:', error);
    throw error;
  }
}

/**
 * Creates a new video project from a template
 */
export async function createProjectFromTemplate(templateId: string): Promise<VideoProject> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/templates/${templateId}/create-project`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to create project: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating project from template:', error);
    throw error;
  }
}
