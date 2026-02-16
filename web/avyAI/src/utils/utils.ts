export function fmtDate(epoch: number) {
    return new Date(epoch * 1000).toLocaleDateString();
}

export function aziToCardinal(deg: number) {
    const d = ((deg % 360) + 360) % 360; // normalize to [0, 360)
    if (d >= 315 || d < 45) return "N";
    if (d >= 45 && d < 135) return "E";
    if (d >= 135 && d < 225) return "S";
    return "W"; // 225–315
}