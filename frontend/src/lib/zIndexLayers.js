// Centralized z-index management for consistent layering across the application
// Higher numbers appear above lower numbers

export const zIndexLayers = {
  // Base layers
  base: 0,
  content: 1,
  
  // Interactive elements
  dropdown: 1000,        // Regular dropdowns and select menus
  overlay: 1500,         // Semi-transparent overlays
  
  // Modal layers  
  modal: 2000,           // Modal backgrounds and containers
  modalContent: 2100,    // Content inside modals
  modalDropdown: 3000,   // Dropdowns inside modals
  
  // Popup layers
  popup: 4000,           // Image popups, tooltips
  popupContent: 4100,    // Content inside popups  
  popupDropdown: 5000,   // Dropdowns inside popups
  
  // Top layers
  notification: 6000,    // Toast notifications, alerts
  critical: 9999,        // Critical overlays that must always be on top
  systemMax: 99999       // Absolute maximum for system components
};

// Tailwind z-index classes corresponding to the layers above
export const zIndexClasses = {
  base: 'z-0',
  content: 'z-[1]',
  dropdown: 'z-[1000]',
  overlay: 'z-[1500]',
  modal: 'z-[2000]',
  modalContent: 'z-[2100]',
  modalDropdown: 'z-[3000]',
  popup: 'z-[4000]',
  popupContent: 'z-[4100]',
  popupDropdown: 'z-[5000]',
  notification: 'z-[6000]',
  critical: 'z-[9999]',
  systemMax: 'z-[99999]'
};

// Helper function to get the appropriate z-index class for a component
export const getZIndexClass = (layer) => {
  return zIndexClasses[layer] || zIndexClasses.base;
};

// Component-specific z-index mappings for clarity
export const componentZIndex = {
  // Modals
  campaignManagerModal: zIndexClasses.modal,
  campaignManagerDropdown: zIndexClasses.modalDropdown,
  
  // Image components
  imagePopupOverlay: zIndexClasses.popup,
  imagePopupContent: zIndexClasses.popupContent,
  imageGenerateDropdown: zIndexClasses.popupDropdown,
  imageGalleryModal: zIndexClasses.popup,
  
  // Select dropdowns
  selectDropdownInModal: zIndexClasses.modalDropdown,
  selectDropdownInPopup: zIndexClasses.popupDropdown,
  selectDropdownDefault: zIndexClasses.dropdown,
  
  // Voice/TTS components
  voiceSelectionPanel: zIndexClasses.content,
  voiceSelectionDropdown: zIndexClasses.dropdown,
  
  // Floating buttons
  floatingButton: zIndexClasses.overlay,
  transcriptionPanel: zIndexClasses.modal,
  
  // Notifications
  alertNotification: zIndexClasses.notification,
  errorMessage: zIndexClasses.notification
};

export default zIndexLayers;