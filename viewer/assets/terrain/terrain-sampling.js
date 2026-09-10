/** Coordinates: local azimuthal equidistant metres, x east, z south. */
export function sampleElevation(elevations, metadata, x, z) {
  const u = (x - metadata.minX) / metadata.dx;
  const v = (z - metadata.minZ) / metadata.dz;
  const { width, height } = metadata;
  if (u < 0 || v < 0 || u > width - 1 || v > height - 1) return null;
  const c = Math.min(Math.floor(u), width - 2);
  const r = Math.min(Math.floor(v), height - 2);
  const tx = u - c, tz = v - r, a = r * width + c;
  const north = elevations[a] * (1 - tx) + elevations[a + 1] * tx;
  const south = elevations[a + width] * (1 - tx) + elevations[a + width + 1] * tx;
  return north * (1 - tz) + south * tz;
}

export function sampleWorldY(elevations, metadata, x, z) {
  const elevation = sampleElevation(elevations, metadata, x, z);
  return elevation === null ? null : elevation - metadata.heightOffsetM;
}

/** Safe little-endian load, including environments without native little endian. */
export async function loadHeightGrid(metadataUrl) {
  const metaResponse = await fetch(metadataUrl);
  if (!metaResponse.ok) throw new Error(`Height metadata: HTTP ${metaResponse.status}`);
  const metadata = await metaResponse.json();
  const dataUrl = new URL(metadata.file, new URL(metadataUrl, globalThis.location?.href));
  const response = await fetch(dataUrl);
  if (!response.ok) throw new Error(`Height binary: HTTP ${response.status}`);
  const buffer = await response.arrayBuffer();
  if (buffer.byteLength !== metadata.width * metadata.height * 4) {
    throw new Error('Height binary has incorrect dimensions');
  }
  const view = new DataView(buffer);
  const elevations = new Float32Array(metadata.width * metadata.height);
  for (let i = 0; i < elevations.length; i++) elevations[i] = view.getFloat32(i * 4, true);
  return { metadata, elevations };
}
