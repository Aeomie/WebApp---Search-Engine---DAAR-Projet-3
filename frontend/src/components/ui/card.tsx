import React from 'react'
export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => (
  <div {...rest} className={['card', className].filter(Boolean).join(' ')} />
)
export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => (
  <div {...rest} className={['card-header', className].filter(Boolean).join(' ')} />
)
export const CardTitle: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => (
  <div {...rest} className={['card-title', className].filter(Boolean).join(' ')} />
)
export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => (
  <div {...rest} className={['card-content', className].filter(Boolean).join(' ')} />
)
