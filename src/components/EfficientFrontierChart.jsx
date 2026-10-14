import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
} from "recharts";

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div
        style={{
          background: "white",
          border: "1px solid #dce1dd",
          borderRadius: "8px",
          padding: "12px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          fontSize: "13px",
          color: "#17201f",
        }}
      >
        <div style={{ marginBottom: "4px", fontWeight: "600" }}>
          Efficient Frontier Point
        </div>
        <div style={{ color: "#68716e" }}>
          Volatility: <strong>{data.volatility.toFixed(2)}%</strong>
        </div>
        <div style={{ color: "#68716e" }}>
          Expected return: <strong>{data.return.toFixed(2)}%</strong>
        </div>
      </div>
    );
  }
  return null;
};

function EfficientFrontierChart({ efficientFrontier, _expectedReturn, _volatility }) {
  const chartData = efficientFrontier.map((point) => ({
    volatility: point.volatility,
    return: point.return,
    isOptimal: point.is_optimal,
  }));

  const sortedData = [...chartData].sort((a, b) => a.volatility - b.volatility);

  return (
    <div className="efficient-frontier-chart">
      <p className="chart-label">EFFICIENT FRONTIER</p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart margin={{ top: 20, right: 30, left: 10, bottom: 20 }} data={sortedData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7ebe8" />
          <XAxis
            dataKey="volatility"
            name="Volatility"
            unit="%"
            tick={{ fill: "#68716e", fontSize: 12 }}
            tickLine={{ stroke: "#dce1dd" }}
            axisLine={{ stroke: "#dce1dd" }}
            label={{
              value: "Volatility (%)",
              position: "insideBottom",
              offset: -5,
              style: { fill: "#68716e", fontSize: 12 },
            }}
          />
          <YAxis
            dataKey="return"
            name="Expected return"
            unit="%"
            tick={{ fill: "#68716e", fontSize: 12 }}
            tickLine={{ stroke: "#dce1dd" }}
            axisLine={{ stroke: "#dce1dd" }}
            label={{
              value: "Expected return (%)",
              angle: -90,
              position: "insideLeft",
              offset: -5,
              style: { fill: "#68716e", fontSize: 12 },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="return"
            stroke="#1f6f68"
            strokeWidth={1.5}
            dot={(props) => {
              const { cx, cy, payload } = props;
              return (
                <circle
                  cx={cx}
                  cy={cy}
                  r={payload.isOptimal ? 8 : 5}
                  fill="#1f6f68"
                  fillOpacity={payload.isOptimal ? 1 : 0.6}
                  stroke={payload.isOptimal ? "#17201f" : "none"}
                  strokeWidth={payload.isOptimal ? 2 : 0}
                />
              );
            }}
            activeDot={{ r: 8 }}
            strokeOpacity={0.4}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-dot frontier-dot"></span>
          <span>Efficient frontier portfolios</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot optimal-dot"></span>
          <span>Model result (max Sharpe)</span>
        </div>
      </div>
    </div>
  );
}

export default EfficientFrontierChart;
