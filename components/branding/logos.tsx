'use client';

import React from 'react';
import { Globe, Wifi } from 'lucide-react';

export const MoreAiIcon: React.FC<{ className?: string; size?: number }> = ({
  className = 'w-8 h-8',
  size,
}) => {
  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 ${className}`}
      style={size ? { width: size, height: size } : undefined}
    >
      <img
        src="/moreai-icon-transparent.png"
        alt="MoreAI Icon"
        className="w-full h-full object-contain select-none"
        loading="eager"
      />
    </div>
  );
};

export const MoreAiLogo: React.FC<{
  className?: string;
  showSubtitle?: boolean;
  subtitle?: string;
  dark?: boolean;
  size?: 'sm' | 'md' | 'lg';
}> = ({
  className = '',
  showSubtitle = false,
  subtitle = 'AI Workspace Platform',
  dark = false,
  size = 'md',
}) => {
  const heightClasses =
    size === 'sm' ? 'h-6 sm:h-7' : size === 'lg' ? 'h-10 sm:h-12' : 'h-7 sm:h-9';

  return (
    <div className={`flex flex-col items-start ${className}`}>
      <img
        src={dark ? '/moreai-logo-dark.png' : '/moreai-logo-transparent.png'}
        alt="MoreAI"
        className={`${heightClasses} w-auto object-contain select-none`}
        loading="eager"
      />
      {showSubtitle && (
        <span
          className={`text-[10px] font-medium tracking-wide mt-0.5 leading-none pl-1 ${
            dark ? 'text-slate-400' : 'text-slate-500'
          }`}
        >
          {subtitle}
        </span>
      )}
    </div>
  );
};

export const GlobalPartnerLogo: React.FC<{
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  dark?: boolean;
  showBadge?: boolean;
}> = ({ className = '', size = 'md', dark = false, showBadge = true }) => {
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4';
  const titleClass =
    size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm sm:text-[15px]';

  return (
    <div className={`flex items-center gap-2 select-none ${className}`}>
      <div
        className={`w-7 h-7 sm:w-8 sm:h-8 rounded-lg flex items-center justify-center shrink-0 border ${
          dark
            ? 'bg-blue-500/10 border-blue-400/30 text-blue-400'
            : 'bg-blue-50 border-blue-200 text-blue-600'
        }`}
      >
        <Globe className={iconSize} />
      </div>
      <div className="flex flex-col leading-tight">
        <div className={`font-bold tracking-tight ${titleClass} ${dark ? 'text-white' : 'text-slate-900'}`}>
          Global Partner
        </div>
        {showBadge && (
          <div className="flex items-center gap-1 mt-0.5">
            <span className="text-[9px] sm:text-[10px] font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
              ISP &bull; Network
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
          </div>
        )}
      </div>
    </div>
  );
};

export const MoreAiNetworkLockup: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  dark?: boolean;
}> = ({ size = 'md', dark = false }) => {
  const heightClasses =
    size === 'sm' ? 'h-6 sm:h-7' : size === 'lg' ? 'h-9 sm:h-11' : 'h-7 sm:h-8.5';

  return (
    <div className="flex items-center gap-2 sm:gap-2.5 shrink-0 select-none">
      <img
        src={dark ? '/moreai-logo-dark.png' : '/moreai-logo-transparent.png'}
        alt="MoreAI"
        className={`${heightClasses} w-auto object-contain`}
        loading="eager"
      />
      <div className="h-5 sm:h-6 w-px bg-slate-200 dark:bg-slate-700 shrink-0" />
      <div
        className={`flex items-center gap-1.5 px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full border text-[11px] sm:text-xs font-semibold shrink-0 transition-colors ${
          dark
            ? 'bg-slate-900/80 border-slate-700 text-slate-200'
            : 'bg-slate-100/90 border-slate-200/80 text-slate-700'
        }`}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0 animate-pulse" />
        <span className="whitespace-nowrap">
          Global Partner <span className="text-blue-600 dark:text-blue-400 font-bold">ISP / Network</span>
        </span>
      </div>
    </div>
  );
};
