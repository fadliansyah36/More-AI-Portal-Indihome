'use client';

import React from 'react';

export const MoreAiIcon: React.FC<{ className?: string; size?: number }> = ({
  className = 'w-8 h-8',
  size,
}) => {
  return (
    <svg
      viewBox="0 0 100 85"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={size ? { width: size, height: size } : undefined}
    >
      <defs>
        <linearGradient id="mRibbon1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FF334B" />
          <stop offset="100%" stopColor="#D90429" />
        </linearGradient>
        <linearGradient id="mRibbon2" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#EA0029" />
          <stop offset="100%" stopColor="#BA0020" />
        </linearGradient>
      </defs>
      {/* Left loop of the 'M' ribbon */}
      <path
        d="M26 12 C14 26, 4 48, 14 66 C22 78, 38 78, 48 64 C56 52, 54 36, 44 26 L30 14 Z"
        fill="url(#mRibbon1)"
      />
      {/* Right loop of the 'M' ribbon */}
      <path
        d="M58 12 C46 26, 38 48, 48 66 C56 78, 72 78, 82 64 C90 52, 88 36, 78 26 L64 14 Z"
        fill="url(#mRibbon2)"
      />
      {/* Connecting sleek slant overlay */}
      <path
        d="M18 52 C28 32, 44 18, 54 18 C60 18, 50 44, 40 60 C32 72, 22 68, 18 52 Z"
        fill="#FF2A42"
        opacity="0.9"
      />
    </svg>
  );
};

export const MoreAiLogo: React.FC<{
  className?: string;
  showSubtitle?: boolean;
  subtitle?: string;
  dark?: boolean;
}> = ({
  className = '',
  showSubtitle = false,
  subtitle = 'AI Workspace Platform',
  dark = false,
}) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <MoreAiIcon className="w-8 h-8 shrink-0" />
      <div className="flex flex-col">
        <span
          className={`text-xl font-extrabold tracking-tight leading-none ${
            dark ? 'text-white' : 'text-slate-900'
          }`}
        >
          More<span className="text-red-600">AI</span>
        </span>
        {showSubtitle && (
          <span className="text-[10px] font-medium text-slate-500 tracking-wide mt-0.5 leading-none">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};

export const IndiHomeLogo: React.FC<{
  className?: string;
  showTelkom?: boolean;
}> = ({ className = '', showTelkom = true }) => {
  return (
    <div className={`flex flex-col items-start ${className}`}>
      <div className="flex items-center gap-1 font-black text-lg tracking-tight leading-none text-red-600">
        <span>Indi</span>
        <span className="text-red-600 font-extrabold">Home</span>
      </div>
      {showTelkom && (
        <div className="flex items-center gap-1 mt-0.5">
          <span className="text-[8px] text-slate-500 font-medium">by Telkom Indonesia</span>
          <svg className="w-2.5 h-2.5 text-red-600" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="5" fill="white" />
          </svg>
        </div>
      )}
    </div>
  );
};

export const MoreAiIndiHomeLockup: React.FC<{
  size?: 'sm' | 'md' | 'lg';
  dark?: boolean;
}> = ({ size = 'md', dark = false }) => {
  const iconSize = size === 'sm' ? 24 : size === 'lg' ? 36 : 28;
  const textSize = size === 'sm' ? 'text-base' : size === 'lg' ? 'text-2xl' : 'text-lg';

  return (
    <div className="flex items-center gap-2.5 sm:gap-3.5 shrink-0">
      <div className="flex items-center gap-1.5">
        <MoreAiIcon size={iconSize} />
        <span className={`font-black ${textSize} tracking-tight ${dark ? 'text-white' : 'text-slate-900'}`}>
          More<span className="text-red-600">AI</span>
        </span>
      </div>
      <span className="text-slate-300 dark:text-slate-700 font-light text-base select-none">|</span>
      <IndiHomeLogo showTelkom={size !== 'sm'} />
    </div>
  );
};
