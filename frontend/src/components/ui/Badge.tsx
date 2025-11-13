import React from 'react';

interface BadgeProps {
  tone?: 'critical' | 'high' | 'medium' | 'low' | 'pending' | 'action';
  children: React.ReactNode;
  className?: string;
}

export function Badge({ tone = 'pending', children, className = '' }: BadgeProps) {
  return (
    <span className={`badge badge-${tone} ${className}`}>{children}</span>
  );
}