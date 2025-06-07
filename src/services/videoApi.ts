import { VideoProject, VideoTemplate } from '../types/video';

const API_BASE_URL = '/api/v1'; // Update this with your actual API base URL

/**
 * Fetches a video project by ID from the backend
 */
export async function fetchVideoProject(projectId: string): Promise<VideoProject> {
  try {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch project: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching video project:', error);
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
    return await response.json();
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
