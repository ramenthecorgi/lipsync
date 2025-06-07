import { VideoTemplate } from '../types/video';

export const dummyTemplates: VideoTemplate[] = [
  {
    id: 'template_1',
    title: 'Summer Vacation Highlights',
    description: 'A vibrant and energetic template perfect for showcasing your summer travel adventures. Bright colors and fast cuts.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1473&q=80',
    duration: 125,
    status: 'published',
    tags: ['summer', 'travel', 'highlights'],
    aspectRatio: '16:9',
    resolution: { width: 1920, height: 1080 },
    createdAt: '2023-06-01T10:00:00Z',
    updatedAt: '2023-06-01T10:00:00Z'
  },
  {
    id: 'template_2',
    title: 'Cooking Masterclass: Pasta',
    description: 'An elegant and informative template for cooking tutorials. Clean layout with space for ingredient lists and instructions.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1551183053-bf91a1d81111?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1472&q=80',
    duration: 320,
    status: 'published',
    tags: ['cooking', 'food', 'tutorial'],
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    createdAt: '2023-06-02T11:30:00Z',
    updatedAt: '2023-06-02T11:30:00Z'
  },
  {
    id: 'template_3',
    title: 'Tech Review: New Gadgets',
    description: 'A sleek and modern template for tech reviews. Dynamic animations and futuristic design elements.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80',
    duration: 180,
    status: 'published',
    tags: ['tech', 'review', 'gadgets'],
    aspectRatio: '16:9',
    resolution: { width: 1920, height: 1080 },
    createdAt: '2023-06-03T09:15:00Z',
    updatedAt: '2023-06-03T09:15:00Z'
  },
  {
    id: 'template_4',
    title: 'Fitness Challenge Day 10',
    description: 'A motivational and high-energy template for fitness content. Bold typography and inspiring visuals.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80',
    duration: 240,
    status: 'published',
    tags: ['fitness', 'challenge', 'workout'],
    aspectRatio: '1:1',
    resolution: { width: 1080, height: 1080 },
    createdAt: '2023-06-04T14:20:00Z',
    updatedAt: '2023-06-04T14:20:00Z'
  },
  {
    id: 'template_5',
    title: 'Corporate Presentation',
    description: 'A professional and clean template for corporate presentations. Minimalist design with clear data visualization options.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80',
    duration: 300,
    status: 'published',
    tags: ['corporate', 'presentation', 'business'],
    aspectRatio: '16:9',
    resolution: { width: 1920, height: 1080 },
    createdAt: '2023-06-05T10:10:00Z',
    updatedAt: '2023-06-05T10:10:00Z'
  },
  {
    id: 'template_6',
    title: 'Wedding Memories',
    description: 'A romantic and elegant template to cherish your wedding memories. Soft tones and beautiful transitions.',
    thumbnailUrl: 'https://images.unsplash.com/photo-1583939003579-730e3918a45a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1374&q=80',
    duration: 360,
    status: 'published',
    tags: ['wedding', 'memories', 'romantic'],
    aspectRatio: '9:16',
    resolution: { width: 1080, height: 1920 },
    createdAt: '2023-06-06T08:45:00Z',
    updatedAt: '2023-06-06T08:45:00Z'
  }
];

export const getTemplateById = (id: string): VideoTemplate | undefined => {
  return dummyTemplates.find(template => template.id === id);
};

export const getTemplatesByTag = (tag: string): VideoTemplate[] => {
  return dummyTemplates.filter(template => 
    template.tags?.some(t => t.toLowerCase() === tag.toLowerCase())
  );
};
