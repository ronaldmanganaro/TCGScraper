export type TCGType = 'magic' | 'pokemon' | 'all';

export interface TCGInfo {
  id: TCGType;
  name: string;
  icon: string;
  color: string;
}

export const TCG_CATEGORIES: Record<TCGType, TCGInfo> = {
  magic: {
    id: 'magic',
    name: 'Magic: The Gathering',
    icon: '🧙',
    color: '#8B5CF6'
  },
  pokemon: {
    id: 'pokemon',
    name: 'Pokémon',
    icon: '⚡',
    color: '#EF4444'
  },
  all: {
    id: 'all',
    name: 'All TCGs',
    icon: '🎴',
    color: '#10B981'
  }
};

export interface ToolInfo {
  text: string;
  icon: string;
  path: string;
  tcgs: TCGType[];
  description: string;
  adminOnly?: boolean;
}

export const TOOL_CATEGORIES: ToolInfo[] = [
  {
    text: 'Dashboard',
    icon: '🏠',
    path: '/',
    tcgs: ['all'],
    description: 'Overview of all your TCG tools and data'
  },
  {
    text: 'Repricer',
    icon: '💲',
    path: '/repricer',
    tcgs: ['all'],
    description: 'Price optimization for all TCG marketplaces'
  },
  {
    text: 'EV Tools',
    icon: '🎰',
    path: '/ev-tools',
    tcgs: ['magic'],
    description: 'Expected Value calculations for Magic: The Gathering packs and boxes'
  },
  {
    text: 'Pokemon Tracker',
    icon: '⚡',
    path: '/pokemon-tracker',
    tcgs: ['pokemon'],
    description: 'Price tracking and analytics for Pokémon cards'
  },
  {
    text: 'Manabox Converter',
    icon: '📦',
    path: '/manabox',
    tcgs: ['magic'],
    description: 'Convert Manabox inventory exports for Magic: The Gathering'
  },
  {
    text: 'Manage Inventory',
    icon: '📋',
    path: '/inventory',
    tcgs: ['all'],
    description: 'Track and manage your complete TCG inventory'
  },
  {
    text: 'TCGPlayer Orders',
    icon: '🖨️',
    path: '/tcgplayer-orders',
    tcgs: ['all'],
    description: 'Process and print shipping labels for all TCG orders'
  }
];

export const ADMIN_TOOLS: ToolInfo[] = [
  {
    text: 'Cloud Control',
    icon: '☁️',
    path: '/cloud-control',
    tcgs: ['all'],
    description: 'Manage cloud infrastructure and deployments',
    adminOnly: true
  },
  {
    text: 'Update TCGPlayer IDs',
    icon: '🔄',
    path: '/update-tcgplayer-ids',
    tcgs: ['all'],
    description: 'Bulk update TCGPlayer product IDs',
    adminOnly: true
  }
];

export const getToolsForTCG = (tcgType: TCGType): ToolInfo[] => {
  return TOOL_CATEGORIES.filter(tool => 
    tcgType === 'all' || tool.tcgs.includes(tcgType) || tool.tcgs.includes('all')
  );
};

export const getAdminToolsForTCG = (tcgType: TCGType): ToolInfo[] => {
  return ADMIN_TOOLS.filter(tool => 
    tcgType === 'all' || tool.tcgs.includes(tcgType) || tool.tcgs.includes('all')
  );
};
