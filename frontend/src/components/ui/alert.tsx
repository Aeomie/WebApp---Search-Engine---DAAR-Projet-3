import React from 'react'
export const Alert: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => (
  <div {...rest} className={className} />
)
export const AlertTitle: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <div {...props} />
export const AlertDescription: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <div {...props} />
export default Alert
