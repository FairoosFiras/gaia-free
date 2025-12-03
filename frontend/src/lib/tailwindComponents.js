// Reusable Tailwind component class names
// This centralizes our component styles for consistency and reusability

export const buttonStyles = {
  // Base button styles
  base: 'px-4 py-2 rounded-lg font-medium transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
  
  // Button variants
  primary: 'bg-gaia-accent text-white hover:bg-gaia-accent-hover',
  secondary: 'bg-gaia-light text-gaia-text border border-gaia-border hover:bg-gaia-border',
  success: 'bg-gaia-success text-black hover:bg-green-500 font-bold',
  danger: 'bg-gaia-error text-white hover:bg-red-600',
  warning: 'bg-gaia-warning text-black hover:bg-yellow-600',
  info: 'bg-gaia-info text-white hover:bg-blue-600',
  ghost: 'bg-transparent text-gaia-text hover:bg-gaia-light',
  
  // Size variants
  small: 'px-3 py-1 text-sm',
  medium: 'px-4 py-2',
  large: 'px-6 py-3 text-lg',
  
  // Special buttons
  gradient: 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:from-purple-600 hover:to-indigo-500 shadow-lg hover:shadow-xl hover:-translate-y-0.5',
  medieval: 'font-medieval bg-gradient-to-r from-amber-700 to-amber-900 text-amber-100 hover:from-amber-800 hover:to-amber-950 shadow-lg'
};

export const cardStyles = {
  // Base card styles
  base: 'bg-gaia-light border border-gaia-border rounded-lg p-4',
  
  // Card variants
  elevated: 'shadow-lg hover:shadow-xl transition-shadow',
  interactive: 'hover:border-gaia-accent cursor-pointer transition-colors',
  glass: 'bg-gaia-light/50 backdrop-blur-sm border-gaia-border/50',
  
  // Card sections
  header: 'text-lg font-semibold mb-3 pb-2 border-b border-gaia-border',
  body: 'text-gaia-text',
  footer: 'mt-4 pt-3 border-t border-gaia-border'
};

export const inputStyles = {
  // Base input styles
  base: 'w-full px-3 py-2 bg-gaia-dark border border-gaia-border rounded-md text-gaia-text placeholder-gaia-text-dim focus:outline-none focus:border-gaia-accent focus:ring-1 focus:ring-gaia-accent',
  
  // Input variants
  error: 'border-gaia-error focus:border-gaia-error focus:ring-gaia-error',
  success: 'border-gaia-success focus:border-gaia-success focus:ring-gaia-success',
  
  // Input sizes
  small: 'px-2 py-1 text-sm',
  medium: 'px-3 py-2',
  large: 'px-4 py-3 text-lg',
  
  // Special inputs
  textarea: 'resize-vertical min-h-[100px]',
  select: 'cursor-pointer'
};

export const modalStyles = {
  // Modal overlay
  overlay: 'fixed inset-0 bg-black/80 flex justify-center items-center z-[1000] p-5',
  
  // Modal content containers
  small: 'bg-gaia-light rounded-lg w-full max-w-[500px] max-h-[90vh] overflow-hidden shadow-2xl',
  medium: 'bg-gaia-light rounded-lg w-full max-w-[800px] max-h-[90vh] overflow-hidden shadow-2xl',
  large: 'bg-gaia-light rounded-lg w-full max-w-[1200px] max-h-[90vh] overflow-y-auto shadow-2xl',
  
  // Modal sections
  header: 'px-6 py-4 border-b border-gaia-border flex justify-between items-center',
  body: 'p-6 overflow-y-auto',
  footer: 'px-6 py-4 border-t border-gaia-border flex justify-end gap-3'
};

export const layoutStyles = {
  // Page layouts
  mainContainer: 'flex flex-col h-screen min-h-0',
  header: 'bg-gaia-border px-8 py-4 border-b-2 border-gaia-border flex justify-between items-center',
  content: 'flex-1 flex flex-row p-4 gap-4 h-full min-h-0 overflow-hidden',
  
  // Section layouts
  sidebar: 'w-64 bg-gaia-light border-r border-gaia-border p-4 overflow-y-auto',
  mainContent: 'flex-1 overflow-y-auto p-4',
  
  // Responsive layouts
  responsiveGrid: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4',
  responsiveFlex: 'flex flex-col md:flex-row gap-4'
};

export const textStyles = {
  // Headings
  h1: 'text-3xl font-bold text-gaia-text mb-4',
  h2: 'text-2xl font-bold text-gaia-text mb-3',
  h3: 'text-xl font-semibold text-gaia-text mb-2',
  h4: 'text-lg font-semibold text-gaia-text mb-2',
  
  // Text variants
  body: 'text-gaia-text',
  muted: 'text-gaia-text-dim',
  error: 'text-gaia-error',
  success: 'text-gaia-success',
  
  // Special text
  medieval: 'font-medieval text-gaia-accent',
  gradient: 'bg-gradient-to-r from-gaia-accent to-purple-400 bg-clip-text text-transparent'
};

export const animationStyles = {
  // Transitions
  fadeIn: 'animate-fadeIn',
  slideIn: 'animate-slideIn',
  
  // Interactive animations
  hover: 'transition-all duration-200 hover:scale-105',
  hoverLift: 'transition-transform duration-200 hover:-translate-y-1',
  
  // Loading animations
  pulse: 'animate-pulse',
  spin: 'animate-spin',
  
  // Special effects
  glow: 'animate-glow',
  shimmer: 'animate-shimmer'
};

export const gameStyles = {
  // Game-specific components
  chatBubble: 'mb-2 p-3 rounded-lg max-w-[90%]',
  userMessage: 'bg-gaia-success text-black ml-auto',
  dmMessage: 'bg-gaia-light text-gaia-text mr-auto',
  systemMessage: 'bg-gaia-border text-gaia-text-dim text-center italic text-sm',
  
  // Game sections
  narrativeSection: 'card medieval-theme p-6 mb-4',
  characterCard: 'card hover:border-gaia-accent transition-colors p-3',
  statusPanel: 'glass rounded-lg p-4 text-sm',
  
  // D&D specific
  diceRoll: 'inline-flex items-center gap-2 px-3 py-1 bg-gaia-accent/20 rounded-full text-gaia-accent font-bold',
  spellCard: 'card bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-purple-500/30'
};

// Helper function to combine class names
export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// Helper function to get button classes
export function getButtonClass(variant = 'primary', size = 'medium', additionalClasses = '') {
  return cn(buttonStyles.base, buttonStyles[variant], buttonStyles[size], additionalClasses);
}

// Helper function to get card classes
export function getCardClass(variant = 'base', additionalClasses = '') {
  return cn(cardStyles.base, cardStyles[variant], additionalClasses);
}

// Helper function to get input classes
export function getInputClass(variant = 'base', size = 'medium', additionalClasses = '') {
  return cn(inputStyles.base, inputStyles[variant], inputStyles[size], additionalClasses);
}

// Helper function to get modal classes
export function getModalClass(size = 'medium') {
  return {
    overlay: modalStyles.overlay,
    content: modalStyles[size],
    header: modalStyles.header,
    body: modalStyles.body,
    footer: modalStyles.footer
  };
}