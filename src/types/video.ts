/**
 * Types for Video Editor data models
 */

/**
 * Represents a single video template
 */
export interface VideoTemplate {
  id: string;
  title: string;
  description?: string;
  thumbnailUrl: string;
  duration: number; // in seconds
  createdAt?: string; // ISO date string
  updatedAt?: string; // ISO date string
  status?: 'draft' | 'published' | 'archived';
  tags?: string[];
  aspectRatio?: '16:9' | '9:16' | '1:1' | '4:5';
  resolution?: {
    width: number;
    height: number;
  };
}

/**
 * Represents a speaker in the video
 */
export interface Speaker {
  id: string;
  name: string;
  role?: string;
  avatarUrl?: string;
  voiceProfileId?: string; // Reference to voice synthesis profile if applicable
}

/**
 * Represents a single segment of the video with editable text
 */
export interface VideoSegment {
  id: string;
  videoId: string; // Reference to parent video
  order: number;
  startTime: number; // in seconds
  endTime: number;   // in seconds
  originalText: string;
  editedText?: string;
  speakerId: string;  // Reference to Speaker
  status?: 'pending' | 'processing' | 'processed' | 'error';
  metadata?: {
    confidence?: number; // Speech-to-text confidence score
    words?: Array<{
      word: string;
      startTime: number;
      endTime: number;
      confidence: number;
    }>;
  };
  // Visual styling for the segment in the UI
  style?: {
    color?: string;
    gradient?: string; // e.g., 'from-purple-500 to-pink-500'
  };
}

/**
 * Represents the complete video project with all its segments and metadata
 */
export interface VideoProject {
  video: VideoTemplate;
  segments: VideoSegment[];
  speakers: Speaker[];
  // Additional project metadata
  projectInfo?: {
    lastEdited: string; // ISO date string
    version: string;
    createdBy: string;
    language: string; // e.g., 'en-US', 'es-ES'
  };
}

/**
 * Represents the state of the video player in the editor
 */
export interface VideoPlayerState {
  isPlaying: boolean;
  currentTime: number;
  isMuted: boolean;
  volume: number;
  playbackRate: number;
  selectedSegmentId: string | null;
}

/**
 * Represents changes made to a segment
 */
export interface SegmentEdit {
  segmentId: string;
  field: 'text' | 'speaker' | 'timing';
  value: any;
  timestamp: string; // ISO date string
  author?: string;
}

/**
 * Represents the state of the video editor
 */
export interface VideoEditorState {
  project: VideoProject;
  player: VideoPlayerState;
  editHistory: SegmentEdit[];
  // UI state
  isLoading: boolean;
  error: string | null;
  // Current editing focus
  activeSegmentId: string | null;
  // Selection state for batch operations
  selectedSegmentIds: string[];
}
