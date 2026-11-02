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
      <circle cx="12" cy="12" r="3" />
      <path d="M19 13.5v-3l-2-.7-.6-1.4.9-1.9-2.1-2.1-1.9.9-1.4-.6-.7-2h-3l-.7 2-1.4.6-1.9-.9-2.1 2.1.9 1.9-.6 1.4-2 .7v3l2 .7.6 1.4-.9 1.9 2.1 2.1 1.9-.9 1.4.6.7 2h3l.7-2 1.4-.6 1.9.9 2.1-2.1-.9-1.9.6-1.4 2-.7Z" />
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
        <div className="brand">
          <span className="brand-mark">
            <img src="/assets/sr-white-transparent.svg" alt="" />
          </span>
          <span className="brand-copy">
            <strong>SELVARITHIK</strong>
            <small>A&amp;D</small>
          </span>
        </div>

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
          <div className="gateway-card">
            <div className="gateway-card-head">
              <span className="gateway-glyph">
                <Icon name="radio" size={15} />
              </span>
              <span className="online-pill">
                <i /> Online
              </span>
            </div>
            <strong>ESP32 Gateway</strong>
            <p>915 MHz · v2.8.4</p>
            <div>
              <span>Uptime</span>
              <b>42d 18h</b>
            </div>
          </div>
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
        </div>
      </aside>

      <main className="dashboard">
        <header className="topbar">
          <span className="topbar-page">System Overview</span>
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
              <i /> <span>Gateway online</span>
            </div>
            <button
              className="icon-button"
              aria-label="Notifications"
              onClick={() => announce("1 active system problem")}
            >
              <Icon name="bell" size={18} />
              <span className="notification-dot" />
            </button>
            <button
              className="primary-button"
              onClick={() => announce("Widget library opened")}
            >
              <Icon name="plus" size={16} /> Add widget
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
            <article className="stat-card">
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
            <article className="stat-card">
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
            <article className="panel telemetry-panel">
              <div className="panel-header">
                <div>
                  <p className="section-kicker">Live telemetry</p>
                  <h2>Network throughput</h2>
                </div>
                <button
                  className="ghost-button"
                  onClick={() => announce("Full telemetry opened")}
                >
                  View telemetry <Icon name="arrow" size={15} />
                </button>
              </div>
              <div className="chart-summary">
                <div>
                  <span>Packets received</span>
                  <strong>{current.packets}</strong>
                  <small>{current.label}</small>
                </div>
                <div className="chart-metrics">
                  <span>
                    <small>Success rate</small>
                    <b>{current.rate}</b>
                  </span>
                  <span>
                    <small>Peak / min</small>
                    <b>{current.peak}</b>
                  </span>
                </div>
                <div className="legend">
                  <span>
                    <i className="red" /> Packets
                  </span>
                  <span>
                    <i className="gray" /> Signal quality
                  </span>
                </div>
              </div>
              <div className="chart-wrap">
                <div className="y-axis">
                  <span>240</span>
                  <span>180</span>
                  <span>120</span>
                  <span>60</span>
                  <span>0</span>
                </div>
                <svg
                  className="chart"
                  viewBox="0 0 760 238"
                  preserveAspectRatio="none"
                  role="img"
                  aria-label="Network packet throughput and signal quality"
                >
                  <defs>
                    <linearGradient
                      id="redGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="0%" stopColor="#e7222e" stopOpacity=".2" />
                      <stop offset="100%" stopColor="#e7222e" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <g className="grid-lines">
                    <line x1="0" y1="10" x2="760" y2="10" />
                    <line x1="0" y1="64" x2="760" y2="64" />
                    <line x1="0" y1="118" x2="760" y2="118" />
                    <line x1="0" y1="172" x2="760" y2="172" />
                    <line x1="0" y1="226" x2="760" y2="226" />
                  </g>
                  <path
                    className="signal-line"
                    d="M0 170 C50 160 70 166 110 145 S180 153 220 132 S290 141 330 111 S405 124 450 96 S520 105 565 81 S635 91 680 66 S730 72 760 58"
                  />
                  <path
                    className="area"
                    d="M0 193 C45 182 70 188 108 162 S174 175 218 140 S286 151 328 110 S399 132 446 88 S515 108 560 68 S628 82 673 46 S722 62 760 28 L760 238 L0 238 Z"
                  />
                  <path
                    className="packet-line"
                    d="M0 193 C45 182 70 188 108 162 S174 175 218 140 S286 151 328 110 S399 132 446 88 S515 108 560 68 S628 82 673 46 S722 62 760 28"
                  />
                  <circle className="chart-point" cx="673" cy="46" r="5" />
                </svg>
                <div className="x-axis">
                  <span>13:30</span>
                  <span>13:45</span>
                  <span>14:00</span>
                  <span>14:15</span>
                  <span>14:30</span>
                </div>
              </div>
            </article>

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
                  <article className="sensor-card" key={sensor.name}>
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
