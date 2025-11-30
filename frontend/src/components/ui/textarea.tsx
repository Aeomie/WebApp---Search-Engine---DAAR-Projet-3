import React from 'react'
export const Textarea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = ({ className, ...rest }) => (
  <textarea {...rest} className={['textarea', className].filter(Boolean).join(' ')} />
)
export default Textarea
