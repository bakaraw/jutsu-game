type LM = { x: number; y: number; z: number };

export function frameFeatures(hands: LM[][], w: number, h: number): Float32Array {
  const parsed = hands.slice(0, 2).map((hand) => {
    const pts = hand.map((l) => [l.x * w, l.y * h, l.z * w]);
    const [wx, wy, wz] = pts[0];
    const rel = pts.map((p) => [p[0] - wx, p[1] - wy, p[2] - wz]);
    const scale = Math.hypot(rel[9][0], rel[9][1], rel[9][2]) || 1;
    const feats = rel.slice(1).flatMap((p) => p.map((v) => v / scale));
    return { feats, wrist: [wx, wy, wz], scale };
  }).sort((a, b) => a.wrist[0] - b.wrist[0]); // leftmost wrist first

  const out = new Float32Array(124);
  if (!parsed.length) return out;
  out.set(parsed[0].feats, 0);
  if (parsed.length === 2) {
    out.set(parsed[1].feats, 60);
    const ms = (parsed[0].scale + parsed[1].scale) / 2;
    for (let i = 0; i < 3; i++) out[120 + i] = (parsed[1].wrist[i] - parsed[0].wrist[i]) / ms;
  }
  out[123] = parsed.length;
  return out;
}
