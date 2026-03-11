import React from 'react';
interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    children: React.ReactNode;
    variant?: 'default' | 'destructive' | 'success';
    className?: string;
}
export function Badge({ children, variant = 'default', className = '', ...props }: BadgeProps) {
    const variants = {
        default: "bg-blue-100 text-blue-800",
        destructive: "bg-red-100 text-red-800",
        success: "bg-green-100 text-green-800",
    };
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variants[variant]} ${className}`} {...props}>
            {children}
        </span>
    );
}
