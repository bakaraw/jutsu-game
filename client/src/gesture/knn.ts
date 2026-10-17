export type KnnModel = { classes: string[]; k: number; X: Float32Array; y: Int32Array; dim: number };

export async function loadKnn(url: string): Promise<KnnModel> {
  const j = await (await fetch(url)).json();
  const dim = j.X[0].length;
  return {
    classes: j.classes,
    k: j.k,
    X: Float32Array.from(j.X.flat()),
    y: Int32Array.from(j.y),
    dim,
  };
}

export function predict(m: KnnModel, x: Float32Array) {
  const n = m.y.length;
  const best: { d: number; c: number }[] = []; // k nearest, kept sorted

  for (let i = 0; i < n; i++) {
    let s = 0;
    const off = i * m.dim;
    for (let j = 0; j < m.dim; j++) {
      const diff = m.X[off + j] - x[j];
      s += diff * diff;
    }
    if (best.length < m.k || s < best[best.length - 1].d) {
      best.push({ d: s, c: m.y[i] });
      best.sort((a, b) => a.d - b.d);
      if (best.length > m.k) best.pop();
    }
  }

  // distance-weighted vote, same as weights="distance"
  const votes = new Float64Array(m.classes.length);
  for (const { d, c } of best) votes[c] += 1 / (Math.sqrt(d) + 1e-9);
  const total = votes.reduce((a, b) => a + b, 0);
  let top = 0;
  for (let c = 1; c < votes.length; c++) if (votes[c] > votes[top]) top = c;

  return {
    label: m.classes[top],
    confidence: votes[top] / total,
    nearestDist: Math.sqrt(best[0].d), // use this for the max-dist rejection
  };
} 
