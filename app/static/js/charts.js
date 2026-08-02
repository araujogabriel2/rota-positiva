(function () {
  const data = window.dashboardData;
  if (!data) return;
  const palette = { revenue: "#53a7bf", profit: "#35c59f", grid: "#2b353a", text: "#a8b4b9" };

  function setup(canvas) {
    const ratio = window.devicePixelRatio || 1;
    const box = canvas.getBoundingClientRect();
    canvas.width = box.width * ratio;
    canvas.height = box.height * ratio;
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    return { ctx, width: box.width, height: box.height };
  }

  function lineChart() {
    const canvas = document.getElementById("dailyChart");
    if (!canvas) return;
    const { ctx, width, height } = setup(canvas);
    const pad = { l: 45, r: 15, t: 20, b: 36 };
    const values = [...data.revenue, ...data.profit, 0];
    const min = Math.min(...values);
    const max = Math.max(...values, 1);
    const range = max - min || 1;
    ctx.font = "11px system-ui";
    ctx.strokeStyle = palette.grid;
    ctx.fillStyle = palette.text;
    for (let i = 0; i <= 4; i++) {
      const y = pad.t + (height - pad.t - pad.b) * (i / 4);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke();
      const label = max - range * (i / 4);
      ctx.fillText(label >= 1000 ? `${(label / 1000).toFixed(1)}k` : label.toFixed(0), 3, y + 4);
    }
    if (!data.labels.length) { ctx.fillText("Sem dados no período", pad.l, height / 2); return; }
    const xAt = (i) => pad.l + (width - pad.l - pad.r) * (data.labels.length === 1 ? .5 : i / (data.labels.length - 1));
    const yAt = (v) => pad.t + (height - pad.t - pad.b) * ((max - v) / range);
    function draw(series, color) {
      ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.lineJoin = "round"; ctx.beginPath();
      series.forEach((v, i) => i ? ctx.lineTo(xAt(i), yAt(v)) : ctx.moveTo(xAt(i), yAt(v)));
      ctx.stroke();
      ctx.fillStyle = color;
      series.forEach((v, i) => { ctx.beginPath(); ctx.arc(xAt(i), yAt(v), 3.5, 0, Math.PI * 2); ctx.fill(); });
    }
    draw(data.revenue, palette.revenue); draw(data.profit, palette.profit);
    const step = Math.max(1, Math.ceil(data.labels.length / 7));
    data.labels.forEach((label, i) => { if (i % step === 0 || i === data.labels.length - 1) { ctx.fillStyle = palette.text; ctx.textAlign = "center"; ctx.fillText(label, xAt(i), height - 12); } });
    ctx.textAlign = "left"; ctx.fillStyle = palette.revenue; ctx.fillRect(pad.l, 4, 12, 3); ctx.fillStyle = palette.text; ctx.fillText("Faturamento", pad.l + 17, 8);
    ctx.fillStyle = palette.profit; ctx.fillRect(pad.l + 105, 4, 12, 3); ctx.fillStyle = palette.text; ctx.fillText("Lucro", pad.l + 122, 8);
  }

  function doughnut() {
    const canvas = document.getElementById("categoryChart");
    if (!canvas) return;
    const { ctx, width, height } = setup(canvas);
    const colors = ["#16a085", "#f2a33a", "#c56f61", "#24677a", "#80611f", "#795a9c", "#5f7b83", "#42a5b3"];
    const total = data.category_values.reduce((a, b) => a + b, 0);
    const cx = width / 2, cy = Math.min(height * .38, 105), radius = Math.min(width * .28, 72);
    if (!total) { ctx.fillStyle = palette.text; ctx.textAlign = "center"; ctx.fillText("Sem despesas no período", cx, cy); return; }
    let angle = -Math.PI / 2;
    data.category_values.forEach((value, i) => {
      const next = angle + (value / total) * Math.PI * 2;
      ctx.beginPath(); ctx.arc(cx, cy, radius, angle, next); ctx.arc(cx, cy, radius * .58, next, angle, true); ctx.closePath(); ctx.fillStyle = colors[i % colors.length]; ctx.fill(); angle = next;
    });
    ctx.fillStyle = "#e8f0f2"; ctx.font = "700 16px system-ui"; ctx.textAlign = "center"; ctx.fillText(new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(total), cx, cy + 5);
    ctx.font = "11px system-ui"; ctx.textAlign = "left";
    data.category_labels.slice(0, 6).forEach((label, i) => { const y = 195 + i * 18; ctx.fillStyle = colors[i % colors.length]; ctx.fillRect(15, y - 8, 10, 10); ctx.fillStyle = palette.text; ctx.fillText(label, 31, y); });
  }

  function drawAll() { lineChart(); doughnut(); }
  drawAll();
  let timer;
  window.addEventListener("resize", () => { clearTimeout(timer); timer = setTimeout(drawAll, 150); });
})();
