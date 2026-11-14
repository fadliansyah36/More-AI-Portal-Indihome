'use client';

import React, { useEffect, useState } from 'react';
import { createSupabaseBrowserClient } from '@/lib/supabase/client';
import {
  Home,
  MessageSquare,
  CheckSquare,
  FolderClosed,
  User,
  Search,
  Sparkles,
  FileSpreadsheet,
  Code2,
  Layers,
  Wifi,
  GraduationCap,
  Gift,
  BarChart3,
  Bell,
  Zap,
  Building2,
  Menu,
  X,
  Compass,
  Grid,
  QrCode,
  Radio,
  Sliders,
  ChevronDown,
} from 'lucide-react';
import { NavigationTab } from '@/types/moreai';
import { MoreAiNetworkLockup, MoreAiIcon } from '@/components/branding/logos';
import { PWAInstallButton } from '@/components/pwa/pwa-install-button';
import { OfflineIndicator } from '@/components/pwa/offline-indicator';
import { AppNavbar, isPartnerTab } from '@/components/navigation/app-navbar';

// Views
import { HomeView } from '@/components/views/home-view';
import { ChatView } from '@/components/views/chat-view';
import { TasksView } from '@/components/views/tasks-view';
import { FilesView } from '@/components/views/files-view';
import { CreateView } from '@/components/views/create-view';
import { ResearchView } from '@/components/views/research-view';
import { AnalyseView } from '@/components/views/analyse-view';
import { CodeView } from '@/components/views/code-view';
import { AgentStudioView } from '@/components/views/agent-studio-view';
import { SkillsLibraryView } from '@/components/views/skills-library-view';
import { WifiManagementView } from '@/components/views/wifi-management-view';
import { EdutechView } from '@/components/views/edutech-view';
import { BenefitCreditView } from '@/components/views/benefit-credit-view';
import { AnalyticsView } from '@/components/views/analytics-view';
import { ProfileSettingsView } from '@/components/views/profile-settings-view';
import { CaptivePortalView } from '@/components/views/captive-portal-view';
import { PartnerPortalView } from '@/components/views/partner-portal-view';

// Standalone Reference Screens
import { SplashScreenView } from '@/components/views/splash-screen-view';
import { OnboardingScreenView } from '@/components/views/onboarding-screen-view';
import { AuthLoginView } from '@/components/views/auth-login-view';
import { AuthRegisterView } from '@/components/views/auth-register-view';
import { WelcomeSuccessView } from '@/components/views/welcome-success-view';
import { ToolsCatalogView } from '@/components/views/tools-catalog-view';
import { DevicesConnectedView } from '@/components/views/devices-connected-view';
import { NotificationsView } from '@/components/views/notifications-view';
import { HelpFaqView } from '@/components/views/help-faq-view';
import { EdutechLessonView } from '@/components/views/edutech-lesson-view';
import { PartnerPromoView } from '@/components/views/partner-promo-view';
import { PartnerAccessBannerView } from '@/components/views/partner-access-banner-view';
import { WorkflowProgressView } from '@/components/views/workflow-progress-view';
import { ArtifactsResultView } from '@/components/views/artifacts-result-view';

// Sheet 3 & 4 & 5 Dedicated Views
import { CaptiveTermsView } from '@/components/views/captive-terms-view';
import { CaptiveOtpView } from '@/components/views/captive-otp-view';
import { CaptiveSuccessView } from '@/components/views/captive-success-view';
import { WifiSessionView } from '@/components/views/wifi-session-view';
import { AccountUpgradeView } from '@/components/views/account-upgrade-view';
import { PartnerLoginView } from '@/components/views/partner-login-view';
import { PartnerLiveSessionsView } from '@/components/views/partner-live-sessions-view';
import { PartnerGatewayConfigView } from '@/components/views/partner-gateway-config-view';
import { PartnerStaffView } from '@/components/views/partner-staff-view';
import { PartnerApiSettingsView } from '@/components/views/partner-api-settings-view';
import { SpeedtestView } from '@/components/views/speedtest-view';
import { DeviceAccessControlView } from '@/components/views/device-access-control-view';
import { PartnerVouchersView } from '@/components/views/partner-vouchers-view';
import { TokenLedgerView } from '@/components/views/token-ledger-view';
import { SecuritySettingsView } from '@/components/views/security-settings-view';

// Modals
import { OnboardingModal } from '@/components/modals/onboarding-modal';
import { ScreenGalleryModal } from '@/components/modals/screen-gallery-modal';

export default function App() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('splash');
  const [showDrawerMenu, setShowDrawerMenu] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showScreenGallery, setShowScreenGallery] = useState(false);
  const [chatInitialPrompt, setChatInitialPrompt] = useState('');
  const [chatInitialAgentKey, setChatInitialAgentKey] = useState<'manus' | 'planning' | 'toolcall'>('manus');
  const [chatInitialAgentConfigurationId, setChatInitialAgentConfigurationId] = useState<string | null>(null);
  const [chatInitialSkillIds, setChatInitialSkillIds] = useState<string[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [drawerRole, setDrawerRole] = useState<'customer' | 'partner'>('customer');
  const [isBottomNavCollapsed, setIsBottomNavCollapsed] = useState(false);
  const isPublicEntry = ['splash', 'onboarding', 'login', 'register', 'welcome_success', 'partner_login'].includes(currentTab);

  // Restore deep links and authentication on direct visits / browser history.
  useEffect(() => {
    const resolveTab = () => {
      const path = window.location.pathname.replace(/\/+$/, '') || '/';
      const queryTab = new URLSearchParams(window.location.search).get('view') as NavigationTab | null;
      const pathTab: Record<string, NavigationTab> = {
        '/': 'splash',
        '/splash': 'splash',
        '/onboarding': 'onboarding',
        '/customer': 'home',
        '/customer/login': 'login',
        '/customer/register': 'register',
        '/partner': 'partner',
        '/mitra': 'partner',
        '/workflow': 'workflow_progress',
        '/workflow-progress': 'workflow_progress',
        '/login': 'login',
        '/register': 'register',
        '/partner/login': 'partner_login',
      };
      const next = path === '/' ? (queryTab || 'splash') : (pathTab[path] || queryTab);
      if (next) setCurrentTab(next);
    };
    const redirectProtectedRouteToRoleLogin = () => {
      const rawPath = window.location.pathname;
      const path = rawPath.length > 1 && rawPath.endsWith('/') ? rawPath.slice(0, -1) : rawPath;
      const requested = new URLSearchParams(window.location.search).get('view');
      const publicRoute = (path === '/' && (!requested || ['splash', 'onboarding', 'login', 'register', 'welcome_success'].includes(requested)))
        || ['/login', '/register', '/customer/login', '/customer/register', '/partner/login', '/splash', '/onboarding'].includes(path);
      if (publicRoute) return;
      const partnerEntry = path.startsWith('/partner') || path.startsWith('/mitra') || requested === 'partner' || Boolean(requested?.startsWith('partner_'));
      const authTab: NavigationTab = partnerEntry ? 'partner_login' : 'login';
      const authPath = partnerEntry ? '/partner/login' : '/customer/login';
      setCurrentTab(authTab);
      window.history.replaceState({ moreaiTab: authTab }, '', authPath);
    };

    resolveTab();
    window.addEventListener('popstate', resolveTab);
    let unsubscribeAuth = () => {};
    try {
      const supabase = createSupabaseBrowserClient();
      const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
        if (!session) {
          const path = window.location.pathname;
          const requested = new URLSearchParams(window.location.search).get('view');
          const publicRoute = (path === '/' && (!requested || ['splash', 'onboarding', 'login', 'register', 'welcome_success'].includes(requested)))
            || ['/login', '/register', '/customer/login', '/customer/register', '/partner/login', '/splash', '/onboarding'].includes(path);
          if (!publicRoute) {
            const partnerEntry = path.startsWith('/partner') || path.startsWith('/mitra') || requested === 'partner' || Boolean(requested?.startsWith('partner_'));
            const authTab: NavigationTab = partnerEntry ? 'partner_login' : 'login';
            const authPath = partnerEntry ? '/partner/login' : '/customer/login';
            setCurrentTab(authTab);
            window.history.replaceState({ moreaiTab: authTab }, '', authPath);
          }
        }
      });
      unsubscribeAuth = () => authListener.subscription.unsubscribe();
    } catch {
      // Keep public Splash/Onboarding routes usable even before Auth is configured;
      // protected Customer/Partner routes still fail closed to their role-specific login.
      redirectProtectedRouteToRoleLogin();
    }
    const restoreSession = async () => {
      try {
        const { data, error } = await createSupabaseBrowserClient().auth.getSession();
        if (error || !data.session) {
          const path = window.location.pathname.replace(/\/+$/, '') || '/';
          const requested = new URLSearchParams(window.location.search).get('view');
          const publicRoute = (path === '/' && (!requested || ['login', 'register', 'splash', 'onboarding', 'welcome_success'].includes(requested)))
            || ['/login', '/register', '/customer/login', '/customer/register', '/partner/login', '/splash', '/onboarding'].includes(path);
          if (!publicRoute) {
            const partnerEntry = path.startsWith('/partner') || path.startsWith('/mitra') || requested === 'partner' || Boolean(requested?.startsWith('partner_'));
            const authTab: NavigationTab = partnerEntry ? 'partner_login' : 'login';
            const authPath = partnerEntry ? '/partner/login' : '/customer/login';
            setCurrentTab(authTab);
            window.history.replaceState({ moreaiTab: authTab }, '', authPath);
          }
        }
      } catch {
        redirectProtectedRouteToRoleLogin();
      }
    };
    void restoreSession();
    return () => {
      window.removeEventListener('popstate', resolveTab);
      unsubscribeAuth();
    };
  // Auth is restored once on app entry; navigation state is managed below.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Quick navigation handler
  const handleNavigate = (tab: NavigationTab) => {
    const routeByTab: Partial<Record<NavigationTab, string>> = {
      splash: '/splash',
      onboarding: '/onboarding',
      home: '/customer',
      login: '/customer/login',
      register: '/customer/register',
      partner: '/partner',
      partner_login: '/partner/login',
      workflow_progress: '/workflow',
    };
    const nextUrl = routeByTab[tab] || ('/?view=' + encodeURIComponent(tab));
    if (window.location.pathname + window.location.search !== nextUrl) {
      window.history.pushState({ moreaiTab: tab }, '', nextUrl);
    }
    setCurrentTab(tab);
    setShowDrawerMenu(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleStartPrompt = (
    promptText: string,
    agentKey: 'manus' | 'planning' | 'toolcall' = 'manus',
    agentConfigurationId?: string | null,
  ) => {
    setChatInitialPrompt(promptText);
    setChatInitialAgentKey(agentKey);
    setChatInitialAgentConfigurationId(agentConfigurationId || null);
    setChatInitialSkillIds(skillIds);
    handleNavigate('chat');
  };

  return (
    <div className={`min-h-screen transition-colors ${isDarkMode ? 'dark bg-slate-950 text-slate-100' : 'bg-slate-100/90 text-slate-900'}`}>
      <OfflineIndicator />

      {/* Dedicated Global Navbar: Customer UI vs Mitra Partner UI (Full Width) */}
      {!['splash', 'onboarding', 'login', 'register', 'welcome_success', 'partner_login'].includes(currentTab) && <AppNavbar
        currentTab={currentTab}
        onNavigate={handleNavigate}
        isDarkMode={isDarkMode}
        onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
      />}

      {/* Main Full-Screen Layout */}
      <main className={`w-full max-w-full px-2 sm:px-6 lg:px-8 pt-2.5 sm:pt-4 ${isPublicEntry ? "pb-6 sm:pb-8" : "pb-36 sm:pb-32"}`}>
        <div className="w-full max-w-full bg-white dark:bg-slate-900 rounded-2xl sm:rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-xs p-3 sm:p-6 lg:p-8 min-h-[650px]">
          {/* Core Views */}
              {currentTab === 'home' && (
                <HomeView
                  onNavigate={handleNavigate}
                  onStartPrompt={handleStartPrompt}
                />
              )}

              {currentTab === 'chat' && (
                <ChatView
                  onBack={() => handleNavigate('home')}
                  initialPrompt={chatInitialPrompt}
                  initialAgentKey={chatInitialAgentKey}
                  initialAgentConfigurationId={chatInitialAgentConfigurationId}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'tasks' && (
                <TasksView
                  onOpenWorkspaceFiles={() => handleNavigate('files')}
                  onOpenWorkflow={() => handleNavigate('workflow_progress')}
                  onStartPrompt={handleStartPrompt}
                />
              )}

              {currentTab === 'files' && <FilesView />}

              {currentTab === 'create' && (
                <CreateView onNavigateToChat={handleStartPrompt} />
              )}

              {currentTab === 'research' && (
                <ResearchView
                  onBack={() => handleNavigate('home')}
                  onSelectTopic={handleStartPrompt}
                />
              )}

              {currentTab === 'analyse' && <AnalyseView onNavigateToChat={handleStartPrompt} />}

              {currentTab === 'code' && <CodeView onNavigateToChat={handleStartPrompt} />}

              {currentTab === 'skills' && <SkillsLibraryView />}

              {currentTab === 'agents' && (
                <AgentStudioView
                  onSelectAgentForChat={(agent, skillIds = []) =>
                    handleStartPrompt(
                      `Saya ingin bekerja dengan ${agent.name}. ${agent.description}`,
                      agent.id === 'planning' ? 'planning' : agent.id === 'toolcall' ? 'toolcall' : 'manus',
                      agent.configurationId,
                    )
                  }
                  onOpenWorkflow={() => handleNavigate('workflow_progress')}
                />
              )}

              {currentTab === 'wifi' && <WifiManagementView onNavigateTab={handleNavigate} />}

              {currentTab === 'edutech' && <EdutechView onStartPrompt={handleStartPrompt} />}

              {currentTab === 'benefits' && <BenefitCreditView onNavigateTab={handleNavigate} />}

              {currentTab === 'analytics' && <AnalyticsView />}

              {currentTab === 'profile' && (
                <ProfileSettingsView
                  onNavigateTab={handleNavigate}
                  isDarkMode={isDarkMode}
                  onToggleDarkMode={() => setIsDarkMode(!isDarkMode)}
                />
              )}

              {currentTab === 'captive' && (
                <CaptivePortalView
                  onBackToApp={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner' && (
                <PartnerPortalView initialMode="dashboard" onNavigateTab={handleNavigate} />
              )}

              {currentTab === 'partner_locations' && (
                <PartnerPortalView initialMode="locations" onNavigateTab={handleNavigate} />
              )}

              {currentTab === 'partner_qr' && (
                <PartnerPortalView initialMode="qr" onNavigateTab={handleNavigate} />
              )}

              {currentTab === 'partner_packages' && (
                <PartnerPortalView initialMode="packages" onNavigateTab={handleNavigate} />
              )}

              {currentTab === 'partner_analytics' && (
                <PartnerPortalView initialMode="analytics" onNavigateTab={handleNavigate} />
              )}

              {/* Standalone Reference Screens (Sheet 1 - 6) */}
              {currentTab === 'splash' && (
                <SplashScreenView onNavigate={handleNavigate} />
              )}

              {currentTab === 'onboarding' && (
                <OnboardingScreenView onNavigate={handleNavigate} />
              )}

              {currentTab === 'login' && (
                <AuthLoginView
                  onNavigate={handleNavigate}
                  onLoginSuccess={() => handleNavigate('home')}
                />
              )}

              {currentTab === 'register' && (
                <AuthRegisterView
                  onNavigate={handleNavigate}
                  onRegisterSuccess={() => handleNavigate('welcome_success')}
                />
              )}

              {currentTab === 'welcome_success' && (
                <WelcomeSuccessView onNavigate={handleNavigate} />
              )}

              {currentTab === 'tools_catalog' && (
                <ToolsCatalogView
                  onNavigateTab={handleNavigate}
                  onSelectToolForPrompt={handleStartPrompt}
                />
              )}

              {currentTab === 'devices_connected' && (
                <DevicesConnectedView onBack={() => handleNavigate('wifi')} />
              )}

              {currentTab === 'notifications' && (
                <NotificationsView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'help_faq' && (
                <HelpFaqView onBack={() => handleNavigate('home')} />
              )}

              {currentTab === 'edutech_lesson' && (
                <EdutechLessonView
                  onBack={() => handleNavigate('edutech')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_promo' && (
                <PartnerPromoView onBack={() => handleNavigate('partner')} />
              )}

              {currentTab === 'partner_access_promo' && (
                <PartnerAccessBannerView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'workflow_progress' && (
                <WorkflowProgressView
                  onBack={() => handleNavigate('tasks')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'artifacts_result' && (
                <ArtifactsResultView
                  onBack={() => handleNavigate('tasks')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {/* Sheet 3 Captive Portal Dedicated Screens */}
              {currentTab === 'captive_terms' && (
                <CaptiveTermsView
                  onBack={() => handleNavigate('captive')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'captive_otp' && (
                <CaptiveOtpView onBack={() => handleNavigate('captive_terms')} />
              )}

              {currentTab === 'captive_success' && (
                <CaptiveSuccessView onNavigateTab={handleNavigate} />
              )}

              {currentTab === 'wifi_session' && (
                <WifiSessionView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'account_upgrade' && (
                <AccountUpgradeView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {/* Sheet 4 B2B Partner Portal Dedicated Screens */}
              {currentTab === 'partner_login' && (
                <PartnerLoginView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_live_sessions' && (
                <PartnerLiveSessionsView
                  onBack={() => handleNavigate('partner')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_gateway_config' && (
                <PartnerGatewayConfigView
                  onBack={() => handleNavigate('partner')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_staff' && (
                <PartnerStaffView
                  onBack={() => handleNavigate('partner')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_api_settings' && (
                <PartnerApiSettingsView
                  onBack={() => handleNavigate('partner')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {/* Sheet 5 Wi-Fi Management & Tools Dedicated Screens */}
              {currentTab === 'speedtest' && (
                <SpeedtestView
                  onBack={() => handleNavigate('wifi')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'device_access_control' && (
                <DeviceAccessControlView
                  onBack={() => handleNavigate('wifi')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'partner_vouchers' && (
                <PartnerVouchersView
                  onBack={() => handleNavigate('home')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'token_ledger' && (
                <TokenLedgerView
                  onBack={() => handleNavigate('benefits')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {currentTab === 'security_settings' && (
                <SecuritySettingsView
                  onBack={() => handleNavigate('profile')}
                  onNavigateTab={handleNavigate}
                />
              )}

              {/* Clearance spacer ensuring content is never covered by bottom nav */}
              <div className="h-20 sm:h-12 w-full shrink-0" aria-hidden="true" />
        </div>
      </main>

      {/* Private workspace dock: never render on public/auth entry screens. */}
      {!isPublicEntry && (
      <>
      {/* Permanent Fixed Bottom Navigation Dock with collapse toggle */}
      {isBottomNavCollapsed ? (
        <div className="fixed bottom-3 left-0 right-0 z-40 flex justify-center pointer-events-none select-none animate-in fade-in duration-150">
          <button
            onClick={() => setIsBottomNavCollapsed(false)}
            className="pointer-events-auto flex items-center gap-2 px-4 py-2 rounded-full bg-slate-900/95 dark:bg-white/95 text-white dark:text-slate-900 text-xs font-bold shadow-2xl backdrop-blur-md border border-slate-700/80 dark:border-slate-300 hover:scale-105 active:scale-95 transition"
          >
            <Menu className="w-3.5 h-3.5 text-red-500" />
            <span>▲ Navigasi Bawah</span>
          </button>
        </div>
      ) : (
        <nav className="fixed bottom-0 left-0 right-0 z-40 px-2 sm:px-4 pb-[max(env(safe-area-inset-bottom),0.75rem)] pt-1 pointer-events-none select-none transition-all duration-200">
          <div className="max-w-lg mx-auto bg-white/95 dark:bg-slate-900/95 backdrop-blur-md rounded-2xl border border-slate-200/90 dark:border-slate-800 px-3 sm:px-4 py-2 shadow-2xl pointer-events-auto transition-all">
            {/* Subtle Mode Switch Indicator Bar with collapse button */}
            <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-100 dark:border-slate-800 text-[10px]">
              <span className="font-bold flex items-center gap-1.5">
                {isPartnerTab(currentTab) ? (
                  <>
                    <Building2 className="w-3 h-3 text-amber-500 shrink-0" />
                    <span className="text-slate-800 dark:text-slate-200 font-bold">Mode Mitra Partner (B2B)</span>
                  </>
                ) : (
                  <>
                    <User className="w-3 h-3 text-red-600 shrink-0" />
                    <span className="text-slate-800 dark:text-slate-200 font-bold">Mode Customer Workspace</span>
                  </>
                )}
              </span>
              <div className="flex items-center gap-2">

                <button
                  onClick={() => setIsBottomNavCollapsed(true)}
                  className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  title="Sembunyikan Menu Bawah"
                >
                  <ChevronDown className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Dynamic Bottom Tabs based on Role */}
            {isPartnerTab(currentTab) ? (
              <div className="grid grid-cols-4 gap-1">
                <button
                  onClick={() => handleNavigate('partner')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'partner'
                      ? 'text-slate-900 dark:text-white font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <Building2 className={`w-5 h-5 ${currentTab === 'partner' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Dashboard</span>
                </button>

                <button
                  onClick={() => handleNavigate('partner_live_sessions')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'partner_live_sessions'
                      ? 'text-slate-900 dark:text-white font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <Radio className={`w-5 h-5 ${currentTab === 'partner_live_sessions' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Live Tamu</span>
                </button>

                <button
                  onClick={() => handleNavigate('partner_qr')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'partner_qr'
                      ? 'text-slate-900 dark:text-white font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <QrCode className={`w-5 h-5 ${currentTab === 'partner_qr' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">QR Meja</span>
                </button>

                <button
                  onClick={() => handleNavigate('partner_gateway_config')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'partner_gateway_config'
                      ? 'text-slate-900 dark:text-white font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <Sliders className={`w-5 h-5 ${currentTab === 'partner_gateway_config' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Gateway</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-4 gap-1">
                <button
                  onClick={() => handleNavigate('home')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'home'
                      ? 'text-red-600 font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <Home className={`w-5 h-5 ${currentTab === 'home' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Home</span>
                </button>

                <button
                  onClick={() => handleNavigate('tasks')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'tasks' || currentTab === 'workflow_progress' || currentTab === 'artifacts_result'
                      ? 'text-red-600 font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <CheckSquare className={`w-5 h-5 ${currentTab === 'tasks' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Tasks</span>
                </button>

                <button
                  onClick={() => handleNavigate('files')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'files'
                      ? 'text-red-600 font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <FolderClosed className={`w-5 h-5 ${currentTab === 'files' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Files</span>
                </button>

                <button
                  onClick={() => handleNavigate('profile')}
                  className={`flex flex-col items-center justify-center py-1 rounded-xl transition ${
                    currentTab === 'profile'
                      ? 'text-red-600 font-bold'
                      : 'text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  <User className={`w-5 h-5 ${currentTab === 'profile' ? 'stroke-[2.5]' : ''}`} />
                  <span className="text-[10px] mt-1 font-semibold">Profile</span>
                </button>
              </div>
            )}
          </div>
        </nav>
      )}
      </>
      )}

      {/* Interactive Screen Gallery Modal (Sheet 1-6 Master Directory) */}
      <ScreenGalleryModal
        isOpen={showScreenGallery}
        onClose={() => setShowScreenGallery(false)}
        onSelectScreen={handleNavigate}
        currentScreen={currentTab}
      />

      {/* Drawer: Full Domain & Page Explorer with Customer vs Partner Tab */}
      {showDrawerMenu && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-sm bg-white dark:bg-slate-900 h-full p-5 shadow-2xl flex flex-col justify-between overflow-y-auto">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <MoreAiNetworkLockup size="sm" dark={isDarkMode} />
                <button
                  onClick={() => setShowDrawerMenu(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Role Switcher */}
              <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700">
                <button
                  onClick={() => setDrawerRole('customer')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    drawerRole === 'customer'
                      ? 'bg-red-600 text-white shadow-2xs'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
                  }`}
                >
                  <User className="w-3.5 h-3.5" />
                  <span>UI Customer</span>
                </button>

                <button
                  onClick={() => setDrawerRole('partner')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    drawerRole === 'partner'
                      ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-2xs'
                      : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
                  }`}
                >
                  <Building2 className="w-3.5 h-3.5 text-amber-500" />
                  <span>UI Mitra Partner</span>
                </button>
              </div>

              {/* Button to open Screen Gallery */}
              <button
                onClick={() => {
                  setShowDrawerMenu(false);
                  setShowScreenGallery(true);
                }}
                className="w-full py-2 px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-200 text-xs font-bold flex items-center justify-center gap-2 border border-slate-200 dark:border-slate-700 transition"
              >
                <Grid className="w-4 h-4 text-red-600" />
                <span>Buka Galeri Sheet 1 - 6</span>
              </button>

              {/* Drawer Content: Customer Pages */}
              {drawerRole === 'customer' && (
                <div className="space-y-3">
                  <div>
                    <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block mb-1">
                      Workspace &amp; Fitur AI
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('home')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Beranda (Dashboard)</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 &amp; 2</span>
                      </button>
                      <button onClick={() => handleNavigate('chat')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Chat AI Assistant</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 &amp; 2</span>
                      </button>
                      <button onClick={() => handleNavigate('agents')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>AI Agent Studio (Spesialis)</span>
                        <span className="text-[10px] text-slate-400">Sheet 6 #6</span>
                      </button>
                      <button onClick={() => handleNavigate('create')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Buat Konten &amp; Media</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 &amp; 2</span>
                      </button>
                      <button onClick={() => handleNavigate('analyse')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Analisis File &amp; Data</span>
                        <span className="text-[10px] text-slate-400">Sheet 2</span>
                      </button>
                      <button onClick={() => handleNavigate('code')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Code Playground Runner</span>
                        <span className="text-[10px] text-slate-400">Sheet 2</span>
                      </button>
                      <button onClick={() => handleNavigate('tasks')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Daftar Tugas &amp; Proyek</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 &amp; 2</span>
                      </button>
                      <button onClick={() => handleNavigate('files')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Files &amp; Library</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 &amp; 2</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block mb-1">
                      Koneksi Wi-Fi Partner ISP &amp; Utilitas
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('wifi')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Wi-Fi Management 100 Mbps</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #3</span>
                      </button>
                      <button onClick={() => handleNavigate('speedtest')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Speedtest &amp; Diagnostik Optik</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #5</span>
                      </button>
                      <button onClick={() => handleNavigate('device_access_control')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Kontrol Akses Perangkat &amp; QoS</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #8</span>
                      </button>
                      <button onClick={() => handleNavigate('devices_connected')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Daftar Perangkat Terhubung (5)</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #4</span>
                      </button>
                      <button onClick={() => handleNavigate('wifi_session')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Sesi Wi-Fi &amp; Kuota Real-Time</span>
                        <span className="text-[10px] text-slate-400">Sheet 3 #10</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-red-600 uppercase tracking-wider block mb-1">
                      Benefit, Poin &amp; Akun
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('benefits')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>AI Credit Center (100K Poin)</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #7</span>
                      </button>
                      <button onClick={() => handleNavigate('token_ledger')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Buku Besar Token &amp; Hash Audit</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #13</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_vouchers')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Dompet Kupon Kafe Mitra</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #12</span>
                      </button>
                      <button onClick={() => handleNavigate('security_settings')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Pusat Keamanan &amp; 2FA</span>
                        <span className="text-[10px] text-slate-400">Sheet 5 #14</span>
                      </button>
                      <button onClick={() => handleNavigate('profile')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Pengaturan Akun &amp; Profil</span>
                        <span className="text-[10px] text-slate-400">Sheet 1 #7</span>
                      </button>
                      <button onClick={() => handleNavigate('captive')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Captive Portal Tamu</span>
                        <span className="text-[10px] text-slate-400">Sheet 3 Flow</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Drawer Content: Mitra Partner Pages */}
              {drawerRole === 'partner' && (
                <div className="space-y-3">
                  <div>
                    <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider block mb-1">
                      Operasional Venue Kafe &amp; Resto
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('partner')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Dashboard Utama Mitra</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #2</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_live_sessions')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Live Monitor Pengunjung Tamu</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #4</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_locations')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Manajemen Lokasi Cabang Venue</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #3</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_staff')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Manajemen Staf &amp; Kasir</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #6</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider block mb-1">
                      Jaringan Hotspot &amp; Akses Tamu
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('partner_gateway_config')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Konfigurasi Gateway Router</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #5</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_qr')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>QR Generator Meja Kafe</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #7</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_packages')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Paket Kuota &amp; Durasi Tamu</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #8</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_promo')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Program Insentif &amp; Poin Mitra</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #11</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider block mb-1">
                      Finansial &amp; Integrasi B2B
                    </span>
                    <div className="space-y-0.5 text-xs">
                      <button onClick={() => handleNavigate('partner_analytics')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Analitik Jam Sibuk &amp; Tamu</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #9</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_api_settings')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>API Keys &amp; Webhook Events</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #13</span>
                      </button>
                      <button onClick={() => handleNavigate('partner_login')} className="w-full p-2 rounded-xl text-left hover:bg-slate-100 dark:hover:bg-slate-800 flex justify-between">
                        <span>Portal Login / Registrasi Mitra</span>
                        <span className="text-[10px] text-slate-400">Sheet 4 #1</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-center">
              <span className="text-[10px] text-slate-400 block">
                MoreAI &bull; Global Partner ISP &amp; Network
              </span>
              <span className="text-[9px] text-slate-400">PWA v1.0.0 · Mobile First Responsive</span>
            </div>
          </div>
        </div>
      )}

      {/* Onboarding & Splash Modal */}
      <OnboardingModal
        isOpen={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onStart={() => {
          setShowOnboarding(false);
          handleNavigate('home');
        }}
      />
    </div>
  );
}
