import useScrollReveal from '../../hooks/useScrollReveal'

export default function Section({ children, className = '', id }) {
  const [ref, visible] = useScrollReveal()
  return (
    <section ref={ref} id={id} className={`transition-all duration-700 ${
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
    } ${className}`}>
      {children}
    </section>
  )
}
