import React from 'react'
export const Separator: React.FC<{orientation?: 'vertical' | 'horizontal'; className?: string}> = ({ orientation='horizontal', className }) => (
  orientation === 'vertical'
    ? <div className={className} style={{ width:1, background:'rgba(255,255,255,.1)'}}/>
    : <hr className={['sep', className].filter(Boolean).join(' ')} />
)
export default Separator
