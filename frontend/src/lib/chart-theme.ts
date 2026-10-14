import * as echarts from 'echarts';

/**
 * Delphi's visualization language, registered once as an ECharts theme.
 *
 * Principles:
 *  - one emphasis color (vermilion) + muted scientific supports;
 *  - hairline axes and split lines that match the surface tokens;
 *  - Inter for labels, tabular numerals, no gradients or shadows;
 *  - identical styling in every chart so a visualization is recognizably Delphi.
 *
 * Colors are resolved from the CSS custom properties at registration time so
 * charts follow the active theme. Call `registerChartTheme()` after theme
 * changes; chart components pass `theme="delphi"`.
 */

const FALLBACKS = {
  light: {
    palette: ['#c2410c', '#64748b', '#4d7c5f', '#b45309', '#86589b', '#4e7f96'],
    text: '#3f3d39',
    subtext: '#7c7a75',
    axis: '#d9d7d2',
    split: '#eceae6',
    tooltipBg: '#ffffff',
  },
  dark: {
    palette: ['#e2683c', '#94a3b8', '#7fa98c', '#d19740', '#ab7fbd', '#7fa6b8'],
    text: '#d6d4d0',
    subtext: '#8f8d88',
    axis: '#3a3835',
    split: '#2b2926',
    tooltipBg: '#26241f',
  },
} as const;

function cssVar(name: string): string | undefined {
  if (typeof window === 'undefined') return undefined;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || undefined;
}

export function registerChartTheme(): void {
  const isDark =
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark');
  const fb = isDark ? FALLBACKS.dark : FALLBACKS.light;

  const palette = [
    cssVar('--chart-1') ?? fb.palette[0],
    cssVar('--chart-2') ?? fb.palette[1],
    cssVar('--chart-3') ?? fb.palette[2],
    cssVar('--chart-4') ?? fb.palette[3],
    cssVar('--chart-5') ?? fb.palette[4],
    cssVar('--chart-6') ?? fb.palette[5],
  ];

  const axisLine = { lineStyle: { color: fb.axis } };
  const splitLine = { lineStyle: { color: fb.split, type: 'solid' as const } };
  const fontFamily =
    "'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif";

  echarts.registerTheme('delphi', {
    color: palette,
    backgroundColor: 'transparent',
    textStyle: { fontFamily, color: fb.text },
    title: {
      textStyle: { fontFamily, color: fb.text, fontSize: 13, fontWeight: 600 },
      subtextStyle: { fontFamily, color: fb.subtext, fontSize: 11 },
    },
    legend: {
      textStyle: { fontFamily, color: fb.subtext, fontSize: 11 },
      icon: 'circle',
      itemWidth: 8,
      itemHeight: 8,
    },
    tooltip: {
      backgroundColor: fb.tooltipBg,
      borderColor: fb.axis,
      borderWidth: 1,
      textStyle: { fontFamily, color: fb.text, fontSize: 12 },
      extraCssText: 'box-shadow: 0 8px 24px rgb(0 0 0 / 0.12); border-radius: 8px;',
    },
    categoryAxis: {
      axisLine,
      axisTick: { show: false },
      axisLabel: { fontFamily, color: fb.subtext, fontSize: 10 },
      splitLine: { show: false },
    },
    valueAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontFamily, color: fb.subtext, fontSize: 10 },
      splitLine,
    },
    bar: { itemStyle: { borderRadius: [3, 3, 0, 0] }, barMaxWidth: 28 },
    line: { symbolSize: 5, lineStyle: { width: 2 }, smooth: false },
    heatmap: { itemStyle: { borderColor: fb.tooltipBg, borderWidth: 1 } },
  });
}
