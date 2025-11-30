import React from 'react'
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'secondary' | 'primary' }
export const Button: React.FC<Props> = ({ variant, className, ...rest }) => (
  <button {...rest} className={['btn', variant==='secondary' ? 'secondary' : '', className].filter(Boolean).join(' ')} />
)
export default Button
