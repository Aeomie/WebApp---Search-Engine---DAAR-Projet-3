import React, { createContext, useContext } from 'react'
type Ctx = { value: string; onValueChange: (v: string)=>void; options: {value:string; label:string}[] }
const SelectCtx = createContext<Ctx | null>(null)

type SelectProps = { value: string; onValueChange: (v: string)=>void; children: React.ReactNode }
export const Select: React.FC<SelectProps> = ({ value, onValueChange, children }) => {
  const options: {value:string; label:string}[] = []
  React.Children.forEach(children as any, (child: any) => {
    if (child?.type?.displayName === 'SelectContent') {
      React.Children.forEach(child.props.children, (it: any) => {
        if (it?.type?.displayName === 'SelectItem') {
          options.push({ value: it.props.value, label: it.props.children })
        }
      })
    }
  })
  return <SelectCtx.Provider value={{ value, onValueChange, options }}>{children}</SelectCtx.Provider>
}

export const SelectTrigger: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...rest }) => {
  const ctx = useContext(SelectCtx)!
  return (
    <div {...rest} className={className}>
      <select className="select" value={ctx.value} onChange={(e)=>ctx.onValueChange(e.target.value)}>
        {ctx.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}

export const SelectContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => <div {...props} />
SelectContent.displayName = 'SelectContent'

export const SelectItem: React.FC<{ value: string; children: any }> = () => null
SelectItem.displayName = 'SelectItem'

export const SelectValue: React.FC<{ placeholder?: string }> = () => null
