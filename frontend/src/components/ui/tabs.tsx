import React, { createContext, useContext, useState } from 'react'
type Ctx = { value: string; setValue: (v: string)=>void }
const TabsCtx = createContext<Ctx | null>(null)
export const Tabs: React.FC<{defaultValue: string; className?: string}> = ({ defaultValue, className, children }) => {
  const [value, setValue] = useState(defaultValue)
  return <div className={className}><TabsCtx.Provider value={{value, setValue}}>{children}</TabsCtx.Provider></div>
}
export const TabsList: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <div {...props} />
export const TabsTrigger: React.FC<{value: string; children: React.ReactNode}> = ({ value, children }) => {
  const ctx = useContext(TabsCtx)!
  return <button className="btn secondary" onClick={()=>ctx.setValue(value)} style={{marginRight:8}}>{children}</button>
}
export const TabsContent: React.FC<{value: string; className?: string}> = ({ value, className, children }) => {
  const ctx = useContext(TabsCtx)!
  if (ctx.value !== value) return null
  return <div className={className}>{children}</div>
}
