export default function SignalSphere() {
  return (
    <div className="signal-sphere" aria-hidden="true">
      <div className="signal-sphere-core" />
      <div className="signal-sphere-ring signal-sphere-ring-one" />
      <div className="signal-sphere-ring signal-sphere-ring-two" />
      <div className="signal-sphere-ring signal-sphere-ring-three" />
      <span className="signal-sphere-node signal-sphere-node-one" />
      <span className="signal-sphere-node signal-sphere-node-two" />
    </div>
  );
}
