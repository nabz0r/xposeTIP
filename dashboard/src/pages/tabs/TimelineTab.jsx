import React from 'react'
import LifeTimeline from '../../components/LifeTimeline'
import IOCTimeline from '../../components/IOCTimeline'

export default function TimelineTab({ profile, findings }) {
  return (
    <div className="space-y-6">
      {profile?.life_timeline?.length > 0 && (
        <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">Life Timeline</h3>
          <LifeTimeline events={profile.life_timeline} />
        </div>
      )}
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-5">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-4">IOC Timeline</h3>
        <IOCTimeline findings={findings} />
      </div>
    </div>
  )
}
