import React from 'react';

interface CardProps {
  title?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  padded?: boolean;
}

export function Card({ title, actions, children, className = '', padded = true }: CardProps) {
  return (
    <section className={`glass border border-[var(--color-border)] rounded-[var(--radius-lg)] shadow-md card-hover ${className}`}>      
      {(title || actions) && (
        <header className="flex items-center justify-between px-5 pt-5 pb-3">
          {title && <h3 className="text-sm tracking-wide uppercase font-semibold text-[var(--color-text-dim)]">{title}</h3>}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={padded ? 'px-5 pb-5' : ''}>{children}</div>
    </section>
  );
}

export function CardSection({ children }: { children: React.ReactNode }) {
  return <div className="mt-4 first:mt-0">{children}</div>;
}