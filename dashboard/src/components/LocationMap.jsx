import { useEffect, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix leaflet default marker icon
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})
L.Marker.prototype.options.icon = defaultIcon

export default function LocationMap({ findings }) {
  const geoFindings = findings.filter(f =>
    f.category === 'geolocation' && f.data?.latitude && f.data?.longitude
  )

  if (geoFindings.length === 0) {
    return (
      <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl p-8 text-center">
        <p className="text-gray-500 text-sm">No geolocation data available. Run the GeoIP module to map server locations.</p>
      </div>
    )
  }

  // Center on first point or average
  const avgLat = geoFindings.reduce((s, f) => s + f.data.latitude, 0) / geoFindings.length
  const avgLon = geoFindings.reduce((s, f) => s + f.data.longitude, 0) / geoFindings.length

  return (
    <div className="bg-[#12121a] border border-[#1e1e2e] rounded-xl overflow-hidden">
      <div className="h-[400px]">
        <MapContainer
          center={[avgLat, avgLon]}
          zoom={3}
          className="h-full w-full"
          style={{ background: '#0a0a0f' }}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
          {geoFindings.map((f, i) => (
            <Marker key={i} position={[f.data.latitude, f.data.longitude]}>
              <Popup>
                <div className="text-xs">
                  <strong>{f.data.city}, {f.data.country}</strong>
                  <br />IP: {f.data.ip}
                  {f.data.isp && <><br />ISP: {f.data.isp}</>}
                  {f.data.org && <><br />Org: {f.data.org}</>}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      {/* Legend */}
      <div className="px-4 py-3 border-t border-[#1e1e2e]">
        <div className="flex flex-wrap gap-4 text-xs text-gray-400">
          {geoFindings.map((f, i) => (
            <span key={i} className="inline-flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#3388ff]" />
              {f.data.city}, {f.data.country} ({f.data.ip})
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
