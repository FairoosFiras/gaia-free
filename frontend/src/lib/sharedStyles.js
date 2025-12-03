// Shared Tailwind styles converted from shared.css
// This file provides Tailwind-based component styles to replace the old CSS variables and classes

import { cn } from './tailwindComponents';

// Base view component styles using Tailwind utilities
export const baseViewStyles = {
  container: 'rounded-xl p-0 shadow-lg transition-all duration-300 animate-slideInFade overflow-hidden hover:-translate-y-0.5 hover:shadow-xl',
  header: 'px-3 py-1 flex items-center gap-2 border-b border-white/10',
  icon: 'text-base leading-none opacity-90',
  title: 'text-sm font-semibold text-white drop-shadow-sm m-0',
  content: 'p-3',
  text: 'leading-normal text-sm',
  paragraph: 'mb-2 p-2 rounded-md last:mb-0',
};

// Section styles
export const sectionStyles = {
  container: 'mb-6 last:mb-0',
  header: 'flex items-center gap-2 mb-4',
  icon: 'w-5 h-5 rounded-full flex-shrink-0',
  title: 'text-lg font-semibold m-0',
  list: 'flex flex-col gap-3',
  item: 'p-3 rounded-md text-base leading-normal transition-all duration-200 hover:translate-x-1',
};

// Color themes for different view types using Tailwind's color system
export const viewThemes = {
  narrative: {
    bg: 'bg-gaia-light border border-gaia-success/30',
    headerBg: 'bg-gradient-to-r from-gaia-success/80 to-gaia-success/60',
    icon: 'text-gaia-success',
    paragraph: 'bg-gaia-success/10 text-gaia-text border-l-2 border-gaia-success',
    sectionIcon: 'bg-gaia-success',
    sectionTitle: 'text-gaia-success',
    item: 'bg-gaia-success/20 text-gaia-text',
  },
  turn: {
    bg: 'bg-gaia-light border border-gaia-border',
    headerBg: 'bg-gradient-to-r from-gaia-border to-gaia-light',
    icon: 'text-gaia-text',
    paragraph: 'bg-gaia-dark/50 text-gaia-text',
    sectionIcon: 'bg-gaia-border',
    sectionTitle: 'text-gaia-text',
    item: 'bg-gaia-dark/30 text-gaia-text',
  },
  characters: {
    bg: 'bg-gradient-to-br from-purple-900/40 to-indigo-900/30',
    headerBg: 'bg-gradient-to-r from-purple-800/60 to-indigo-800/50',
    icon: 'text-purple-400',
    paragraph: 'bg-purple-900/20 text-purple-100',
    sectionIcon: 'bg-purple-600',
    sectionTitle: 'text-purple-300',
    item: 'bg-purple-900/30 text-purple-100',
  },
  status: {
    bg: 'bg-gradient-to-br from-orange-900/40 to-amber-900/30',
    headerBg: 'bg-gradient-to-r from-orange-800/60 to-amber-800/50',
    icon: 'text-orange-400',
    paragraph: 'bg-orange-900/20 text-orange-100',
    sectionIcon: 'bg-orange-600',
    sectionTitle: 'text-orange-300',
    item: 'bg-orange-900/30 text-orange-100',
  },
  dm: {
    bg: 'bg-gradient-to-br from-gray-900/50 to-slate-900/40',
    headerBg: 'bg-gradient-to-r from-gray-800/70 to-slate-800/60',
    icon: 'text-gray-400',
    paragraph: 'bg-gray-900/30 text-gray-100',
    sectionIcon: 'bg-gray-600',
    sectionTitle: 'text-gray-300',
    item: 'bg-gray-900/40 text-gray-100',
  },
};

// Responsive styles for mobile
export const responsiveStyles = {
  view: 'lg:rounded-xl rounded-lg',
  header: 'lg:px-6 lg:py-5 px-4 py-4',
  title: 'lg:text-2xl text-xl',
  content: 'lg:p-6 p-4',
  text: 'lg:text-lg text-base',
  sectionTitle: 'lg:text-lg text-base',
  item: 'lg:text-base text-sm',
};

// Helper function to combine view styles with theme
export function getViewStyles(theme = 'narrative', customStyles = {}) {
  const selectedTheme = viewThemes[theme] || viewThemes.narrative;
  
  return {
    container: cn(
      baseViewStyles.container,
      selectedTheme.bg,
      responsiveStyles.view,
      customStyles.container
    ),
    header: cn(
      baseViewStyles.header,
      selectedTheme.headerBg,
      responsiveStyles.header,
      customStyles.header
    ),
    icon: cn(
      baseViewStyles.icon,
      selectedTheme.icon,
      customStyles.icon
    ),
    title: cn(
      baseViewStyles.title,
      responsiveStyles.title,
      customStyles.title
    ),
    content: cn(
      baseViewStyles.content,
      responsiveStyles.content,
      customStyles.content
    ),
    text: cn(
      baseViewStyles.text,
      responsiveStyles.text,
      customStyles.text
    ),
    paragraph: cn(
      baseViewStyles.paragraph,
      selectedTheme.paragraph,
      customStyles.paragraph
    ),
    section: {
      container: cn(sectionStyles.container, customStyles.sectionContainer),
      header: cn(sectionStyles.header, customStyles.sectionHeader),
      icon: cn(sectionStyles.icon, selectedTheme.sectionIcon, customStyles.sectionIcon),
      title: cn(sectionStyles.title, selectedTheme.sectionTitle, responsiveStyles.sectionTitle, customStyles.sectionTitle),
      list: cn(sectionStyles.list, customStyles.sectionList),
      item: cn(sectionStyles.item, selectedTheme.item, responsiveStyles.item, customStyles.sectionItem),
    },
  };
}

// Utility classes that replace the CSS utility classes
export const utilityClasses = {
  // Text alignment
  textAlign: {
    center: 'text-center',
    left: 'text-left',
    right: 'text-right',
    justify: 'text-justify',
  },
  
  // Margin utilities
  margin: {
    top: {
      0: 'mt-0',
      1: 'mt-1',
      2: 'mt-2',
      3: 'mt-3',
      4: 'mt-4',
      5: 'mt-5',
      6: 'mt-6',
    },
    bottom: {
      0: 'mb-0',
      1: 'mb-1',
      2: 'mb-2',
      3: 'mb-3',
      4: 'mb-4',
      5: 'mb-5',
      6: 'mb-6',
    },
  },
  
  // Padding utilities
  padding: {
    all: {
      0: 'p-0',
      1: 'p-1',
      2: 'p-2',
      3: 'p-3',
      4: 'p-4',
      5: 'p-5',
      6: 'p-6',
    },
  },
  
  // Flexbox utilities
  flex: {
    display: 'flex',
    column: 'flex-col',
    row: 'flex-row',
    itemsCenter: 'items-center',
    justifyCenter: 'justify-center',
    gap: {
      1: 'gap-1',
      2: 'gap-2',
      3: 'gap-3',
      4: 'gap-4',
    },
  },
};

// Export all utility functions from tailwindComponents for convenience
export { cn, getButtonClass, getCardClass, getInputClass, getModalClass } from './tailwindComponents';

// Export specific named exports for backward compatibility
export const sharedStyles = {
  baseView: baseViewStyles.container,
  baseHeader: baseViewStyles.header,
  baseIcon: baseViewStyles.icon,
  baseTitle: baseViewStyles.title,
  baseContent: baseViewStyles.content,
  baseText: baseViewStyles.text,
  baseParagraph: baseViewStyles.paragraph,
  baseSection: sectionStyles.container,
  baseSectionHeader: sectionStyles.header,
  baseSectionIcon: sectionStyles.icon,
  baseSectionTitle: sectionStyles.title,
  baseList: sectionStyles.list,
  baseItem: sectionStyles.item,
};

// Export narrative-specific styles for NarrativeView component
export const narrativeStyles = {
  // Main view container - matching conversation box style
  view: 'bg-gaia-light border border-gaia-success/30 shadow-lg h-full flex flex-col hover:shadow-xl rounded-lg',
  
  // Header styles - using gaia-success green like send button
  header: 'bg-gradient-to-r from-gaia-success/90 to-gaia-success/70 shrink-0 flex items-center gap-3 pr-5 rounded-t-lg',
  
  // Title that flexes to fill space
  title: 'flex-1 text-black font-bold',
  
  // Play button styles
  playButton: 'bg-black/20 border-2 border-black/40 rounded-full w-10 h-10 flex items-center justify-center cursor-pointer text-xl transition-all duration-200 ml-auto hover:bg-black/30 hover:border-black/60 hover:scale-110 hover:shadow-lg active:scale-95',
  playButtonPlaying: 'bg-red-500/30 border-red-500/60 animate-pulse-custom',
  
  // Content container with proper scrolling
  content: 'flex-1 overflow-y-auto overflow-x-hidden min-h-0 max-h-full p-5',
  
  // Scrollbar styles (using custom CSS classes since Tailwind doesn't support pseudo-elements)
  scrollbar: 'scrollbar-narrative',
  
  // Text styles - matching chat message font size
  text: 'text-gaia-text leading-relaxed',
  
  // Paragraph styles with user message background color but keeping borders for separation
  paragraph: 'indent-8 text-justify border-l-4 border-green-500 py-3 px-4 mb-4 last:mb-0 first:mt-0 bg-gradient-to-r from-[#2e4a30] to-[#234a26]',
  
  // Responsive styles
  mobile: {
    view: 'max-md:rounded-lg',
    header: 'max-md:py-3 max-md:px-4',
    title: 'max-md:text-lg',
    content: 'max-md:p-4',
    text: 'max-md:text-base'
  },
  
  // Selection styles
  selection: 'selection:bg-gaia-success/30 selection:text-white'
};