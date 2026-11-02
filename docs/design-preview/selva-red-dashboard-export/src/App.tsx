import { useState, type ReactNode } from "react"

type IconName = "overview" | "nodes" | "sensors" | "radio" | "mqtt" | "terminal" | "firmware" | "logs" | "accounts" | "settings" | "search" | "bell" | "plus" | "refresh" | "arrow" | "more" | "signal" | "temperature" | "humidity" | "battery"

const iconPaths: Record<IconName, ReactNode> = {
  overview: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="3" width="7" height="7" rx="2" />
      <rect x="3" y="14" width="7" height="7" rx="2" />
      <rect x="14" y="14" width="7" height="7" rx="2" />
    </>
  ),
  nodes: (
    <>
      <circle cx="12" cy="5" r="2.5" />
      <circle cx="5" cy="18" r="2.5" />
      <circle cx="19" cy="18" r="2.5" />
      <path d="m10.8 7.2-4.6 8.6m3.3 2.2h5m-1.3-10.8 4.6 8.6" />
    </>
  ),
  sensors: (
    <>
      <path d="M12 4v16M8 7.5a6 6 0 0 0 0 9m8-9a6 6 0 0 1 0 9" />
      <circle cx="12" cy="12" r="2" />
    </>
  ),
  radio: (
    <>
      <circle cx="12" cy="12" r="2" />
      <path d="M8.5 8.5a5 5 0 0 0 0 7m7-7a5 5 0 0 1 0 7M5 5a10 10 0 0 0 0 14M19 5a10 10 0 0 1 0 14" />
    </>
  ),
  mqtt: (
    <>
      <path d="M4 17V7m0 0 4 4m-4-4L0 11M20 7v10m0 0 4-4m-4 4-4-4" />
      <path d="M9 5h6v14H9z" />
    </>
  ),
  terminal: (
    <>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="m7 9 3 3-3 3m6 0h4" />
    </>
  ),
  firmware: (
    <>
      <rect x="7" y="7" width="10" height="10" rx="1" />
      <path d="M9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3" />
    </>
  ),
  logs: (
    <>
      <path d="M6 3h9l4 4v14H6z" />
      <path d="M14 3v5h5M9 12h6m-6 4h6" />
    </>
  ),
  accounts: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M3 20a6 6 0 0 1 12 0m1-15a3.5 3.5 0 0 1 0 6m2 3a5.5 5.5 0 0 1 3 5" />
    </>
  ),
  settings: (
    <>
      <path d="M4 6h16M4 12h16M4 18h16" />
      <circle cx="9" cy="6" r="2" fill="currentColor" stroke="none" />
      <circle cx="15" cy="12" r="2" fill="currentColor" stroke="none" />
      <circle cx="8" cy="18" r="2" fill="currentColor" stroke="none" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  bell: (
    <>
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  refresh: (
    <>
      <path d="M20 7v5h-5" />
      <path d="M18.2 17a8 8 0 1 1 1.5-8.5L20 12" />
    </>
  ),
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  more: (
    <>
      <circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" />
    </>
  ),
  signal: <path d="M5 18v-2m4 2v-5m4 5v-8m4 8V7m4 11V4" />,
  temperature: (
    <>
      <path d="M10 14.8V5a2 2 0 0 1 4 0v9.8a4 4 0 1 1-4 0Z" />
      <path d="M12 9v7" />
    </>
  ),
  humidity: <path d="M12 2S5 10 5 15a7 7 0 0 0 14 0c0-5-7-13-7-13Z" />,
  battery: (
    <>
      <rect x="3" y="7" width="17" height="10" rx="2" />
      <path d="M22 10v4M6 10v4m3-4v4m3-4v4" />
    </>
  ),
}

function Icon({ name, size = 19 }: { name: IconName; size?: number }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {iconPaths[name]}
    </svg>
  )
}

const navGroups: { label: string; items: { label: string; icon: IconName }[] }[] =
  [
    {
      label: "Workspace",
      items: [
        { label: "Overview", icon: "overview" },
        { label: "Nodes", icon: "nodes" },
        { label: "Sensors", icon: "sensors" },
        { label: "Communication", icon: "radio" },
      ],
    },
    {
      label: "Manage",
      items: [
        { label: "MQTT", icon: "mqtt" },
        { label: "Command center", icon: "terminal" },
        { label: "Firmware", icon: "firmware" },
        { label: "Logs", icon: "logs" },
        { label: "Accounts", icon: "accounts" },
      ],
    },
  ]

const rangeData = {
  "1H": {
    packets: "5,284",
    rate: "98.8%",
    peak: "182",
    label: "Last 60 minutes",
  },
  "6H": {
    packets: "31,840",
    rate: "98.6%",
    peak: "194",
    label: "Last 6 hours",
  },
  "24H": {
    packets: "128,492",
    rate: "99.1%",
    peak: "208",
    label: "Last 24 hours",
  },
  "7D": {
    packets: "886,204",
    rate: "98.9%",
    peak: "224",
    label: "Last 7 days",
  },
}

const sensors: {
  name: string
  node: string
  value: string
  unit: string
  icon: IconName
  status: string
  points: string
}[] = [
  {
    name: "Temperature",
    node: "NODE-A07",
    value: "24.8",
    unit: "°C",
    icon: "temperature",
    status: "Nominal",
    points: "2,24 12,21 22,22 32,15 42,18 52,9 62,12 72,5",
  },
  {
    name: "Relative humidity",
    node: "NODE-A07",
    value: "58.2",
    unit: "%",
    icon: "humidity",
    status: "Nominal",
    points: "2,18 12,20 22,14 32,17 42,11 52,14 62,8 72,10",
  },
  {
    name: "Signal strength",
    node: "NODE-B12",
    value: "−67",
    unit: "dBm",
    icon: "signal",
    status: "Strong",
    points: "2,22 12,20 22,23 32,16 42,14 52,8 62,11 72,6",
  },
  {
    name: "Battery level",
    node: "NODE-C04",
    value: "84",
    unit: "%",
    icon: "battery",
    status: "Healthy",
    points: "2,6 12,7 22,9 32,10 42,12 52,14 62,15 72,17",
  },
]

const events = [
  {
    tone: "warning",
    title: "Signal variance detected",
    detail: "NODE-B12 · RSSI dropped below −82 dBm",
    time: "12 min",
  },
  {
    tone: "success",
    title: "Node reconnected",
    detail: "NODE-C04 · Session restored",
    time: "38 min",
  },
  {
    tone: "info",
    title: "Firmware check complete",
    detail: "20 nodes verified · v2.8.4",
    time: "1 hr",
  },
]

export default function App() {
  const [activeNav, setActiveNav] = useState("Overview")
  const [range, setRange] = useState<keyof typeof rangeData>("1H")
  const [notice, setNotice] = useState("")
  const current = rangeData[range]

  const announce = (message: string) => {
    setNotice(message)
    window.setTimeout(() => setNotice(""), 2400)
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
          <button
            className="user-card"
            onClick={() => announce("Account menu opened")}
          >
            <span className="avatar">SR</span>
            <span>
              <strong>Selvarithik</strong>
              <small>Administrator</small>
            </span>
            <Icon name="more" size={17} />
          </button>

        <nav className="main-nav" aria-label="Primary navigation">
          {navGroups.map((group) => (
            <div className="nav-group" key={group.label}>
              <p className="nav-label">{group.label}</p>
              {group.items.map((item) => (
                <button
                  key={item.label}
                  className={`nav-item ${
                    activeNav === item.label ? "active" : ""
                  }`}
                  onClick={() => {
                    setActiveNav(item.label)
                    announce(`${item.label} selected`)
                  }}
                >
                  <Icon name={item.icon} />
                  <span>{item.label}</span>
                  {item.label === "Logs" && (
                    <span className="nav-badge">3</span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button
            className="nav-item"
            onClick={() => announce("Settings opened")}
          >
            <Icon name="settings" />
            <span>Settings</span>
          </button>

        </div>
      </aside>

      <main className="dashboard">
        <header className="topbar">
          <div className="header-identity"><strong className="header-name">SELVARITHIK <span>A&amp;D</span></strong><span className="topbar-page"><Icon name="overview" size={20} /> System Overview</span></div>
          <label className="search">
            <Icon name="search" size={18} />
            <input
              aria-label="Search nodes and sensors"
              placeholder="Search nodes, sensors, commands..."
              onKeyDown={(event) => {
                if (event.key === "Enter" && event.currentTarget.value)
                  announce(`Searching for “${event.currentTarget.value}”`)
              }}
            />
            <kbd>⌘ K</kbd>
          </label>
          <div className="top-actions">
            <div className="connection">
              <Icon name="radio" size={17} /> <span>Gateway online</span>
            </div>
            <button
              className="icon-button"
              aria-label="Notifications"
              onClick={() => announce("1 active system problem")}
            >
              <Icon name="bell" size={21} />
              <span className="notification-dot" />
            </button>
            <button
              className="primary-button"
              onClick={() => announce("Widget library opened")}
            >
              <Icon name="plus" size={19} /> Add widget
            </button>
          </div>
        </header>

        <div className="content">
          <section className="welcome-row">
            <div>
              <p className="eyebrow">Gateway operations / Live</p>
              <h1>System overview</h1>
              <p className="subhead">
                Real-time health and telemetry across your LoRa network.
              </p>
            </div>
            <div className="welcome-actions">
              <span className="updated">
                <i /> Updated 8 sec ago
              </span>
              <button
                className="refresh-button"
                onClick={() => announce("Telemetry refreshed")}
              >
                <Icon name="refresh" size={15} /> Refresh
              </button>
              <div className="range-control" aria-label="Telemetry period">
                {(Object.keys(rangeData) as (keyof typeof rangeData)[]).map(
                  (item) => (
                    <button
                      key={item}
                      className={range === item ? "selected" : ""}
                      onClick={() => setRange(item)}
                    >
                      {item}
                    </button>
                  ),
                )}
              </div>
            </div>
          </section>

          <section className="gateway-banner" aria-label="Gateway information">
            <img
              src="/assets/sr-white-transparent.svg"
              alt="SELVARITHIK SR logo"
            />
            <div className="gateway-banner-copy">
              <p>SELVARITHIK A&amp;D</p>
              <h2>LoRa Gateway</h2>
              <span>PROFESSIONAL GATEWAY MONITORING DASHBOARD</span>
            </div>
            <div className="gateway-banner-status">
              <span>
                <i /> Operational
              </span>
              <dl>
                <div>
                  <dt>Gateway</dt>
                  <dd>ESP32-MASTER</dd>
                </div>
                <div>
                  <dt>Frequency</dt>
                  <dd>915 MHz</dd>
                </div>
                <div>
                  <dt>Uptime</dt>
                  <dd>42d 18h</dd>
                </div>
              </dl>
            </div>
          </section>

          <section className="stats-grid" aria-label="Gateway metrics">
            <article className="stat-card featured">
              <div className="stat-top">
                <span className="stat-icon">
                  <Icon name="nodes" size={18} />
                </span>
                <span className="trend light">↗ 2 online</span>
              </div>
              <p>Nodes online</p>
              <h2>
                18 <small>/ 20</small>
              </h2>
              <span className="stat-note">90% fleet availability</span>
              <div className="node-dots" aria-hidden="true">
                {Array.from({ length: 10 }).map((_, index) => (
                  <i className={index === 9 ? "offline" : ""} key={index} />
                ))}
              </div>
            </article>
            <article className="stat-card sensors-stat">
              <div className="stat-top">
                <span className="stat-icon">
                  <Icon name="sensors" size={18} />
                </span>
                <span className="trend">↗ 4.2%</span>
              </div>
              <p>Active sensors</p>
              <h2>64</h2>
              <span className="stat-note">Across 18 connected nodes</span>
            </article>
            <article className="stat-card packets-stat">
              <div className="stat-top">
                <span className="stat-icon">
                  <Icon name="radio" size={18} />
                </span>
                <span className="trend">Stable</span>
              </div>
              <p>Packet success</p>
              <h2>{current.rate}</h2>
              <span className="stat-note">
                {current.packets} packets received
              </span>
            </article>
            <article className="stat-card problem-card">
              <div className="stat-top">
                <span className="stat-icon amber">
                  <Icon name="bell" size={18} />
                </span>
                <span className="trend warning">Review</span>
              </div>
              <p>Active problems</p>
              <h2>1</h2>
              <span className="stat-note">Signal variance on NODE-B12</span>
            </article>
          </section>

          <section className="dashboard-grid">
            <article className="panel problems-panel">
              <div className="panel-header">
                <div>
                  <p className="section-kicker">Attention</p>
                  <h2>System events</h2>
                </div>
                <button className="icon-button flat" aria-label="Event options">
                  <Icon name="more" size={17} />
                </button>
              </div>
              <div className="event-list">
                {events.map((event) => (
                  <button
                    key={event.title}
                    onClick={() => announce(event.title)}
                  >
                    <i className={event.tone} />
                    <span>
                      <strong>{event.title}</strong>
                      <small>{event.detail}</small>
                    </span>
                    <time>{event.time}</time>
                  </button>
                ))}
              </div>
              <button
                className="panel-link"
                onClick={() => announce("Event log opened")}
              >
                View event log <Icon name="arrow" size={14} />
              </button>
            </article>
          </section>

          <section className="sensor-section">
            <div className="section-heading">
              <div>
                <p className="section-kicker">All nodes</p>
                <h2>Live sensor readings</h2>
              </div>
              <button
                className="filter-button"
                onClick={() => announce("Sensor filters opened")}
              >
                All sensors <span>⌄</span>
              </button>
            </div>
            <article className="node-panel">
              <header className="node-panel-head">
                <div className="node-title">
                  <i />
                  <span>
                    <strong>Workshop Environmental Node</strong>
                    <small>NODE-A07 · ESP32-S3</small>
                  </span>
                </div>
                <div className="node-meta">
                  <span>
                    <small>Communication</small>
                    <b>LoRa · 915 MHz</b>
                  </span>
                  <span>
                    <small>Firmware</small>
                    <b>v2.8.4</b>
                  </span>
                  <span className="node-online">
                    <small>State</small>
                    <b>Online</b>
                  </span>
                  <button
                    className="icon-button flat"
                    aria-label="Node options"
                  >
                    <Icon name="more" size={17} />
                  </button>
                </div>
              </header>
              <div className="sensor-grid">
                {sensors.map((sensor, index) => (
                  <article className={`sensor-card sensor-${sensor.icon}`} key={sensor.name}>
                    <div className="sensor-head">
                      <span className="sensor-icon">
                        <Icon name={sensor.icon} size={18} />
                      </span>
                      <span>
                        <strong>{sensor.name}</strong>
                        <small>
                          {sensor.node} · PARAM-
                          {String(index + 1).padStart(2, "0")}
                        </small>
                      </span>
                      <span className="sensor-type">SENSOR</span>
                    </div>
                    <div className="sensor-value">
                      <strong>{sensor.value}</strong>
                      <span>{sensor.unit}</span>
                    </div>
                    <div className="sensor-chart">
                      <svg
                        viewBox="0 0 240 58"
                        preserveAspectRatio="none"
                        role="img"
                        aria-label={`${sensor.name} recent readings`}
                      >
                        <line x1="0" y1="10" x2="240" y2="10" />
                        <line x1="0" y1="29" x2="240" y2="29" />
                        <line x1="0" y1="48" x2="240" y2="48" />
                        <polyline
                          points={sensor.points
                            .split(" ")
                            .map((point) => {
                              const [x, y] = point.split(",").map(Number)
                              return `${(x / 74) * 240},${(y / 30) * 52 + 2}`
                            })
                            .join(" ")}
                        />
                      </svg>
                      <span>−30m</span>
                      <span>Now</span>
                    </div>
                    <div className="sensor-foot">
                      <span>
                        <i /> {sensor.status}
                      </span>
                      <small>Updated 8 sec ago</small>
                    </div>
                  </article>
                ))}
              </div>
            </article>
          </section>
        </div>
      </main>
      <div className={`toast ${notice ? "show" : ""}`} role="status">
        {notice}
      </div>
    </div>
  )
}
