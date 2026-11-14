export type NavigationTab =
  // Core Customer Workspace (Sheet 1, 2, 6)
  | 'home'
  | 'chat'
  | 'tasks'
  | 'files'
  | 'profile'
  // Onboarding & Auth screens (Sheet 1, 3, 5, 6)
  | 'splash'
  | 'onboarding'
  | 'login'
  | 'register'
  | 'welcome_success'
  // Tools & Capabilities (Sheet 1, 2, 3, 5)
  | 'tools_catalog'
  | 'research'
  | 'create'
  | 'analyse'
  | 'code'
  | 'agents'
  // Workflow & Artifacts (Sheet 6)
  | 'workflow_progress'
  | 'artifacts_result'
  // Connectivity & Learning (Sheet 3, 5)
  | 'wifi'
  | 'devices_connected'
  | 'edutech'
  | 'edutech_lesson'
  | 'benefits'
  | 'analytics'
  // Support & Settings (Sheet 3, 6)
  | 'notifications'
  | 'help_faq'
  // Captive Portal (Sheet 3)
  | 'captive'
  | 'captive_terms'
  | 'captive_otp'
  | 'captive_success'
  | 'wifi_session'
  | 'account_upgrade'
  | 'partner_access_promo'
  // B2B Partner Portal (Sheet 4)
  | 'partner'
  | 'partner_login'
  | 'partner_promo'
  | 'partner_locations'
  | 'partner_qr'
  | 'partner_packages'
  | 'partner_analytics'
  | 'partner_live_sessions'
  | 'partner_gateway_config'
  | 'partner_staff'
  | 'partner_api_settings'
  // Wi-Fi Management & Tools (Sheet 5)
  | 'speedtest'
  | 'device_access_control'
  | 'partner_vouchers'
  | 'token_ledger'
  | 'security_settings';

export type DeviceFrameMode = 'mobile' | 'tablet' | 'desktop' | 'fullscreen';

export interface TaskItem {
  id: string;
  title: string;
  time: string;
  completed: boolean;
  category: string;
  deadline?: string;
  credits?: number;
}

export interface WorkflowStep {
  id: string;
  agentName: string;
  role: string;
  status: 'completed' | 'in_progress' | 'pending';
  progress?: number;
  outputSummary?: string;
}

export interface ArtifactFile {
  id: string;
  name: string;
  size: string;
  date: string;
  type: 'pdf' | 'docx' | 'image' | 'xlsx' | 'pptx' | 'code';
  url?: string;
}

export interface AIAgent {
  id: string;
  name: string;
  specialty: string;
  description: string;
  iconName: string;
  color: string;
  creditsRequired: number;
  active?: boolean;
  capabilityTags?: string[];
  toolKeys?: string[];
  configurationId?: string;
}

export interface ConnectedDevice {
  id: string;
  name: string;
  ip: string;
  type: 'phone' | 'laptop' | 'tablet' | 'tv' | 'iot';
  connectedAt: string;
  bandwidth: string;
}

export interface EduTechModule {
  id: string;
  title: string;
  duration: string;
  level: string;
  rating: number;
  reviewsCount: string;
  lessons: string[];
}

export interface PartnerLocation {
  id: string;
  name: string;
  type: string;
  address: string;
  status: 'active' | 'inactive';
  plan: 'Basic' | 'Business' | 'Enterprise';
  dailyUsers: number;
  totalAiAccess: number;
  ssid: string;
}
