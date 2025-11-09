/** Card component for displaying metrics */
import React from 'react'

interface CardProps {
  title: string
  value: string | number
  subtitle?: string
  className?: string
}

export default function Card({ title, value, subtitle, className = '' }: CardProps) {
  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 border border-gray-200 ${className}`}
    >
      <h3 className="text-sm font-medium text-gray-500 mb-2">{title}</h3>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {subtitle && <p className="text-sm text-gray-500 mt-2">{subtitle}</p>}
    </div>
  )
}

