
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
  aspectRatio?: '16:9' | '9:16' | '1:1' | '4:5';
  resolution?: {
    width: number;
    height: number;
  };
}

/**
 * Coqui TTS voice settings for a speaker
 */
export interface CoquiVoiceSettings {
  voiceId?: string;          // Unique identifier for the voice
  name?: string;             // Display name of the voice
  language?: string;         // Language code (e.g., 'en', 'es')
  gender?: 'male' | 'female' | 'neutral';
  speakerEmbedding?: number[]; // Voice embedding for voice cloning
  modelName?: string;        // Specific TTS model to use
  speed?: number;            // Speaking rate (default: 1.0)
  pitch?: number;           // Voice pitch (default: 1.0)
  energy?: number;          // Speech energy (default: 1.0)
}

/**
 * Represents a speaker in the video
 */
export interface Speaker {
  id: string;
  name: string;
  role?: string;
  avatarUrl?: string;
  // Coqui TTS voice settings
  voiceSettings?: CoquiVoiceSettings;
  // Reference to voice synthesis profile if applicable
  voiceProfileId?: string;
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
  editedText?: string;  // User-edited version of the text
  speakerId?: string;  // ID of the speaker for this segment
  status?: 'pending' | 'processed' | 'error'; // Processing status of the segment

  // Visual styling for the segment in the UI
  style?: {
    color?: string;
    gradient?: string; // e.g., 'from-purple-500 to-pink-500'
  };
}

/**
 * Represents the complete video project with all its segments and metadata
 */
export interface VideoFile {
  title: string;
  file_path: string;
  duration: number;
  segments: Array<{
    start_time: number;
    end_time: number;
    text: string;
    is_silence: boolean;
  }>;
}

export interface VideoProject {
  video: VideoTemplate;
  videos: VideoFile[];
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
// Status of TTS synthesis operation
export interface TTSSynthesisStatus {
  segmentId: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress?: number; // 0-100
  error?: string;
  audioUrl?: string;
}

export interface VideoEditorState {
  project: VideoProject;
  player: VideoPlayerState;
  editHistory: SegmentEdit[];
  // UI state
  isLoading: boolean;
  isSynthesizing: boolean;
  synthesisQueue: string[]; // Queue of segment IDs waiting for TTS
  currentSynthesisStatus: Record<string, TTSSynthesisStatus>; // Status of current TTS operations
  error: string | null;
  // Current editing focus
  activeSegmentId: string | null;
  // Selection state for batch operations
  selectedSegmentIds: string[];
}
