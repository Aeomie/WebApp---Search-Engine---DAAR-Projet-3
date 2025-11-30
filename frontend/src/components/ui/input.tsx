import React from 'react'
export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = ({ className, ...rest }) => (
  <input {...rest} className={['input', className].filter(Boolean).join(' ')} />
)
export default Input
