import React from 'react';
interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
}
export function Alert({ children, className = '' }: AlertProps) {
    return (
        <div className={`p-4 rounded-lg border border-yellow-200 bg-yellow-50 ${className}`}>
            {children}
        </div>
    );
}
export function AlertDescription({ children, className = '' }: AlertProps) {
    return <div className={`text-sm text-yellow-800 ${className}`}>{children}</div>;
}
