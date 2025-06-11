const API_BASE_URL = 'http://localhost:8000/api/v1';

export type GenerationStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface TranscriptSegment {
  start_time: number;
  end_time: number;
  text: string;
  is_silence?: boolean;
}

export interface VideoTranscript {
  title: string;
  file_path: string;
  duration: number;
  segments: TranscriptSegment[];
  segment_count?: number;
}

export interface TranscriptMetadata {
  video_duration: number;
  total_segments: number;
  total_segments_duration: number;
  processing_timestamp?: string;
  processing_notes?: string;
  segment_stats?: Record<string, any>;
}

export interface TranscriptData {
  title: string;
  description: string;
  is_public: boolean;
  videos: VideoTranscript[];
  metadata?: TranscriptMetadata;
}

export interface VideoGenerationResponse {
  job_id: string;
  output_path: string;
  message: string;
  status?: 'success' | 'error';
  error?: string;
}

export interface StartVideoGenerationParams {
  videoPath: string;
  transcript: TranscriptData;
  outputPath?: string;
  jobId?: string;
  testMode?: boolean;
}

export const startVideoGeneration = async ({
  videoPath,
  transcript,
  outputPath = '',
  jobId = `job_${Date.now()}`,
  testMode = false
}: StartVideoGenerationParams): Promise<VideoGenerationResponse> => {
  try {
    const url = new URL(`${API_BASE_URL}/lipsync/generate-lipsync-from-transcript`);
    if (testMode) {
      url.searchParams.append('test_mode', 'true');
    }

    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: videoPath,
        transcript: transcript,
        output_path: outputPath,
        job_id: jobId
      } as const),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || 
        errorData.message || 
        `Failed to start video generation: ${response.statusText}`
      );
    }

    return response.json();
  } catch (error) {
    console.error('Error starting video generation:', error);
    throw error instanceof Error 
      ? error 
      : new Error('Failed to start video generation');
  }
}


