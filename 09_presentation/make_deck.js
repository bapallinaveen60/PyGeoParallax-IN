// PyGeoParallax-IN — M.Tech thesis review deck (pptxgenjs, structured: theme, layouts, sections).
const path = require("path");
const pptxgen = require("pptxgenjs");
const SKILL = "C:/Users/baipa/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/local-agent-mode-sessions/skills-plugin/e83ffeaf-7047-47de-bb96-cc01186f6837/58a76c7c-fc5b-4255-a7cc-db24c8e9aab1/skills/pptx";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const REPO = "D:/Projects/@GeoVision/PyGeoParallax-IN";
const FIG = (n) => `${REPO}/07_figures/paper/${n}.png`;
const DEMO = "C:/Users/baipa/AppData/Local/Temp/claude/D--Projects--GeoVision-PyGeoParallax-IN/d41600e3-c7e3-471a-b8f3-22511e0efabb/scratchpad/pygeoparallax_demo/demo.png";
const OUT = `${REPO}/09_presentation/PyGeoParallax-IN_MTech_review.pptx`;
const ASPECT = { fig0_schematic: 1.705, fig1_geometry: 1.106, fig2_navigation: 1.44, fig3_cases: 1.883, fig4_states: 1.431,
  fig5_heights: 0.923, fig6_terrain: 1.013, fig7_meteosat_tilt: 3.018, demo: 3.261 };

const THEME = {
  name: "PyGeoParallax-IN",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1A1A1A", lt1: "FFFFFF", dk2: "1F3864", lt2: "F2F2F2",
    accent1: "1F3864", accent2: "A23B2A", accent3: "6B6B6B", accent4: "4A6FA5", accent5: "C0504D", accent6: "8C8C8C",
    hlink: "1F3864", folHlink: "6B6B6B",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Naveen Bapalli";
pres.title = "Parallax correction of INSAT-3DR imagery over India";
const C = pres.SchemeColor;
const W = 13.333, H = 7.5, MX = 0.6;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: "TITLE",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.0, w: 11.5, h: 1.9, fontSize: 38, bold: true, color: C.text2, valign: "bottom", align: "left", fontFace: "Cambria" }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 0.9, y: 4.05, w: 11.5, h: 0.8, fontSize: 21, color: C.accent3, valign: "top" }, text: "" } },
    { placeholder: { options: { name: "meta", type: "body", x: 0.9, y: 5.75, w: 11.5, h: 0.9, fontSize: 16, color: C.text1, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "number", type: "body", x: 0.9, y: 2.3, w: 3, h: 1.1, fontSize: 30, bold: false, color: C.accent3, fontFace: "Cambria", valign: "bottom" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 3.45, w: 11.5, h: 1.0, fontSize: 36, bold: true, color: C.text2, fontFace: "Cambria", valign: "top", align: "left" }, text: "" } },
    { placeholder: { options: { name: "blurb", type: "body", x: 0.9, y: 4.5, w: 10.5, h: 1.2, fontSize: 18, color: C.accent3, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.35, w: W - 2 * MX, h: 0.95, fontSize: 30, bold: true, color: C.text1, fontFace: "Cambria", valign: "middle", align: "left", margin: 0 }, text: "" } },
    { text: { text: "PyGeoParallax-IN  ·  M.Tech thesis review", options: { x: MX, y: 7.02, w: 6, h: 0.3, fontSize: 10, color: C.accent3, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontSize: 10, color: C.accent3, align: "right" },
});

// ------------------------------------------------------------------ helpers
let section = "";
const notes = (s, t) => s.addNotes(t);
function content(title) {
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function divider(num, title, blurb) {
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: section });
  s.addText(num, { placeholder: "number" });
  s.addText(title, { placeholder: "title" });
  s.addText(blurb, { placeholder: "blurb" });
  return s;
}
function fit(name, x, y, w, h, align = "center") {
  const a = ASPECT[name];
  let iw = w, ih = w / a;
  if (ih > h) { ih = h; iw = h * a; }
  const ix = align === "left" ? x : x + (w - iw) / 2;
  return { x: ix, y: y + (h - ih) / 2, w: iw, h: ih };
}
function figure(s, name, x, y, w, h, alt, align) {
  const b = fit(name, x, y, w, h, align);
  s.addImage({ path: name === "demo" ? DEMO : FIG(name), ...b, altText: alt, objectName: `figure ${name}` });
  return b;
}
function takeaway(s, text, y = 6.35) {
  s.addText(text, { x: MX, y, w: W - 2 * MX, h: 0.5, fontSize: 16, italic: true, color: C.text1, isTextBox: true, margin: 0, objectName: "takeaway" });
}
function stat(s, x, y, w, big, label, color = C.accent1, bigSize = 30) {
  s.addText(big, { x, y, w, h: 0.62, fontSize: bigSize, bold: true, color, fontFace: "Cambria", isTextBox: true, margin: 0, objectName: `stat ${big}` });
  s.addText(label, { x, y: y + 0.64, w, h: 0.62, fontSize: 13, color: C.accent3, isTextBox: true, margin: 0, valign: "top", objectName: `stat label ${big}` });
}
function card(s, x, y, w, h, head, body, opts = {}) {
  s.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: opts.fill || C.background2 }, line: { color: opts.fill || C.background2 }, objectName: `card ${head}` });
  s.addText(head, { x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.42, fontSize: opts.headSize || 16, bold: true, color: opts.headColor || C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addText(body, { x: x + 0.22, y: y + 0.62, w: w - 0.44, h: h - 0.78, fontSize: opts.bodySize || 14, color: C.text1, isTextBox: true, margin: 0, valign: "top", paraSpaceAfter: 4 });
}
function badge(s, x, y, n, color = C.accent1) {
  s.addText(String(n), { x, y, w: 0.48, h: 0.48, fontSize: 22, bold: true, color, fontFace: "Cambria", align: "left", valign: "middle", isTextBox: true, margin: 0, objectName: `number ${n}` });
}
function bullets(s, items, x, y, w, h, size = 15) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1 } })),
    { x, y, w, h, fontSize: size, color: C.text1, valign: "top", paraSpaceAfter: 8, isTextBox: true, margin: 0 });
}
function chip(s, x, y, w, text, color) {
  s.addText(text, { x, y, w, h: 0.36, fontSize: 16, bold: true, color, align: "left", valign: "middle", isTextBox: true, margin: 0 });
}
const AX = { catAxisLabelColor: HEX.accent3, valAxisLabelColor: HEX.accent3, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valGridLine: { color: "E1E5E8", size: 0.75 }, catGridLine: { style: "none" },
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, titleFontFace: "+mn-lt", titleFontSize: 13, titleColor: HEX.dk1,
  legendFontFace: "+mn-lt", legendFontSize: 12, valAxisTitleFontFace: "+mn-lt", catAxisTitleFontFace: "+mn-lt",
  valAxisTitleColor: HEX.accent3, catAxisTitleColor: HEX.accent3, valAxisTitleFontSize: 12, catAxisTitleFontSize: 12 };

// ================================================================== 1. OPENING
section = "Opening";
pres.addSection({ title: section });
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
  s.addText("Parallax correction of INSAT-3DR imagery over India", { placeholder: "title" });
  s.addText("An open-source tool and the limits of validation against GPM radar", { placeholder: "subtitle" });
  s.addText("Naveen Bapalli\nM.Tech thesis review  ·  November 2026", { placeholder: "meta" });
  notes(s, "Good morning. My thesis is about a geometric error in India's geostationary weather imagery, cloud parallax: what it is, how to correct it, and, the part that turned out to be most interesting, how far we can actually verify the correction with radar from space. Over the next thirty minutes I will go through the problem, the method, the validation against GPM, a second-satellite test that explains the main puzzle, the open-source tool, and the conclusions.");
}
{
  const s = content("Tall clouds appear in the wrong place in geostationary images");
  figure(s, "fig0_schematic", MX, 1.45, 7.6, 4.7, "Cross-section of cloud and terrain parallax for a geostationary view", "left");
  stat(s, 8.75, 1.65, 4.0, "h · tan(VZA)", "displacement of a cloud top at height h, away from the satellite", C.accent1, 30);
  stat(s, 8.75, 3.15, 4.0, "≈ 10 km", "for a 15 km monsoon cloud top at a 35° viewing angle", C.accent2);
  stat(s, 8.75, 4.65, 4.0, "4 km", "INSAT-3DR infrared pixel: the error is 2–3 pixels", C.accent3);
  takeaway(s, "Satellite images are mapped as if every pixel lay on the ground. A high cloud does not.");
  notes(s, "This schematic shows the problem. The imager is geolocated as if everything it sees is on the Earth's surface. A cloud top several kilometres up lies on the same line of sight but closer to the satellite, so it appears displaced away from the sub-satellite point. The displacement is roughly the cloud height times the tangent of the viewing zenith angle. For a 15 km monsoon cloud at 35 degrees that is about 10 km, two to three INSAT pixels. Terrain does the same thing for the ground itself, on a smaller scale.");
}
{
  const s = content("India is unusually exposed: INSAT-3DR looks at it from 74° E");
  figure(s, "fig1_geometry", MX, 1.4, 6.0, 4.85, "Viewing zenith angle and parallax shift over South Asia", "left");
  stat(s, 7.2, 1.6, 5.4, "33–38°", "viewing angle over the Himalaya and Northeast India");
  stat(s, 7.2, 3.0, 5.4, "8–12 km", "apparent displacement of deep convective tops there");
  stat(s, 7.2, 4.4, 5.4, "every product", "rainfall estimates, cloud masks and ML classifiers inherit the error", C.accent2, 28);
  takeaway(s, "The error is largest exactly where monsoon convection is deepest.");
  notes(s, "INSAT-3DR sits at 74 degrees east, near the western edge of the country. Over the Himalaya and Northeast India the viewing angle reaches 33 to 38 degrees, and monsoon convection reaches the tropopause at 15 to 17 km. So the deepest storms appear 8 to 12 km from their true position. Every downstream product, rainfall estimates, cloud masks, machine-learning classifications, inherits that, and any comparison with radar or gauges mixes it with the real error.");
}
{
  const s = content("What was missing before this work");
  card(s, MX, 1.5, 3.85, 2.9, "No validated correction", "For INSAT-3D/3DR only an undocumented internal shift exists, inside ISRO's Hydro-Estimator rain product. Nothing has quantified or validated it.");
  card(s, MX + 4.05, 1.5, 3.85, 2.9, "No test of verification", "How much of a correction can radar from space actually confirm for monsoon storms? Not known.");
  card(s, MX + 8.1, 1.5, 3.53, 2.9, "No open tool", "Nothing produced matched corrected and uncorrected INSAT data, with terrain and navigation, for others to use.");
  s.addText("Objectives", { x: MX, y: 4.7, w: 4, h: 0.4, fontSize: 18, bold: true, color: C.text1, isTextBox: true, margin: 0 });
  bullets(s, [
    "Build an exact, open parallax correction for INSAT-3DR",
    "Validate it against GPM radar over several monsoons and regions",
    "Find out what limits radar-based validation, and why",
  ], MX, 5.15, 11.5, 1.2, 15);
  notes(s, "Before this work there were three gaps. First, no documented and validated parallax correction for INSAT-3D or 3DR; the only trace is an internal shift in ISRO's Hydro-Estimator rain algorithm, never quantified. Second, nobody had tested how much of such a correction spaceborne radar can verify for monsoon storms. Third, there was no open tool to produce matched corrected and uncorrected datasets. My objectives follow directly from these gaps.");
}
{
  const s = content("Six contributions");
  const items = [
    ["Open-source tool", "Exact ray tracing on the WGS84 ellipsoid, terrain, occlusion-aware regridding, native-grid output"],
    ["GPM validation", "63 coincident monsoon overpasses, 2018–2024, four regions, two offset measures"],
    ["Limits of radar validation", "GPM can verify absolute position only to about ±3–5 km for monsoon convection"],
    ["Second-satellite test", "Meteosat confirms the correction without radar and locates the cause of the GPM limit"],
    ["INSAT-3DR navigation", "A seasonal geolocation error of 7–20 km to the west in winter"],
    ["Downstream test", "A precipitation-type U-Net retrained on corrected input (Appendix A)"],
  ];
  items.forEach(([head, body], i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = MX + col * 6.1, y = 1.55 + row * 1.6;
    badge(s, x, y + 0.05, i + 1, i === 3 ? C.accent2 : C.accent1);
    s.addText(head, { x: x + 0.65, y, w: 5.3, h: 0.45, fontSize: 17, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addText(body, { x: x + 0.65, y: y + 0.45, w: 5.3, h: 0.95, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  });
  notes(s, "These are the six contributions. The tool; the GPM validation; the finding that radar can verify absolute position only to a few kilometres; the second-satellite test with Meteosat, which I highlight because it resolved the main puzzle; the characterisation of INSAT-3DR navigation; and a downstream machine-learning test, which is in the appendix of the paper.");
}

// ================================================================== 2. METHOD
section = "Method";
pres.addSection({ title: section });
divider("01", "Method", "From a raw INSAT-3DR L1C file to a corrected image");
{
  const s = content("Five steps from a raw L1C file to a corrected image");
  const steps = [
    ["Read L1C", "BT from look-up tables; pixel lat/lon from the Mercator grid"],
    ["Navigation", "Shift measured from clear-sky coastlines"],
    ["Cloud-top height", "10.8 µm BT through AFGL or ERA5 profiles"],
    ["Ray tracing", "Line of sight to the cloud top on the WGS84 ellipsoid"],
    ["Regridding", "Highest cloud wins; gaps flagged, never invented"],
  ];
  const bw = 2.15, gap = 0.28, y = 1.75;
  steps.forEach(([head, body], i) => {
    const x = MX + i * (bw + gap);
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: bw, h: 2.55, fill: { color: i === 3 ? "E6EAF2" : C.background2 }, line: { color: i === 3 ? "E6EAF2" : C.background2 }, objectName: `step ${i + 1}` });
    badge(s, x + 0.2, y + 0.2, i + 1, i === 3 ? C.accent2 : C.accent1);
    s.addText(head, { x: x + 0.2, y: y + 0.8, w: bw - 0.4, h: 0.45, fontSize: 16, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addText(body, { x: x + 0.2, y: y + 1.27, w: bw - 0.4, h: 1.2, fontSize: 13, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
    if (i < steps.length - 1) s.addShape(pres.shapes.CHEVRON, { x: x + bw + 0.07, y: y + 1.12, w: 0.14, h: 0.28, fill: { color: C.accent3 }, line: { color: C.accent3 }, flipH: false, objectName: `arrow ${i + 1}` });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 4.75, w: 7.4, h: 0.62, fill: { color: C.background2 }, line: { color: "D0D0D0" } });
  s.addText("pygeoparallax l1c  \"3RIMG_*.h5\"  -o corrected/  --native", { x: MX + 0.25, y: 4.75, w: 7.0, h: 0.62, fontSize: 15, fontFace: "Courier New", color: C.text1, valign: "middle", isTextBox: true, margin: 0 });
  s.addText("One command runs all five steps on a whole archive, in parallel.", { x: 8.3, y: 4.75, w: 4.4, h: 0.62, fontSize: 14, color: C.accent3, valign: "middle", isTextBox: true, margin: 0 });
  takeaway(s, "Corrected and uncorrected images come out on the same grid, so the effect of the correction can be measured.");
  notes(s, "The pipeline has five steps. Read the L1C file and decode brightness temperatures; apply a navigation correction measured from coastlines; estimate cloud-top height from the 10.8 micron channel; trace each line of sight to that height on the ellipsoid; and regrid. The same regridding is run without correction to give an uncorrected baseline on exactly the same grid. In the tool all of this is one command.");
}
{
  const s = content("The solver is exact: ray tracing on the WGS84 ellipsoid");
  s.addText("Line of sight from the satellite S through the apparent ground point P, intersected with the ellipsoid enlarged by the cloud height h:", { x: MX, y: 1.5, w: 6.3, h: 0.9, fontSize: 15, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addShape(pres.shapes.RECTANGLE, { x: MX, y: 2.5, w: 6.3, h: 0.95, fill: { color: C.background2 }, line: { color: C.background2 } });
  s.addText("(x² + y²) / (a + h)²  +  z² / (b + h)²  =  1", { x: MX, y: 2.5, w: 6.3, h: 0.95, fontSize: 22, fontFace: "Cambria", italic: true, color: C.text1, align: "center", valign: "middle", isTextBox: true, margin: 0 });
  bullets(s, [
    "Solved in closed form, then one Newton step on the true geodetic height: error below 1 mm",
    "With terrain: the ground height at the corrected point is found by fixed-point iteration",
    "Numba kernel: a full INSAT disk in 0.5 s",
  ], MX, 3.75, 6.3, 2.3, 15);
  s.addTable([
    [{ text: "Independent check", options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } }, { text: "Agreement", options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } }],
    ["ECEF transform vs pyproj", "< 1 mm"],
    ["Viewing angles vs pyorbital", "0.01°"],
    ["Parallax shift vs satpy (sphere)", "13–25 m on 2.5–8.8 km"],
    ["Synthetic storm, VZA 35°", "10.9 vs 10.5 km expected"],
    ["India scene, full pipeline", "1.8 s (148 scenes)"],
  ], { x: 7.35, y: 1.55, w: 5.4, colW: [3.25, 2.15], fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.75, color: "BFBFBF" }, rowH: 0.52, valign: "middle", margin: [3, 8, 3, 8] });
  takeaway(s, "Any remaining error comes from the inputs, cloud height and navigation, not from the geometry.");
  notes(s, "The geometric core is exact. I intersect the line of sight with an ellipsoid enlarged by the cloud height, which has a closed-form solution, and refine with one Newton step; the error is below a millimetre. Against independent references it agrees with pyproj to a millimetre and with satpy's spherical correction to 25 metres. So for the rest of the talk, any error is in the inputs, the cloud height and the navigation, not in the geometry.");
}
{
  const s = content("Cloud-top height from the 10.8 µm brightness temperature");
  const T = [299.7, 293.7, 287.7, 283.7, 277.0, 270.3, 263.6, 257.0, 250.3, 243.6, 237.0, 230.1, 223.6, 217.0, 210.3, 203.7, 197.0, 194.8];
  const Z = T.map((_, i) => i);
  s.addChart(pres.charts.SCATTER, [{ name: "Temperature", values: T }, { name: "AFGL tropical profile", values: Z }], {
    x: MX, y: 1.4, w: 6.1, h: 4.75, lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 5, chartColors: [HEX.accent1],
    showTitle: true, title: "AFGL tropical atmosphere", showLegend: false,
    valAxisTitle: "height [km]", showValAxisTitle: true, catAxisTitle: "temperature [K]", showCatAxisTitle: true,
    valAxisMinVal: 0, valAxisMaxVal: 18, catAxisMinVal: 190, catAxisMaxVal: 300, ...AX,
  });
  bullets(s, [
    "Cloudy where TIR1 is below 270 K, or 8 K below ISRO's clear-sky BT",
    "Height where the profile has that temperature: AFGL tropical or per-pixel ERA5",
    "Tops colder than the tropopause are capped at 17 km",
    "Effective-height option for rain work: scale · h − offset",
  ], 7.15, 1.6, 5.6, 3.3, 15);
  s.addText("Limit: thin cirrus is partly transparent, so its height comes out too low.", { x: 7.15, y: 5.0, w: 5.6, h: 0.8, fontSize: 14, color: C.accent3, isTextBox: true, margin: 0, valign: "top" });
  takeaway(s, "ERA5 instead of the standard atmosphere changes the storm offsets by less than 0.5 km.");
  notes(s, "Cloud-top height comes from the 10.8 micron brightness temperature. A pixel is cloudy below 270 K, or 8 K below ISRO's clear-sky value, and its height is where the atmospheric profile has that temperature. I use the AFGL tropical atmosphere by default and ERA5 per pixel as an option; for the storms the choice changes offsets by less than half a kilometre. The known limit is thin cirrus. The tool also has an effective-height option, which becomes relevant later.");
}
{
  const s = content("Corrected pixels are regridded without inventing information");
  figure(s, "demo", MX, 1.4, W - 2 * MX, 3.35, "Synthetic storms before and after correction, with the shift applied");
  const rules = [["Collisions", "The highest cloud wins a cell: it hides the others from the satellite."],
    ["Small gaps", "Filled from neighbours within one cell (flag 1)."],
    ["Never seen", "Cells behind tall clouds stay empty (flag 2)."]];
  rules.forEach(([h, b], i) => card(s, MX + i * 4.1, 4.9, 3.85, 1.3, h, b, { headSize: 15, bodySize: 13 }));
  takeaway(s, "Built-in self-test: three synthetic storms return to within one pixel of their true positions.", 6.4);
  notes(s, "After correction, pixels no longer lie on a grid, so regridding needs rules. When several land in one cell the highest wins, because it hides the others from the satellite. Small gaps are interpolated and flagged; cells the satellite never saw stay empty. The figure is the tool's built-in self-test: three storms at known heights are simulated as the satellite would see them, red circles are their true positions, and after correction they return to within a pixel.");
}
{
  const s = content("INSAT-3DR navigation errors are seasonal");
  figure(s, "fig2_navigation", MX, 1.4, 7.4, 4.85, "INSAT-3DR navigation correction from coastline matching, 2022–2024", "left");
  stat(s, 8.4, 1.6, 4.3, "7–20 km", "positions too far east from late September to mid-March", C.accent2);
  stat(s, 8.4, 3.0, 4.3, "≈ 0–3 km", "during the monsoon (per-year values)");
  s.addText("The switch near the equinoxes coincides with the spacecraft's twice-yearly yaw flip. Measured by matching clear-sky coastlines in 13 windows around India.", { x: 8.4, y: 4.45, w: 4.3, h: 1.6, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  takeaway(s, "Outside the monsoon, navigation error is larger than the parallax itself.");
  notes(s, "A side result, but an important one for users. Matching clear-sky coastlines shows that INSAT-3DR L1C positions are 7 to 20 km too far east from late September to mid-March, and nearly right in the monsoon. The switch coincides with the spacecraft's yaw flip. Outside the monsoon this error is larger than the parallax, so it must be corrected first.");
}

// ================================================================== 3. VALIDATION DESIGN
section = "Validation design";
pres.addSection({ title: section });
divider("02", "Validation against GPM radar", "Where are the storms really? The GPM Ku-band radar sees the rain directly");
{
  const s = content("63 coincident GPM overpasses across four regions, 2018–2024");
  const hd = (t) => ({ text: t, options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } });
  s.addTable([
    [hd("Region"), hd("Viewing angle"), hd("Processed"), hd("Usable")],
    ["South India", "9–21°", "17", "14"], ["Central India", "22–33°", "25", "15"],
    ["Himalaya", "29–37°", "11", "4"], ["Northeast India", "31–38°", "10", "5"],
    [{ text: "Total", options: { bold: true } }, "", { text: "63", options: { bold: true } }, { text: "38", options: { bold: true } }],
  ], { x: MX, y: 1.55, w: 6.6, colW: [2.2, 1.7, 1.35, 1.35], fontSize: 15, color: HEX.dk1, border: { type: "solid", pt: 0.75, color: "BFBFBF" }, rowH: 0.55, valign: "middle", margin: [3, 8, 3, 8] });
  bullets(s, [
    "GPM DPR 2A Ku, version 8: storm tops placed on the slanted radar beam",
    "INSAT scan within a few minutes of the overpass",
    "Usable: a convective cluster of 100+ footprints and a reliable match",
    "Bootstrap intervals; Wilcoxon and sign tests per case",
  ], 7.75, 1.6, 5.0, 3.6, 15);
  takeaway(s, "Seven monsoons and the full range of viewing angles over India.");
  notes(s, "The validation uses 63 GPM overpasses that coincide with an INSAT scan within a few minutes, over seven monsoons and four regions spanning the viewing angles over India. 38 are usable. GPM storm tops are placed on the slanted beam, because the radar itself looks at an angle. Statistics are bootstrap intervals with paired tests per case.");
}
{
  const s = content("Two offset measures, each seeing a different part of the storm");
  const panel = (x, title, body, anvilW) => {
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.5, w: 5.9, h: 4.6, fill: { color: C.background2 }, line: { color: C.background2 } });
    s.addText(title, { x: x + 0.3, y: 1.7, w: 5.3, h: 0.45, fontSize: 18, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addShape(pres.shapes.OVAL, { x: x + 2.95 - anvilW / 2, y: 2.4, w: anvilW, h: 1.0, fill: { color: "C8C8C8" }, line: { color: "C8C8C8" } });
    s.addShape(pres.shapes.OVAL, { x: x + 2.65, y: 2.65, w: 0.6, h: 0.5, fill: { color: HEX.accent2 }, line: { color: HEX.accent2 } });
    s.addText(body, { x: x + 0.3, y: 3.65, w: 5.3, h: 2.3, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  };
  panel(MX, "Field measure (storm scale)", "Shift that best correlates the INSAT brightness-temperature field with the GPM storm-top field within 250 km.\n\nDriven by the large cold anvil against the radar's rain area.", 4.4);
  panel(MX + 6.23, "Cell measure (convective core)", "Each GPM deep-echo cell (storm top above 10 km) paired with the nearest INSAT cold core.\n\nDriven by the coldest tops against the tallest echoes.", 2.0);
  takeaway(s, "Both measure the offset along the line of sight, GPM minus INSAT.");
  notes(s, "I use two independent offset measures. The field measure finds the shift that best correlates the whole INSAT image with the GPM storm-top field around the storm; it is dominated by the big cold anvil against the radar's rain area. The cell measure pairs each deep radar cell with the nearest INSAT cold core; it compares the coldest tops with the tallest echoes. As we will see, they disagree, and that disagreement is the key to the results.");
}

// ================================================================== 4. RESULTS
section = "Results";
pres.addSection({ title: section });
divider("03", "Results", "What the correction does, what GPM can verify, and why");
{
  const s = content("The correction moves deep cores by 4–10 km");
  s.addChart(pres.charts.BAR, [{ name: "Median shift of deep cores [km]", labels: ["South India", "Central India", "Himalaya", "Northeast India"], values: [3.9, 7.3, 9.8, 10.5] }], {
    x: MX, y: 1.4, w: 7.4, h: 4.75, barDir: "col", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
    showLegend: false, showTitle: true, title: "Median applied shift at deep cores [km]", valAxisMinVal: 0, valAxisMaxVal: 12, barGapWidthPct: 70, ...AX,
  });
  stat(s, 8.5, 1.7, 4.2, "0.0 km", "change in the cross-look offset (95 % interval −0.2 to +0.2 km)");
  s.addText("Features move only along the line of sight, by the computed amount, and nothing moves across it.", { x: 8.5, y: 3.3, w: 4.2, h: 1.4, fontSize: 15, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  takeaway(s, "On real data the correction behaves exactly as the geometry says it should.");
  notes(s, "First, the correction does what it should. The median shift applied to deep cores grows from about 4 km in South India to over 10 km in the Northeast, following the viewing angle. And the offset across the line of sight does not change at all, median 0.0 km, which shows the correction moves features only along the line of sight.");
}
{
  const s = content("The storm-scale bias reverses, but not case by case");
  stat(s, MX, 1.7, 3.8, "+2.2 → −1.9 km", "mean storm-scale offset, uncorrected → corrected", C.accent1, 30);
  stat(s, MX + 4.15, 1.7, 3.8, "5.1 → 3.8 km", "median absolute offset", C.accent1, 30);
  stat(s, MX + 8.3, 1.7, 3.8, "18 of 30", "cases improve (sign test p = 0.36)", C.accent2, 30);
  card(s, MX, 3.55, 12.1, 1.75, "Reading this result", "The corrected mean is no longer significantly different from zero, so the correction removes the storm-scale bias on average. But case by case the improvement is not significant. The first 12 cases looked much better (10 of 12 improving); they were a favourable sample. With 38 cases the honest answer is: on average yes, case by case GPM cannot tell.", { bodySize: 15 });
  takeaway(s, "A caution for validation studies built on a handful of overpasses.");
  notes(s, "At the scale of the whole storm, the correction reverses the mean bias, from plus 2.2 to minus 1.9 km, and the median absolute offset drops from 5.1 to 3.8 km. But only 18 of 30 cases improve, which is not significant. Early on, with 12 cases, 10 improved; that did not survive the larger sample, which is itself a lesson for validation studies based on a few overpasses.");
}
{
  const s = content("At convective cores, almost none of the parallax is visible");
  figure(s, "fig3_cases", MX, 1.4, 8.1, 4.85, "Uncorrected offset against the applied shift, field and cell measures", "left");
  stat(s, 9.0, 1.65, 3.8, "−0.1 km", "median cell offset before correction: cold cores already sit on the radar cells");
  stat(s, 9.0, 3.05, 3.8, "≈ 5 %", "of the computed parallax visible at the cells", C.accent2);
  stat(s, 9.0, 4.45, 3.8, "−4.7 km", "after correction the cores overshoot (p < 0.001)", C.accent3);
  takeaway(s, "This is the puzzle the rest of the results answer.");
  notes(s, "Here is the puzzle. At the convective cores, uncorrected INSAT cold cores already sit on the GPM cells, median minus 0.1 km. If parallax were visible they would be offset by the applied shift, the dashed line. Only about 5 percent of it is visible, and after correction the cores overshoot by 4.7 km. The rest of the results are about explaining this.");
}
{
  const s = content("No single navigation shift centres both measures");
  figure(s, "fig4_states", MX, 1.4, 7.2, 4.85, "Offsets in each correction state, cell and field measures", "left");
  s.addTable([
    [{ text: "State", options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } }, { text: "Field", options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } }, { text: "Cells", options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } }],
    ["Uncorrected", "+2.2", "−0.1"], ["Parallax", "−1.9", "−4.7"], ["Coastline nav. + parallax", "−1.0", "−3.3"], ["GPM nav. + parallax", "+4.9", "−0.5"],
  ], { x: 8.15, y: 1.6, w: 4.6, colW: [2.6, 1.0, 1.0], fontSize: 14, color: HEX.dk1, border: { type: "solid", pt: 0.75, color: "BFBFBF" }, rowH: 0.5, valign: "middle", margin: [3, 8, 3, 8] });
  s.addText("Fitting the navigation to the GPM cells centres them, but pushes the storm-scale field to +4.9 km, worse than uncorrected (Wilcoxon p = 0.027). Values in km, GPM minus INSAT along the line of sight.", { x: 8.15, y: 4.35, w: 4.6, h: 1.8, fontSize: 13, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  takeaway(s, "The two measures differ by 2–5 km: GPM can verify absolute position only to about ±3–5 km.");
  notes(s, "Could navigation explain it? If I fit a navigation shift to the GPM cells, I can centre the cells, but the storm-scale field moves to plus 4.9 km, worse than doing nothing. No single translation centres both measures; they differ by 2 to 5 km. That sets the limit: GPM can verify absolute position only to about plus or minus 3 to 5 km for monsoon deep convection.");
}
{
  const s = content("It is not the method: known shifts are recovered");
  stat(s, MX, 1.65, 3.6, "10.9 km", "measured for a synthetic storm with 10.5 km of parallax (VZA 35°)");
  stat(s, MX, 3.05, 3.6, "3.5 km", "measured for 3.9 km of parallax (VZA 15°)");
  s.addText("After correction the synthetic offsets are about zero.", { x: MX, y: 4.45, w: 3.6, h: 0.8, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  s.addChart(pres.charts.BAR, [
    { name: "Applied shift", labels: ["4.4 km", "8.9 km", "13.3 km", "20 km"], values: [4.4, 8.9, 13.3, 20.0] },
    { name: "Recovered by the cell measure (median)", labels: ["4.4 km", "8.9 km", "13.3 km", "20 km"], values: [3.2, 5.7, 7.7, 8.6] },
  ], { x: 4.75, y: 1.4, w: 8.0, h: 4.75, barDir: "col", chartColors: ["C8C8C8", HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0",
    showLegend: true, legendPos: "b", showTitle: true, title: "Real INSAT scenes shifted by a known distance [km]", valAxisMinVal: 0, valAxisMaxVal: 22, barGapWidthPct: 60, ...AX });
  takeaway(s, "On real scenes the cell measure recovers about two-thirds of a shift: attenuated, but not blind.");
  notes(s, "Is the cell measure simply blind? Two checks. A synthetic storm with a known parallax is recovered almost exactly, 10.9 km against 10.5 expected, and is near zero after correction. And when I shift real INSAT scenes by a known distance, the cell measure recovers about two-thirds of the shift, less for very large shifts, because big cold anvils fill its search area. So it is attenuated, which I now state in the paper, but it would still see 4 to 5 km of a 7 km parallax. It sees almost none.");
}
{
  const s = content("Infrared tops lie about 3 km above the radar echo tops");
  figure(s, "fig5_heights", MX, 1.4, 5.0, 4.85, "INSAT cold-core height against GPM maximum echo top per cell", "left");
  stat(s, 6.3, 1.65, 3.0, "16.6 km", "median infrared cold-core height");
  stat(s, 9.6, 1.65, 3.0, "11.9 km", "median GPM maximum echo top", C.accent3);
  stat(s, 6.3, 3.05, 3.0, "3.2 km", "median difference, 206 cells", C.accent2);
  stat(s, 9.6, 3.05, 3.0, "46 %", "of cores at the 17 km tropopause cap", C.accent3);
  s.addText("Physical, not a profile error: the Ku radar detects only precipitation-sized particles (about 15–18 dBZ). The gap inflates the shift at the rain core by 1–2 km. It cannot hide 4–10 km.", { x: 6.3, y: 4.55, w: 6.45, h: 1.6, fontSize: 14, color: C.text1, isTextBox: true, margin: 0, valign: "top" });
  takeaway(s, "Cloud height explains part of the overshoot, not the missing parallax.");
  notes(s, "Could cloud height be the reason? The infrared cold cores are at a median 16.6 km, the radar echo tops at 11.9, a 3.2 km gap. That is physical: the radar sees only precipitation-sized particles. The gap explains 1 to 2 km of the overshoot, but it cannot hide 4 to 10 km of parallax.");
}
{
  const s = content("The storm column leans west, not towards the satellite");
  s.addChart(pres.charts.LINE, [
    { name: "East [km]", labels: ["2–4 km core", "5–7 km", "8–10 km", "11–13 km", "Echo top"], values: [0, -0.5, -1.3, -2.2, -1.5] },
    { name: "Towards INSAT [km]", labels: ["2–4 km core", "5–7 km", "8–10 km", "11–13 km", "Echo top"], values: [0, 0.1, 0.3, 0.7, 0.8] },
  ], { x: MX, y: 1.4, w: 7.4, h: 4.75, chartColors: [HEX.accent1, HEX.accent2], lineSize: 2.5, lineDataSymbol: "circle", lineDataSymbolSize: 7,
    showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "+0.0;-0.0;0.0", showLegend: true, legendPos: "b", showTitle: true,
    title: "Displacement of GPM echo centroids from the 2–4 km core (203 cells)", valAxisMinVal: -3, valAxisMaxVal: 2, ...AX });
  stat(s, 8.5, 1.7, 4.2, "1.5 km west", "lean of the echo top: the monsoon easterlies aloft", C.accent1, 30);
  stat(s, 8.5, 3.1, 4.2, "+0.8 km", "of it points towards INSAT (−0.9 to +1.4)", C.accent2, 30);
  stat(s, 8.5, 4.5, 4.2, "≈ 6 km", "of parallax that the cell measure does not see", C.accent3, 30);
  takeaway(s, "Each range bin is placed on its slanted beam; the result holds for every threshold tried.");
  notes(s, "A natural explanation was tilted storms: if the cells leaned towards the satellite, lean and parallax would cancel. I measured the lean from GPM's three-dimensional reflectivity, placing every range bin on its slanted beam. The cells do lean, 1.5 km west at the echo top, as expected under the upper-level easterlies. But only 0.8 km of that points towards INSAT, against about 6 km of hidden parallax. So column tilt is ruled out.");
}
{
  const s = content("A second satellite confirms the correction without radar");
  figure(s, "fig7_meteosat_tilt", MX, 1.35, W - 2 * MX, 3.9, "INSAT minus Meteosat per case, cold cores for both satellites, storm lean");
  stat(s, MX, 5.3, 3.9, "11.6 → 7.9 km", "INSAT–Meteosat distance, before → after correction", C.accent1, 28);
  stat(s, MX + 4.15, 5.3, 3.9, "29 of 38", "cases closer after correction (p = 3 × 10⁻⁵)", C.accent1, 28);
  stat(s, MX + 8.3, 5.3, 3.9, "−1.1 km", "INSAT north–south error relative to Meteosat", C.accent2, 28);
  notes(s, "This is the key test. Meteosat over the Indian Ocean sees the same storms from the west, so its parallax points east instead of north. If the correction is right, correcting both satellites for their own parallax should make their images agree. Panel a shows exactly that: the 9.5 km east-west disagreement disappears, and the two fields come closer in 29 of 38 cases, p three times ten to the minus five. This is a confirmation that does not depend on radar at all. It also measures INSAT's north-south navigation error: minus 1.1 km, nowhere near the 5 to 10 km needed to hide the parallax.");
}
{
  const s = content("What hides the parallax: the coldest tops sit off the rain cores");
  const rows = [
    ["Tilt of the rain column", "GPM 3-D reflectivity: only +0.8 km towards INSAT", "Ruled out", HEX.accent3],
    ["INSAT navigation error", "Meteosat: −1.1 km north–south, not 5–10 km", "Ruled out", HEX.accent3],
    ["Cold tops displaced from the rain cores", "Both satellites, after correction: 4–5 km west to south-west of the GPM cells", "Supported", HEX.accent1],
  ];
  rows.forEach(([head, body, verdict, col], i) => {
    const y = 1.55 + i * 1.45;
    s.addShape(pres.shapes.RECTANGLE, { x: MX, y, w: W - 2 * MX, h: 1.25, fill: { color: i === 2 ? "E6EAF2" : C.background2 }, line: { color: i === 2 ? "E6EAF2" : C.background2 }, objectName: `explanation ${i + 1}` });
    s.addText(head, { x: MX + 0.3, y: y + 0.17, w: 7.9, h: 0.42, fontSize: 17, bold: true, color: C.text1, isTextBox: true, margin: 0 });
    s.addText(body, { x: MX + 0.3, y: y + 0.6, w: 8.6, h: 0.5, fontSize: 14, color: C.text1, isTextBox: true, margin: 0 });
    chip(s, W - MX - 2.2, y + 0.44, 1.9, verdict, col);
  });
  takeaway(s, "The coldest tops, above the radar's view, lie downwind of the rain cores and cancel most of the parallax.");
  notes(s, "Putting it together. Column tilt is ruled out by GPM's 3-D data. Navigation is ruled out by Meteosat. What remains, and what both satellites agree on independently, is that after correction the coldest tops sit 4 to 5 km west to south-west of the radar rain cores, a lower bound given the measure's attenuation. That is the direction the echo leans, continued above what the radar can see, and it points largely towards INSAT, so at the cell scale it cancels most of the parallax. The correction is right; the cold top and the rain core are simply different targets.");
}
{
  const s = content("Terrain matters for the ground, not for the storms");
  figure(s, "fig6_terrain", MX, 1.4, 5.3, 4.85, "Clear-sky terrain parallax from SRTM", "left");
  stat(s, 6.5, 1.65, 6.2, "3–4 km", "ground displacement over the Himalaya and Tibetan Plateau");
  stat(s, 6.5, 3.05, 6.2, "1.3–2.5 km", "median shift of clear-sky ground in Himalayan scenes, up to 6 km");
  stat(s, 6.5, 4.45, 6.2, "0.1 km", "change in the storm offsets: storm tops are far above the ground", C.accent3);
  takeaway(s, "For land-surface, snow or terrain products in the mountains, terrain-aware correction should be standard.");
  notes(s, "Terrain is handled too. Over the Himalaya, ellipsoid-navigated ground pixels are 3 to 4 km out of place, up to 6 km in clear sky. It makes no difference to the storm results, but for anything observed at the ground in mountains it matters.");
}
{
  const s = content("Downstream: a precipitation-type U-Net does not improve");
  s.addChart(pres.charts.BAR, [
    { name: "Model A: uncorrected input", labels: ["4-class macro F1", "Strat./conv. macro F1", "Rain macro F1", "Deep-conv. CSI (×10)"], values: [0.421, 0.686, 0.718, 0.41] },
    { name: "Model B: corrected input", labels: ["4-class macro F1", "Strat./conv. macro F1", "Rain macro F1", "Deep-conv. CSI (×10)"], values: [0.420, 0.685, 0.717, 0.38] },
  ], { x: MX, y: 1.4, w: 7.6, h: 4.75, barDir: "col", chartColors: ["A6A6A6", HEX.accent1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00",
    showLegend: true, legendPos: "b", showTitle: true, title: "Test set, 2,197 patches from 347 scenes", valAxisMinVal: 0, valAxisMaxVal: 0.9, barGapWidthPct: 55, ...AX });
  bullets(s, [
    "Same network, labels, split and seed; only the input differs",
    "Accuracy and macro F1 change by at most 0.12 percentage points",
    "Convective scores fall slightly (deep-convective CSI 0.041 → 0.038)",
    "Same direction as the only earlier study of this kind, for SEVIRI (D'Adderio et al., 2023)",
  ], 8.6, 1.6, 4.15, 4.4, 14);
  takeaway(s, "Consistent with the cell result: shifting cold cores off the rain does not help a rain classifier.");
  notes(s, "As an application test, the group's precipitation-type U-Net was retrained on corrected instead of uncorrected input, with everything else identical. It does not improve; convective scores drop slightly. That fits the physical picture: the cold cores already sat on the rain, so moving them away does not help a rain classifier. It agrees with the one earlier study of this kind, for Meteosat. These are small effects from one training run per model, so in the paper this is an appendix.");
}

// ================================================================== 5. THE TOOL
section = "The tool";
pres.addSection({ title: section });
{
  const s = content("PyGeoParallax-IN: open, tested and documented");
  const feats = [
    ["One-command correction", "pygeoparallax l1c on whole L1C archives, in parallel"],
    ["Native-grid output", "Corrected image on the file's own pixels, for ML"],
    ["Effective height", "Lower correction height for precipitation work"],
    ["Navigation from coastlines", "Measure and apply a geolocation correction"],
    ["Self-test and Colab", "pygeoparallax demo; try it in the browser"],
    ["Documentation", "12 pages and a PDF manual; every example tested"],
  ];
  feats.forEach(([h, b], i) => card(s, MX + (i % 3) * 4.1, 1.5 + Math.floor(i / 3) * 1.75, 3.85, 1.55, h, b, { headSize: 15, bodySize: 13 }));
  stat(s, MX, 5.15, 3.0, "73 tests", "on Linux and Windows, in continuous integration", C.accent1, 26);
  stat(s, MX + 3.3, 5.15, 3.4, "v0.4.2", "archived on Zenodo, DOI 10.5281/zenodo.23838067", C.accent1, 26);
  stat(s, MX + 7.0, 5.15, 2.5, "1.8 s", "per India scene", C.accent1, 26);
  stat(s, MX + 9.7, 5.15, 2.4, "MIT", "licence, on GitHub", C.accent1, 26);
  notes(s, "All of this is released as an open-source Python package. It corrects whole archives with one command, can keep the native pixel grid for machine learning, has the effective-height option, the coastline navigation, a built-in self-test and a Colab notebook, and full documentation. It has 73 automated tests and is archived on Zenodo with a DOI, so the paper's results are reproducible.");
}

// ================================================================== 6. CONCLUSIONS
section = "Conclusions";
pres.addSection({ title: section });
divider("04", "Conclusions", "What the correction does, what can verify it, and what comes next");
{
  const s = content("Key findings");
  const f = [
    "The correction is exact and moves storms only along the line of sight, by 4–10 km",
    "At storm scale it removes the mean bias; GPM cannot show a per-case gain",
    "GPM can verify absolute position only to about ±3–5 km for monsoon convection",
    "Meteosat confirms the correction without radar and rules out INSAT navigation as the cause",
    "The coldest tops sit 4–5 km west to south-west of the rain cores: that hides the parallax",
  ];
  f.forEach((t, i) => {
    const y = 1.5 + i * 0.92;
    badge(s, MX, y + 0.04, i + 1, i === 3 || i === 4 ? C.accent2 : C.accent1);
    s.addText(t, { x: MX + 0.7, y, w: 11.4, h: 0.56, fontSize: 17, color: C.text1, isTextBox: true, margin: 0, valign: "middle" });
  });
  takeaway(s, "For cloud products use the infrared height; for rain, the relevant level lies lower.");
  notes(s, "To summarise the five key findings. The correction is exact and behaves as geometry predicts. At storm scale it removes the mean bias, but GPM cannot show a per-case gain. GPM can verify absolute position only to a few kilometres. A second satellite confirms the correction and rules out navigation. And the coldest tops sit off the rain cores, which is why the parallax is hidden at the cell scale.");
}
{
  const s = content("Limitations");
  const L = [
    ["One radar, one look", "GPM samples each storm once in a 245 km swath; its echo tops differ from infrared tops by definition."],
    ["Few cases at high angles", "Himalaya and Northeast have only 4 and 5 usable cases."],
    ["Attenuated cell measure", "It recovers about two-thirds of a known shift, so the cold-top offset is a lower bound."],
    ["Meteosat assumptions", "Its navigation is taken as correct; east–west navigation and cloud-height errors cannot be separated."],
  ];
  L.forEach(([h, b], i) => card(s, MX + (i % 2) * 6.15, 1.5 + Math.floor(i / 2) * 2.3, 5.95, 2.1, h, b, { bodySize: 14 }));
  notes(s, "The limitations: GPM sees each storm once and measures precipitation, not cloud tops; the high-angle regions have few cases; the cell measure is attenuated, so the 4 to 5 km offset is a lower bound; and for Meteosat I assume its navigation is correct, and cannot separate east-west navigation from height errors because both satellites look from the west.");
}
{
  const s = content("Status and next steps");
  const col = (x, title, items, color) => {
    chip(s, x, 1.5, 1.6, title, color);
    bullets(s, items, x, 2.1, 3.85, 3.9, 15);
  };
  col(MX, "Done", ["Tool released (v0.4.2, Zenodo DOI)", "Validation, storm tilt and Meteosat analyses", "Documentation and PDF manual", "Paper in four formats"], HEX.accent1);
  col(MX + 4.15, "Now", ["Submission to Atmospheric Research (Elsevier)", "Software paper for JOSS from February 2027"], HEX.accent2);
  col(MX + 8.3, "Next", ["IMD ground radar for finer verification", "Effective-height U-Net and more seeds", "INSAT-3DS at 82° E"], HEX.accent3);
  notes(s, "Where things stand: the tool, the analyses, documentation and the paper are done. The paper is being submitted to Atmospheric Research, and the software paper will go to JOSS once the repository has six months of public history. Next steps are ground radar to verify positions more finely, an effective-height version of the U-Net, and extending the tool to INSAT-3DS.");
}
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: section });
  s.addText("Thank you", { placeholder: "title" });
  s.addText("Questions and discussion", { placeholder: "subtitle" });
  s.addText("github.com/bapallinaveen60/PyGeoParallax-IN\nDOI 10.5281/zenodo.23838067  ·  baipallinaveen60@gmail.com", { placeholder: "meta" });
  notes(s, "Thank you. I am happy to take questions; I have backup slides with the full statistics.");
}

// ================================================================== BACKUP
section = "Backup";
pres.addSection({ title: section });
{
  const s = content("Backup: INSAT minus Meteosat, all numbers");
  const hd = (t) => ({ text: t, options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } });
  s.addTable([
    [hd("Quantity (38 cases)"), hd("Uncorrected"), hd("Corrected")],
    ["East offset, median [km]", "−9.5 (−12.1 to −6.5)", "−2.3 (−5.2 to +0.9)"],
    ["North offset, median [km]", "−1.2 (−4.4 to +1.5)", "−1.1 (−3.9 to +1.4)"],
    ["Distance apart, median [km]", "11.6", "7.9"],
    ["Cases closer after correction", "", "29 of 38 (Wilcoxon p = 3 × 10⁻⁵)"],
    ["Cold core − GPM cell, INSAT (E, N) [km]", "−2.2, +0.2", "−4.2, −4.5"],
    ["Cold core − GPM cell, Meteosat (E, N) [km]", "−0.1, +1.2", "−4.5, −1.5"],
  ], { x: MX, y: 1.5, w: W - 2 * MX, colW: [5.0, 3.5, 3.63], fontSize: 15, color: HEX.dk1, border: { type: "solid", pt: 0.75, color: "BFBFBF" }, rowH: 0.58, valign: "middle", margin: [3, 8, 3, 8] });
  s.addText("Meteosat-8 (41.5° E, 24 cases) until May 2022, Meteosat-9 (45.5° E, 14 cases) after. Storms scanned a median 1.3 min from GPM; motion from two Meteosat cycles. 95 % bootstrap intervals over cases.", { x: MX, y: 5.75, w: W - 2 * MX, h: 0.8, fontSize: 13, color: C.accent3, isTextBox: true, margin: 0, valign: "top" });
  notes(s, "Backup with all the Meteosat numbers, if needed.");
}
{
  const s = content("Backup: offsets in each correction state");
  const hd = (t) => ({ text: t, options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 } } });
  s.addTable([
    [hd("State"), hd("Field mean [km]"), hd("Field median |offset| [km]"), hd("Cases improved"), hd("Cells, median [km]")],
    ["Uncorrected", "+2.2", "5.1", "–", "−0.1 (−2.7 to +3.5)"],
    ["Parallax only", "−1.9", "3.8", "18 of 30", "−4.7 (−6.8 to −0.9)"],
    ["Coastline navigation + parallax", "−1.0", "4.3", "15 of 30", "−3.3 (−5.9 to +0.2)"],
    ["GPM navigation + parallax", "+4.9", "6.0", "10 of 31", "−0.5 (−2.6 to +2.9)"],
  ], { x: MX, y: 1.5, w: W - 2 * MX, colW: [3.6, 1.9, 2.5, 1.8, 2.33], fontSize: 15, color: HEX.dk1, border: { type: "solid", pt: 0.75, color: "BFBFBF" }, rowH: 0.62, valign: "middle", margin: [3, 8, 3, 8] });
  s.addText("Line-of-sight offsets, GPM minus INSAT (positive: INSAT must move towards the satellite). Field: 30–31 cases; cells: 157–167 cells in 27–28 cases; cluster bootstrap intervals.", { x: MX, y: 4.9, w: W - 2 * MX, h: 0.8, fontSize: 13, color: C.accent3, isTextBox: true, margin: 0, valign: "top" });
  notes(s, "Backup with the full table of correction states.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  // Fade transition on every slide (pptxgenjs has no transition option): after clrMapOvr, before timing.
  const fs = require("fs");
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(OUT));
  const slides = Object.keys(zip.files).filter((f) => /^ppt\/slides\/slide\d+\.xml$/.test(f));
  for (const f of slides) {
    let xml = await zip.file(f).async("string");
    if (!xml.includes("<p:transition")) {
      xml = xml.replace("</p:clrMapOvr>", "</p:clrMapOvr><p:transition spd=\"med\"><p:fade/></p:transition>");
      zip.file(f, xml);
    }
  }
  fs.writeFileSync(OUT, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("wrote", OUT, `(${slides.length} slides)`);
})();
